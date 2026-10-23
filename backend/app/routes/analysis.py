"""HTTP endpoints for text analysis."""

from fastapi import APIRouter

from ..services.ai_analysis.schemas import ScamAnalysisRequest, ScamAssessment
from ..services.ai_analysis.service import analyze_text


router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.post("/analysis", response_model=ScamAssessment)
async def create_analysis(request: ScamAnalysisRequest) -> ScamAssessment:
    """Analyze a suspicious message using configured AI and baseline checks."""
    return await analyze_text(request.text)
