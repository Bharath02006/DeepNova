from fastapi import APIRouter

from app.models.schemas import CodeAnalysisRequest, UnifiedAnalysisResponse
from app.services import analysis_engine


router = APIRouter()


@router.post("/analyze", response_model=UnifiedAnalysisResponse)
async def analyze_code(payload: CodeAnalysisRequest) -> UnifiedAnalysisResponse:
    result = await analysis_engine.analyze_code(payload.code, payload.language)
    return UnifiedAnalysisResponse(**result)

