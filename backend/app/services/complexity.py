from app.models.schemas import CodeAnalysisRequest, CodeAnalysisResponse


def analyze_complexity(payload: CodeAnalysisRequest) -> CodeAnalysisResponse:
    """Very lightweight complexity heuristic for hackathon use."""
    line_count = len(payload.code.splitlines())
    complexity = float(line_count)

    return CodeAnalysisResponse(
        file_path=payload.file_path,
        language=payload.language,
        complexity=complexity,
    )

