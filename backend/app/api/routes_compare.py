from fastapi import APIRouter

from app.models.schemas import CodeCompareRequest, CodeCompareResponse
from app.services import compare


router = APIRouter()


@router.post("", response_model=CodeCompareResponse)
async def compare_code(payload: CodeCompareRequest) -> CodeCompareResponse:
  base = compare.compare_versions(payload)
  metrics = await compare.compare_codes(
      payload.original_code,
      payload.modified_code,
      payload.language,
  )
  return CodeCompareResponse(
      diff=base.diff,
      risk_score=base.risk_score,
      summary=base.summary,
      metrics_comparison=metrics.get("metrics_comparison") if not metrics.get("error") else None,
      error=metrics.get("error"),
      message=metrics.get("message"),
  )

