from __future__ import annotations

from typing import Any, Dict, List

from app.models.schemas import CodeCompareRequest, CodeCompareResponse, CodeDiff
from app.services import analysis_engine
from app.services.language_detector import detect_language
from app.services.validators import validate_code


def compare_versions(payload: CodeCompareRequest) -> CodeCompareResponse:
    """Very simple line-based comparison suitable for hackathon demos."""
    original_lines = payload.original_code.splitlines()
    modified_lines = payload.modified_code.splitlines()

    added = [line for line in modified_lines if line not in original_lines]
    removed = [line for line in original_lines if line not in modified_lines]
    changed: list[str] = []

    # In a real implementation we would use a diff algorithm;
    # for hackathon purposes, keep it simple.

    diff = CodeDiff(added=added, removed=removed, changed=changed)

    risk_score = float(len(added) + len(removed))

    summary = "Basic diff calculated. Replace with smarter analysis as needed."

    return CodeCompareResponse(diff=diff, risk_score=risk_score, summary=summary)


async def compare_codes(code_a: str, code_b: str, language: str | None = None) -> Dict[str, Any]:
    """Compare two code versions using the unified analysis engine.

    Returns:
    {
      better_version: "A" | "B",
      improvement_notes: [...],
      metrics_comparison: {...}
    }
    """
    a = await analysis_engine.analyze_code(code_a, language)
    b = await analysis_engine.analyze_code(code_b, language)

    if a.get("error") == "CompilationError" or b.get("error") == "CompilationError":
        which = []
        if a.get("error") == "CompilationError":
            which.append("A")
        if b.get("error") == "CompilationError":
            which.append("B")
        return {
            "error": "CompilationError",
            "message": f"Code is invalid even after correction for versions: {', '.join(which)}.",
        }

    a_big_o_rank = _big_o_rank(a.get("big_o", ""))
    b_big_o_rank = _big_o_rank(b.get("big_o", ""))

    a_cyclomatic = int(a.get("cyclomatic_complexity", 0))
    b_cyclomatic = int(b.get("cyclomatic_complexity", 0))

    a_risk = int(a.get("risk_score", 0))
    b_risk = int(b.get("risk_score", 0))

    better_version = _pick_better(
        a_risk=a_risk,
        b_risk=b_risk,
        a_cyclomatic=a_cyclomatic,
        b_cyclomatic=b_cyclomatic,
        a_big_o_rank=a_big_o_rank,
        b_big_o_rank=b_big_o_rank,
    )

    notes: List[str] = []
    notes.extend(_notes_for_metric("Big‑O", a.get("big_o"), b.get("big_o"), better_version))
    notes.extend(
        _notes_for_delta(
            "Cyclomatic complexity",
            a_cyclomatic,
            b_cyclomatic,
            better_version,
            lower_is_better=True,
        )
    )
    notes.extend(
        _notes_for_delta(
            "Risk score",
            a_risk,
            b_risk,
            better_version,
            lower_is_better=True,
        )
    )

    metrics_comparison = {
        "A": {
            "big_o": a.get("big_o"),
            "cyclomatic_complexity": a_cyclomatic,
            "maintainability": a.get("maintainability"),
            "risk_score": a_risk,
            "risk_level": a.get("risk_level"),
        },
        "B": {
            "big_o": b.get("big_o"),
            "cyclomatic_complexity": b_cyclomatic,
            "maintainability": b.get("maintainability"),
            "risk_score": b_risk,
            "risk_level": b.get("risk_level"),
        },
        "delta": {
            "cyclomatic_complexity": b_cyclomatic - a_cyclomatic,
            "risk_score": b_risk - a_risk,
        },
    }

    return {
        "better_version": better_version,
        "improvement_notes": notes,
        "metrics_comparison": metrics_comparison,
    }


def _big_o_rank(big_o: str) -> int:
    """Lower rank is better."""
    s = (big_o or "").lower()
    if "n^2" in s:
        return 3
    if "n)" in s or "o(n" in s:
        return 2
    if "1" in s:
        return 1
    return 4


def _pick_better(
    *,
    a_risk: int,
    b_risk: int,
    a_cyclomatic: int,
    b_cyclomatic: int,
    a_big_o_rank: int,
    b_big_o_rank: int,
) -> str:
    # Lower risk score wins
    if a_risk != b_risk:
        return "A" if a_risk < b_risk else "B"
    # Then lower cyclomatic
    if a_cyclomatic != b_cyclomatic:
        return "A" if a_cyclomatic < b_cyclomatic else "B"
    # Then better Big‑O
    if a_big_o_rank != b_big_o_rank:
        return "A" if a_big_o_rank < b_big_o_rank else "B"
    # Always return one of A/B as requested
    return "A"


def _notes_for_metric(name: str, a_val: Any, b_val: Any, better: str) -> List[str]:
    if a_val == b_val:
        return [f"{name}: no change ({a_val})."]
    return [f"{name}: {a_val} → {b_val} (better: {better})."]


def _notes_for_delta(
    name: str,
    a_val: int,
    b_val: int,
    better: str,
    *,
    lower_is_better: bool,
) -> List[str]:
    if a_val == b_val:
        return [f"{name}: no change ({a_val})."]

    direction = "decreased" if b_val < a_val else "increased"
    if lower_is_better:
        desirability = "good" if b_val < a_val else "worse"
    else:
        desirability = "good" if b_val > a_val else "worse"

    return [f"{name}: {a_val} → {b_val} ({direction}, {desirability}; better: {better})."]

