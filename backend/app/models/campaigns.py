from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, UniqueConstraint, text, true
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    CreatedAtMixin,
    IdMixin,
    OrgMixin,
    TimestampMixin,
    TZDateTime,
    enum_type,
)
from app.models.enums import (
    CampaignStatus,
    CampaignType,
    Channel,
    MessageLanguage,
    RecipientStatus,
    TemplateApprovalStatus,
)


class MessageTemplate(IdMixin, OrgMixin, TimestampMixin, Base):
    __tablename__ = "message_templates"

    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50))  # e.g. "new_property_alert"
    channel: Mapped[Channel] = mapped_column(enum_type(Channel))
    language: Mapped[MessageLanguage] = mapped_column(
        enum_type(MessageLanguage), default=MessageLanguage.ENGLISH
    )
    subject: Mapped[str | None] = mapped_column(String(255))  # email only
    body: Mapped[str] = mapped_column(Text)
    variables: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    # WhatsApp templates must be approved by the official platform before use.
    whatsapp_template_name: Mapped[str | None] = mapped_column(String(200))
    approval_status: Mapped[TemplateApprovalStatus] = mapped_column(
        enum_type(TemplateApprovalStatus), default=TemplateApprovalStatus.NOT_APPLICABLE
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )


class Campaign(IdMixin, OrgMixin, TimestampMixin, Base):
    __tablename__ = "campaigns"

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    objective: Mapped[str | None] = mapped_column(Text)
    campaign_type: Mapped[CampaignType] = mapped_column(
        enum_type(CampaignType), default=CampaignType.CUSTOM
    )
    channel: Mapped[Channel] = mapped_column(enum_type(Channel))
    status: Mapped[CampaignStatus] = mapped_column(
        enum_type(CampaignStatus), default=CampaignStatus.DRAFT
    )
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("message_templates.id", ondelete="SET NULL")
    )
    language: Mapped[MessageLanguage] = mapped_column(
        enum_type(MessageLanguage), default=MessageLanguage.ENGLISH
    )
    subject: Mapped[str | None] = mapped_column(String(255))
    message_body: Mapped[str | None] = mapped_column(Text)
    is_personalized: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true()
    )
    audience_filter: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    follow_up_settings: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    timezone: Mapped[str] = mapped_column(
        String(64), default="Asia/Karachi", server_default="Asia/Karachi"
    )
    started_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    completed_at: Mapped[datetime | None] = mapped_column(TZDateTime)

    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    # The mandatory human review step: who approved this campaign, and when.
    approved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column(TZDateTime)

    properties: Mapped[list["CampaignProperty"]] = relationship(
        cascade="all, delete-orphan"
    )
    recipients: Mapped[list["CampaignRecipient"]] = relationship(
        cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_campaigns_org_status", "organization_id", "status"),)


class CampaignProperty(IdMixin, OrgMixin, CreatedAtMixin, Base):
    __tablename__ = "campaign_properties"

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True
    )

    __table_args__ = (
        UniqueConstraint("campaign_id", "property_id", name="uq_campaign_property"),
    )


class CampaignRecipient(IdMixin, OrgMixin, TimestampMixin, Base):
    __tablename__ = "campaign_recipients"

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    property_id: Mapped[int | None] = mapped_column(
        ForeignKey("properties.id", ondelete="SET NULL")
    )
    status: Mapped[RecipientStatus] = mapped_column(
        enum_type(RecipientStatus), default=RecipientStatus.PENDING
    )
    exclusion_reason: Mapped[str | None] = mapped_column(String(100))
    # Prevents sending the same campaign to the same person twice.
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)

    __table_args__ = (
        UniqueConstraint("campaign_id", "customer_id", name="uq_campaign_customer"),
    )