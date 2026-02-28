from __future__ import annotations

from typing import Any, Dict, List, Optional
import ast

from app.models.schemas import CodeAnalysisRequest, Issue
from app.services import complexity as complexity_service
from app.services import security as security_service
from app.services.language_detector import detect_language
from app.services.validators import validate_code
from app.utils.ai_client import get_ai_client


async def analyze_code(code: str, language: Optional[str] = None) -> Dict[str, Any]:
    """Run unified analysis over a raw code string with validation/correction.

    Pipeline:
    1. Determine language (request override > auto-detect).
    2. Validate syntax/structure for supported languages.
    3. If invalid, attempt auto‑correction via AI.
    4. Re‑validate corrected code.
    5. If still invalid → return structured error without computing metrics.
    6. Otherwise run complexity/security/AI summary on the final code.
    """
    # 1. Language detection (heuristic, with optional override).
    override_language = (language or "").strip().lower()
    detection_result = detect_language(code)
    detected_language = str(detection_result.get("language") or "generic").lower()
    detection_confidence = float(detection_result.get("confidence") or 0.0)

    effective_language = override_language or detected_language or "generic"

    # Quick self‑heal: if heuristics/Gemini say "python" but the code clearly
    # looks like C/C++ (e.g. has #include), prefer treating it as C so we don't
    # run Python's ast.parse on C source.
    if effective_language == "python" and "#include" in code:
        effective_language = "c"

    # Optionally refine low‑confidence detection with AI.
    if not override_language and detection_confidence < 0.5:
        ai_lang, ai_conf = await _detect_language_via_ai(code, detected_language, detection_confidence)
        effective_language = ai_lang
        detection_confidence = ai_conf

    # 2. Initial validation.
    validation = validate_code(effective_language, code)
    original_valid = bool(validation.get("valid"))

    final_code = code
    was_corrected = False

    # 3. Auto‑correct if invalid.
    if not original_valid:
        corrected_code = await attempt_auto_correction(effective_language, code)
        revalidation = validate_code(effective_language, corrected_code)

        if revalidation.get("valid"):
            final_code = corrected_code
            was_corrected = True
        else:
            # 4. Still invalid after correction – return structured SyntaxError.
            return _syntax_error_response(
                language_detected=effective_language,
                detection_confidence=detection_confidence,
                was_corrected=False,
                original_valid=False,
                corrected_code=None,
                message=str(validation.get("error") or "Code is invalid even after correction."),
            )

    # 5. At this point code is considered valid – run analysis on final_code.
    payload = CodeAnalysisRequest(code=final_code, language=effective_language)

    complexity_result = complexity_service.analyze_complexity(payload)
    security_result = security_service.analyze_security(payload)

    big_o = _estimate_big_o(final_code, effective_language)
    space_o = _estimate_space_complexity(final_code, effective_language)
    cyclomatic = _estimate_cyclomatic_complexity(final_code)
    maintainability = _estimate_maintainability(cyclomatic, final_code)
    security_summary = _summarise_security(security_result.security_findings)
    ai_summary = await _ai_suggestion_summary(final_code)

    refined: Optional[Dict[str, str]] = None
    if effective_language in {"python", "py"}:
        refined = await _refine_python_complexity_with_gemini(
            code=final_code,
            preliminary={
                "time_complexity": big_o,
                "space_complexity": space_o,
            },
        )
        if refined:
            big_o = refined.get("time_complexity", big_o) or big_o
    risk_score, risk_level = _compute_risk(
        big_o=big_o,
        cyclomatic_complexity=cyclomatic,
        security_issues=security_result.security_findings,
        maintainability=maintainability,
    )
    complexity_trend = _estimate_complexity_trend(cyclomatic)

    return {
        "big_o": big_o,
        "cyclomatic_complexity": cyclomatic,
        "maintainability": maintainability,
        "security_summary": security_summary,
        "ai_summary": ai_summary,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "complexity_trend": complexity_trend,
        "language_detected": effective_language,
        "detection_confidence": detection_confidence,
        "was_corrected": was_corrected,
        "original_valid": original_valid,
        "corrected_code": final_code if was_corrected else None,
        "algorithm": (refined or {}).get("algorithm") if refined else None,
        "time_complexity": (refined or {}).get("time_complexity") if refined else big_o,
        "space_complexity": (refined or {}).get("space_complexity") if refined else space_o,
        "recommendation": (refined or {}).get("recommendation") if refined else None,
        "explanation": (refined or {}).get("explanation") if refined else None,
        "error": None,
        "message": None,
    }


async def run_full_analysis(payload: CodeAnalysisRequest) -> Dict[str, Any]:
    """Backward‑compatible entry that works with existing routes."""
    return await analyze_code(payload.code, payload.language)


def _estimate_big_o(code: str, language: Optional[str]) -> str:
    """Very rough Big‑O guess.

    For Python, use an AST‑based approximation that inspects loops and
    recursion. For other languages, fall back to simple text heuristics.
    """
    lang = (language or "").lower()
    if lang in {"python", "py"}:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return "O(1)"

        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.loop_depth = 0
                self.max_loop_depth = 0
                self.self_calls_per_func: Dict[str, int] = {}
                self.current_func: Optional[str] = None
                self.has_log_loop = False

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                prev_func = self.current_func
                self.current_func = node.name
                self.self_calls_per_func.setdefault(node.name, 0)
                self.generic_visit(node)
                self.current_func = prev_func

            def visit_Call(self, node: ast.Call) -> None:
                # Track direct self‑recursion: f(...) inside def f.
                if isinstance(node.func, ast.Name) and self.current_func:
                    if node.func.id == self.current_func:
                        self.self_calls_per_func[self.current_func] += 1
                self.generic_visit(node)

            def visit_For(self, node: ast.For) -> None:
                self.loop_depth += 1
                self.max_loop_depth = max(self.max_loop_depth, self.loop_depth)
                self.generic_visit(node)
                self.loop_depth -= 1

            def visit_While(self, node: ast.While) -> None:
                # Try to detect logarithmic loops where a bound variable is
                # repeatedly halved or similar.
                self.loop_depth += 1
                self.max_loop_depth = max(self.max_loop_depth, self.loop_depth)

                loop_src = ast.unparse(node) if hasattr(ast, "unparse") else ""
                lowered = loop_src.lower()
                if any(v in lowered for v in ("low", "high", "start", "end", "left", "right")) and (
                    "// 2" in lowered or ">> 1" in lowered or "/= 2" in lowered
                ):
                    self.has_log_loop = True

                self.generic_visit(node)
                self.loop_depth -= 1

        visitor = ComplexityVisitor()
        visitor.visit(tree)

        # Determine recursion pattern.
        max_self_calls = max(visitor.self_calls_per_func.values(), default=0)

        if visitor.has_log_loop:
            return "O(log n)"

        if max_self_calls >= 2:
            # Multiple self‑calls per activation suggest exponential‑type recursion.
            return "O(2^n)"
        if max_self_calls == 1:
            # Single self‑call is often linear recursion.
            return "O(n)"

        if visitor.max_loop_depth >= 2:
            return "O(n^2)"
        if visitor.max_loop_depth == 1:
            return "O(n)"
        return "O(1)"

    # Non‑Python: text heuristics with special‑case binary search.
    lowered = code.lower()

    # Special‑case: binary search‑like pattern.
    # Look for:
    # - variables named like low/high or start/end
    # - a loop with a condition low <= high or start <= end
    # - mid computed as (low + high) / 2 or similar.
    has_range_vars = any(tok in lowered for tok in ("low", "high", "start", "end", "left", "right"))
    has_bisect_loop = any(
        cond in lowered
        for cond in (
            # C / C++ / Java style
            "while (low <=",
            "while (low >=",
            "while(low <=",
            "while(low >=",
            "while (start <=",
            "while(start <=",
            "while (begin <=",
            "while(begin <=",
            "while (left <=",
            "while(left <=",
            "while (left < right",
            "while(left < right",
            # Python style (no parentheses)
            "while left <=",
            "while left >=",
            "while start <=",
            "while begin <=",
        )
    )
    has_mid_calc = "mid" in lowered and ("/ 2" in lowered or ">> 1" in lowered)

    if has_range_vars and has_bisect_loop and has_mid_calc:
        return "O(log n)"

    # Fallback: loop nesting depth.
    max_depth = 0
    current_depth = 0

    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith(("for ", "while ")):
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        if stripped.endswith(":") and not stripped.startswith(("for ", "while ", "if ", "elif ")):
            # treat new blocks as potential exits (Python‑style blocks)
            current_depth = max(current_depth - 1, 0)

    if max_depth >= 2:
        return "O(n^2)"
    if max_depth == 1:
        return "O(n)"
    return "O(1)"


def _estimate_space_complexity(code: str, language: Optional[str]) -> str:
    """Rule-based space complexity estimate.

    Python uses an AST approximation; other languages default to O(1).
    """
    lang = (language or "").lower()
    if lang not in {"python", "py"}:
        return "O(1)"

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return "O(1)"

    class SpaceVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.self_calls_per_func: Dict[str, int] = {}
            self.current_func: Optional[str] = None
            self.has_linear_allocation = False

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            prev = self.current_func
            self.current_func = node.name
            self.self_calls_per_func.setdefault(node.name, 0)
            self.generic_visit(node)
            self.current_func = prev

        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Name) and self.current_func:
                if node.func.id == self.current_func:
                    self.self_calls_per_func[self.current_func] += 1
            self.generic_visit(node)

        def visit_ListComp(self, node: ast.ListComp) -> None:
            self.has_linear_allocation = True
            self.generic_visit(node)

        def visit_DictComp(self, node: ast.DictComp) -> None:
            self.has_linear_allocation = True
            self.generic_visit(node)

        def visit_SetComp(self, node: ast.SetComp) -> None:
            self.has_linear_allocation = True
            self.generic_visit(node)

    v = SpaceVisitor()
    v.visit(tree)

    max_self_calls = max(v.self_calls_per_func.values(), default=0)
    if max_self_calls >= 1:
        return "O(n)"
    if v.has_linear_allocation:
        return "O(n)"
    return "O(1)"


def _estimate_cyclomatic_complexity(code: str) -> int:
    """Simple cyclomatic complexity approximation."""
    keywords = ("if ", "elif ", "for ", "while ", "case ", " except ", " and ", " or ")
    complexity = 1  # base path

    lowered = code.lower()
    for kw in keywords:
        complexity += lowered.count(kw)

    return complexity


def _estimate_maintainability(cyclomatic: int, code: str) -> float:
    """Crude maintainability score from 0–100 (higher is better)."""
    line_count = max(len(code.splitlines()), 1)

    score = 100.0
    score -= cyclomatic * 1.5
    score -= line_count * 0.1

    return max(0.0, min(100.0, score))


def _summarise_security(issues: List[Issue]) -> str:
    if not issues:
        return "No obvious security issues detected by simple rules."

    kinds = {issue.message for issue in issues}
    return f"Potential security concerns: {', '.join(sorted(kinds))}."


async def _ai_suggestion_summary(code: str) -> str:
    """Ask the AI client for a short improvement summary.

    In stub mode this will just echo the prompt.
    """
    client = get_ai_client()
    prompt = (
        "Summarise the main issues and possible improvements in the following code. "
        "Keep it to 2–3 sentences, plain text only.\n\n"
        f"{code[:4000]}"
    )
    return await client.chat(prompt=prompt, context=None)


async def attempt_auto_correction(language: str, code: str) -> str:
    """Use the AI client to fix syntax/runtime issues.

    If Gemini/stub fails, returns the original code unchanged.
    """
    client = get_ai_client()
    lang = language or "code"
    prompt = (
        f"Fix syntax and runtime errors in the following {lang} code.\n"
        "Do NOT change business logic.\n"
        "Return ONLY corrected code.\n"
        "No explanation.\n"
        "No markdown.\n\n"
        f"{code[:6000]}"
    )

    reply = await client.chat(prompt=prompt, context=None)
    lowered = reply.lower()

    # If Gemini failed or stub client is active, fall back to original code.
    if "stubbed ai" in lowered or not reply.strip():
        return code

    return reply.strip()


async def _refine_python_complexity_with_gemini(
    *,
    code: str,
    preliminary: Dict[str, str],
) -> Optional[Dict[str, str]]:
    """Use Gemini to refine algorithm/time/space complexity for Python."""
    client = get_ai_client()

    schema_hint = {
        "algorithm": "Unknown",
        "time_complexity": preliminary.get("time_complexity", "O(1)"),
        "space_complexity": preliminary.get("space_complexity", "O(1)"),
        "recommendation": "",
        "explanation": "",
    }

    system_prompt = "You are a Python code analysis assistant."
    user_prompt = (
        "Input 1: User-submitted Python code.\n"
        "Input 2: Rule-based analysis JSON from AST estimator:\n"
        f"{preliminary}\n\n"
        "Task:\n"
        "- Recognize algorithm type (e.g., Binary Search, Merge Sort, DFS, BFS, DP, or custom).\n"
        "- Correct rule-based time and space complexity estimates.\n"
        "- Suggest optimizations (iterative vs recursive, memoization, loop improvements).\n"
        "- Provide explanation in human-readable language.\n\n"
        "Output Requirements:\n"
        "Return strict JSON only with fields:\n"
        '{ "algorithm": "...", "time_complexity": "O(...)", "space_complexity": "O(...)", '
        '"recommendation": "...", "explanation": "..." }\n'
        "Truncate explanation to 300 characters if too long.\n"
        "Do not include any extra text or commentary.\n\n"
        "CODE:\n"
        f"{code[:6000]}"
    )

    result = await client.openai_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        json_schema_hint=schema_hint,
    )

    if result.get("_stubbed") or result.get("_parse_error"):
        return None

    algorithm = str(result.get("algorithm") or "Unknown")
    time_c = str(result.get("time_complexity") or schema_hint["time_complexity"])
    space_c = str(result.get("space_complexity") or schema_hint["space_complexity"])
    recommendation = str(result.get("recommendation") or "")
    explanation = str(result.get("explanation") or "")

    if len(explanation) > 300:
        explanation = explanation[:300]

    return {
        "algorithm": algorithm,
        "time_complexity": time_c,
        "space_complexity": space_c,
        "recommendation": recommendation,
        "explanation": explanation,
    }


async def _detect_language_via_ai(
    code: str,
    fallback_language: str,
    fallback_confidence: float,
) -> tuple[str, float]:
    """Ask Gemini to detect language when heuristic confidence is low.

    On failure, falls back to the provided language/confidence.
    """
    client = get_ai_client()
    prompt = (
        "Detect the programming language of the following code.\n"
        "Return ONLY the language name.\n"
        "No explanation.\n\n"
        f"{code[:6000]}"
    )

    reply = await client.chat(prompt=prompt, context=None)
    lowered = reply.lower().strip()

    if "stubbed ai" in lowered or not lowered:
        return fallback_language or "generic", fallback_confidence

    # Normalise common language names/aliases.
    alias_map = {
        "python": "python",
        "py": "python",
        "javascript": "javascript",
        "js": "javascript",
        "typescript": "typescript",
        "ts": "typescript",
        "java": "java",
        "c++": "cpp",
        "cpp": "cpp",
        "c": "c",
    }

    token = lowered.split()[0]
    lang = alias_map.get(token)
    if not lang:
        return "generic", 0.0

    return lang, 0.9


def _syntax_error_response(
    *,
    language_detected: Optional[str],
    detection_confidence: float,
    was_corrected: bool,
    original_valid: bool,
    corrected_code: Optional[str],
    message: str,
) -> Dict[str, Any]:
    """Standardised error payload when syntax validation fails.

    Metrics are set to neutral defaults; no complexity/risk computation is done.
    """
    return {
        "big_o": "N/A",
        "cyclomatic_complexity": 0,
        "maintainability": 0.0,
        "security_summary": "",
        "ai_summary": "",
        "risk_score": 0,
        "risk_level": "Unknown",
        "complexity_trend": "unknown",
        "language_detected": language_detected,
        "detection_confidence": detection_confidence,
        "was_corrected": was_corrected,
        "original_valid": original_valid,
        "corrected_code": corrected_code,
        "error": "SyntaxError",
        "message": message,
    }


def _compute_risk(
    *,
    big_o: str,
    cyclomatic_complexity: int,
    security_issues: List[Issue],
    maintainability: float,
) -> tuple[int, str]:
    """Compute risk score + level using simple hackathon rules."""
    score = 0

    # Rules
    if "n^2" in big_o:
        score += 2
    if cyclomatic_complexity > 15:
        score += 2
    if security_issues:
        score += 3
    if maintainability < 50:
        score += 2

    # Mapping
    if score <= 2:
        level = "Low"
    elif score <= 4:
        level = "Medium"
    elif score <= 6:
        level = "High"
    else:
        level = "Critical"

    return score, level


def _estimate_complexity_trend(cyclomatic: int) -> str:
    """Heuristic 'trend' label without historical data."""
    if cyclomatic >= 15:
        return "increasing"
    if cyclomatic >= 8:
        return "slightly_increasing"
    return "stable"
