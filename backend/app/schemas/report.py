"""Scam report request/response shapes."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator

from ..models.enums import ReportStatus, ScamChannel


class ReportCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=5000)
    channel: ScamChannel = ScamChannel.OTHER
    reported_url: str | None = Field(default=None, max_length=2048)
    reported_contact: str | None = Field(
        default=None, max_length=255,
        description="Scammer phone/email/handle - never displayed publicly",
    )
    occurred_at: datetime | None = None
    assessment_id: int | None = Field(
        default=None,
        description="Optional link to a risk_assessments row from the analysis half",
    )

    @field_validator("occurred_at")
    @classmethod
    def _not_in_future(cls, value: datetime | None) -> datetime | None:
        if value and value > datetime.now(timezone.utc):
            raise ValueError("occurred_at cannot be in the future")
        return value


class VisibilityUpdate(BaseModel):
    """Admin-only report publish/unpublish (is_public defaults FALSE in DB)."""

    is_public: bool


class ReportOut(BaseModel):
    report_id: int
    reporter_id: int | None = None
    assessment_id: int | None = None
    title: str
    description: str
    channel: ScamChannel
    reported_url: str | None = None
    reported_contact: str | None = None
    occurred_at: datetime | None = None
    duplicate_of_id: int | None = None
    status: ReportStatus
    is_public: bool
    created_at: datetime

    model_config = {"from_attributes": True}
