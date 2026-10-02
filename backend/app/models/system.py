from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import (
    Base,
    CreatedAtMixin,
    IdMixin,
    OrgMixin,
    TimestampMixin,
    TZDateTime,
    enum_type,
)
from app.models.enums import JobStatus


class ScheduledJob(IdMixin, OrgMixin, TimestampMixin, Base):
    """A job to run later: campaign start, appointment reminder, follow-up reminder."""

    __tablename__ = "scheduled_jobs"

    job_type: Mapped[str] = mapped_column(String(50))
    reference_type: Mapped[str | None] = mapped_column(String(50))  # e.g. "campaign"
    reference_id: Mapped[int | None] = mapped_column(Integer)
    run_at: Mapped[datetime] = mapped_column(TZDateTime)
    status: Mapped[JobStatus] = mapped_column(enum_type(JobStatus), default=JobStatus.PENDING)
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_error: Mapped[str | None] = mapped_column(Text)
    celery_task_id: Mapped[str | None] = mapped_column(String(100))

    __table_args__ = (Index("ix_jobs_status_run_at", "status", "run_at"),)


class AuditLog(IdMixin, CreatedAtMixin, Base):
    """Who did what, and when. Never store passwords or full personal data here."""

    __tablename__ = "audit_logs"

    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    action: Mapped[str] = mapped_column(String(100))  # e.g. "campaign.launch"
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[str | None] = mapped_column(String(64))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    details: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )

    __table_args__ = (
        Index("ix_audit_org_created", "organization_id", "created_at"),
        Index("ix_audit_entity", "entity_type", "entity_id"),
    )


class AiGeneration(IdMixin, OrgMixin, CreatedAtMixin, Base):
    """Record of every AI-generated text (for review and cost tracking)."""

    __tablename__ = "ai_generations"

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    kind: Mapped[str] = mapped_column(String(50))  # e.g. "property_description"
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str | None] = mapped_column(String(100))
    language: Mapped[str | None] = mapped_column(String(20))
    tone: Mapped[str | None] = mapped_column(String(30))
    channel: Mapped[str | None] = mapped_column(String(20))
    prompt_summary: Mapped[str | None] = mapped_column(Text)
    output_text: Mapped[str] = mapped_column(Text)
    warnings: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)