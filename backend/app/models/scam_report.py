"""scam_reports table - duplicates are LINKED via duplicate_of_id, never merged."""

from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Boolean, DateTime, ForeignKey, Identity, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base
from .enums import ReportStatus, ScamChannel, pg_enum


class ScamReport(Base):
    __tablename__ = "scam_reports"

    report_id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True
    )
    reporter_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL")
    )
    # References the partner's risk_assessments table. The FK exists in the DB
    # (baseline), but deliberately NOT here: the partner's models are not part
    # of this metadata yet, and SQLAlchemy needs the target table in-metadata
    # to build a ForeignKey. Declare the FK in a model once the partner's half
    # lands. Insert behaviour is identical (DB still enforces the FK).
    assessment_id: Mapped[int | None] = mapped_column(BigInteger)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[ScamChannel] = mapped_column(
        pg_enum(ScamChannel, "scam_channel"),
        nullable=False,
        server_default=text("'OTHER'"),
    )
    reported_url: Mapped[str | None] = mapped_column(String(2048))
    reported_contact: Mapped[str | None] = mapped_column(String(255))
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    content_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    duplicate_of_id: Mapped[int | None] = mapped_column(
        ForeignKey("scam_reports.report_id", ondelete="SET NULL")
    )
    status: Mapped[ReportStatus] = mapped_column(
        pg_enum(ReportStatus, "report_status"),
        nullable=False,
        server_default=text("'SUBMITTED'"),
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
