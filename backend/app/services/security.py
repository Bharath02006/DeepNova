from app.models.schemas import CodeAnalysisRequest, CodeAnalysisResponse, Issue


def analyze_security(payload: CodeAnalysisRequest) -> CodeAnalysisResponse:
    """Toy security checks – extend with real rules or AI later."""
    issues: list[Issue] = []
    lowered = payload.code.lower()

    suspicious_patterns = [
        "eval(",
        "exec(",
        "os.system(",
        "subprocess.call(",
        "password",
        "secret",
        "api_key",
    ]

    for pattern in suspicious_patterns:
        if pattern in lowered:
            issues.append(
                Issue(
                    type="security",
                    message=f"Suspicious pattern detected: {pattern}",
                    severity="warning",
                )
            )

    return CodeAnalysisResponse(
        file_path=payload.file_path,
        language=payload.language,
        security_findings=issues,
    )

