from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class ValidationResult:
    valid: bool
    error: str | None = None

    def to_dict(self) -> Dict[str, object]:
        return {"valid": self.valid, "error": self.error}


def _balanced_brackets(code: str) -> bool:
    stack: list[str] = []
    opening = {"(": ")", "{": "}", "[": "]"}
    closing = {v: k for k, v in opening.items()}

    for ch in code:
        if ch in opening:
            stack.append(ch)
        elif ch in closing:
            if not stack or stack[-1] != closing[ch]:
                return False
            stack.pop()
    return not stack


def _balanced_quotes(code: str) -> bool:
    # Simple even-count heuristic for quotes; good enough for snippets.
    single = code.count("'")
    double = code.count('"')
    backtick = code.count("`")
    return single % 2 == 0 and double % 2 == 0 and backtick % 2 == 0


def validate_code(language: str, code: str) -> dict:
    """Lightweight syntax/structure validation.

    For Python we use ast.parse; for other languages we only check bracket/quote
    balance and very small sanity rules so snippets remain valid.
    """
    lang = (language or "").strip().lower()

    if not code.strip():
        return ValidationResult(valid=False, error="Empty code").to_dict()

    if lang in {"generic", ""}:
        return ValidationResult(valid=True).to_dict()

    # Python – real syntax validation.
    if lang in {"py", "python"}:
        try:
            import ast

            ast.parse(code)
        except SyntaxError as exc:
            return ValidationResult(valid=False, error=str(exc)).to_dict()
        return ValidationResult(valid=True).to_dict()

    # All other languages – structural checks only.
    if not _balanced_brackets(code):
        return ValidationResult(valid=False, error="Unbalanced brackets/braces").to_dict()
    if not _balanced_quotes(code):
        return ValidationResult(valid=False, error="Unbalanced quotes").to_dict()

    # Basic semicolon sanity: if code clearly looks like a multi‑statement block
    # but has zero semicolons at all, flag it as suspicious. Single‑line or
    # expression snippets are allowed.
    lines = [ln for ln in code.splitlines() if ln.strip()]
    if len(lines) >= 3 and ";" not in code and lang in {"javascript", "typescript", "java", "c", "cpp", "c++"}:
        return ValidationResult(valid=False, error="No semicolons found in multi-line code").to_dict()

    return ValidationResult(valid=True).to_dict()

