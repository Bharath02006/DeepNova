from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

from app.models.schemas import CodeAnalysisRequest, CodeAnalysisResponse, StructureInfo


def analyze_structure(payload: CodeAnalysisRequest) -> CodeAnalysisResponse:
    """Trivial structure extraction – can be swapped with a parser later."""
    functions: list[str] = []
    classes: list[str] = []

    for line in payload.code.splitlines():
        stripped = line.strip()
        if stripped.startswith("def "):
            name = stripped.split("def ", 1)[1].split("(", 1)[0]
            functions.append(name)
        elif stripped.startswith("class "):
            name = stripped.split("class ", 1)[1].split("(", 1)[0].split(":", 1)[0]
            classes.append(name)

    return CodeAnalysisResponse(
        file_path=payload.file_path,
        language=payload.language,
        structure=StructureInfo(functions=functions, classes=classes),
    )


def analyze_file_structure(file_paths: List[str]) -> Dict[str, Any]:
    """Hackathon-friendly file structure analysis.

    No deep parsing. Uses file extensions + lightweight keyword heuristics.
    """
    paths = [Path(p) for p in file_paths]
    total_files = len(paths)

    language_counts: Counter[str] = Counter()
    risky: List[Dict[str, Any]] = []

    for p in paths:
        language = _language_from_path(p)
        language_counts[language] += 1

        reasons = _risk_reasons_for_path(p)
        content_reasons = _risk_reasons_for_content(p)
        reasons.extend(content_reasons)

        if reasons:
            risky.append(
                {
                    "file_path": str(p),
                    "language": language,
                    "reasons": sorted(set(reasons)),
                }
            )

    language_breakdown = dict(sorted(language_counts.items(), key=lambda kv: (-kv[1], kv[0])))

    summary = _structure_summary(
        total_files=total_files,
        language_breakdown=language_breakdown,
        risky_modules=risky,
    )

    return {
        "total_files": total_files,
        "language_breakdown": language_breakdown,
        "risky_modules": risky,
        "summary": summary,
    }


def _language_from_path(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".json": "json",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".md": "markdown",
        ".sql": "sql",
        ".sh": "shell",
        ".bat": "shell",
        ".ps1": "shell",
        ".env": "env",
    }.get(ext, "other")


def _risk_reasons_for_path(path: Path) -> List[str]:
    name = str(path).lower()
    reasons: List[str] = []

    risky_name_keywords = [
        "auth",
        "login",
        "password",
        "secret",
        "token",
        "key",
        "keys",
        "crypto",
        "payment",
        "billing",
        "admin",
        "rbac",
        "acl",
        "permission",
        "oauth",
        "jwt",
        "session",
        "webhook",
    ]

    for kw in risky_name_keywords:
        if kw in name:
            reasons.append(f"name_contains:{kw}")

    if path.name.startswith(".env"):
        reasons.append("sensitive_env_file")

    return reasons


def _risk_reasons_for_content(path: Path) -> List[str]:
    """Light content scanning; best-effort and safe."""
    if not path.exists() or not path.is_file():
        return []

    # Avoid scanning very large files in a hackathon setting.
    try:
        if path.stat().st_size > 1_000_000:  # 1MB
            return ["file_too_large_to_scan"]
    except Exception:
        return []

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    lowered = text.lower()
    hits: List[str] = []

    patterns = {
        "hardcoded_password": ["password =", "pwd =", "pass =", "password:"],
        "secret_like": ["api_key", "apikey", "secret", "token", "bearer "],
        "dangerous_exec": ["eval(", "exec(", "os.system(", "subprocess.call(", "subprocess.run("],
        "sql_string": ["select ", "insert ", "update ", "delete "],
    }

    for label, needles in patterns.items():
        if any(n in lowered for n in needles):
            hits.append(label)

    return hits


def _structure_summary(
    *,
    total_files: int,
    language_breakdown: Dict[str, int],
    risky_modules: List[Dict[str, Any]],
) -> str:
    if total_files == 0:
        return "No files provided."

    top_lang = next(iter(language_breakdown.items())) if language_breakdown else ("other", total_files)
    risky_count = len(risky_modules)

    return (
        f"Scanned {total_files} files. "
        f"Top language: {top_lang[0]} ({top_lang[1]}). "
        f"Flagged {risky_count} potentially risky module(s) using simple heuristics."
    )

