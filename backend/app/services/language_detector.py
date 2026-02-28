from __future__ import annotations

from typing import Dict


def detect_language(code: str) -> Dict[str, object]:
    """Heuristic language detector with confidence scoring.

    Returns:
    {
      "language": str,   # e.g. "python", "javascript", "java", "cpp", "c", "typescript", "generic"
      "confidence": float  # 0.0–1.0
    }
    """
    snippet = code.lower()

    signals = {
        "python": ["def ", "import ", "print(", "async def", "self", "elif ", "lambda "],
        "javascript": ["console.log", "function ", "=>", "var ", "let ", "const "],
        "java": ["public class", "system.out", "public static void"],
        "cpp": ["#include", "std::", "cout<<", "cout <<"],
        "c": ["printf(", "scanf(", "int main("],
        "typescript": ["interface ", "type ", ": string", ": number"],
    }

    scores: Dict[str, int] = {lang: 0 for lang in signals.keys()}

    for lang, patterns in signals.items():
        for pat in patterns:
            if pat in snippet:
                scores[lang] += 1

    # Pick best scoring language.
    best_lang = "generic"
    best_score = 0
    for lang, score in scores.items():
        if score > best_score:
            best_lang = lang
            best_score = score

    if best_score == 0:
        return {"language": "generic", "confidence": 0.0}

    max_possible = len(signals[best_lang]) or 1
    confidence = min(1.0, best_score / float(max_possible))

    return {"language": best_lang, "confidence": confidence}

