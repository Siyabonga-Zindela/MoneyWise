"""Data shapes used by the scam analysis service."""

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class RiskCategory(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    INCONCLUSIVE = "inconclusive"


class IndicatorSeverity(str, Enum):
    MEDIUM = "medium"
    HIGH = "high"


class ScamAnalysisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)

    @field_validator("text", mode="before")
    @classmethod
    def strip_text(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class AnalysisIndicator(BaseModel):
    code: str
    title: str
    explanation: str
    evidence: str
    severity: IndicatorSeverity


class ScamAssessment(BaseModel):
    category: RiskCategory
    indicators: list[AnalysisIndicator] = Field(default_factory=list)
    explanation: str
    next_steps: list[str]
    limitations: str
    source: str = "deterministic_rules"


class AIAnalysisExplanation(BaseModel):
    explanation: str = Field(min_length=1, max_length=1200)
    next_steps: list[Annotated[str, Field(min_length=1, max_length=300)]] = Field(
        min_length=1, max_length=5
    )
    limitations: str = Field(min_length=1, max_length=800)
