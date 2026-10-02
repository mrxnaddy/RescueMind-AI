from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import (
    Base,
    CreatedAtMixin,
    IdMixin,
    OrgMixin,
    SoftDeleteMixin,
    TimestampMixin,
    TZDateTime,
    enum_type,
)
from app.models.enums import AppointmentStatus, FollowUpStatus, InterestLevel, LeadStatus


class Lead(IdMixin, OrgMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "leads"

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[LeadStatus] = mapped_column(enum_type(LeadStatus), default=LeadStatus.NEW)
    source: Mapped[str | None] = mapped_column(String(100))  # e.g. "walk-in", "facebook"
    assigned_agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    last_contact_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    next_follow_up_at: Mapped[datetime | None] = mapped_column(TZDateTime)

    __table_args__ = (
        Index("ix_leads_org_status", "organization_id", "status"),
        Index("ix_leads_org_followup", "organization_id", "next_follow_up_at"),
    )


class LeadNote(IdMixin, OrgMixin, TimestampMixin, Base):
    __tablename__ = "lead_notes"

    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    body: Mapped[str] = mapped_column(Text)


class LeadAssignment(IdMixin, OrgMixin, CreatedAtMixin, Base):
    """History of who a lead was assigned to, and by whom."""

    __tablename__ = "lead_assignments"

    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), index=True
    )
    assigned_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    assigned_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


class Appointment(IdMixin, OrgMixin, TimestampMixin, Base):
    __tablename__ = "appointments"

    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    lead_id: Mapped[int | None] = mapped_column(
        ForeignKey("leads.id", ondelete="SET NULL")
    )
    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL")
    )
    scheduled_at: Mapped[datetime] = mapped_column(TZDateTime)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30, server_default="30")
    status: Mapped[AppointmentStatus] = mapped_column(
        enum_type(AppointmentStatus), default=AppointmentStatus.REQUESTED
    )
    interest_level: Mapped[InterestLevel | None] = mapped_column(enum_type(InterestLevel))
    outcome: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    reminder_sent_at: Mapped[datetime | None] = mapped_column(TZDateTime)

    __table_args__ = (Index("ix_appointments_org_time", "organization_id", "scheduled_at"),)


class FollowUp(IdMixin, OrgMixin, TimestampMixin, Base):
    __tablename__ = "follow_ups"

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id", ondelete="SET NULL"))
    appointment_id: Mapped[int | None] = mapped_column(
        ForeignKey("appointments.id", ondelete="SET NULL")
    )
    assigned_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    due_at: Mapped[datetime] = mapped_column(TZDateTime)
    status: Mapped[FollowUpStatus] = mapped_column(
        enum_type(FollowUpStatus), default=FollowUpStatus.PENDING
    )
    notes: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(TZDateTime)

    __table_args__ = (Index("ix_followups_org_due", "organization_id", "status", "due_at"),)