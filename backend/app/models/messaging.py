from datetime import datetime

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    false,
    text,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    IdMixin,
    OrgMixin,
    TimestampMixin,
    TZDateTime,
    enum_type,
)
from app.models.enums import Channel, MessageStatus


class Message(IdMixin, OrgMixin, TimestampMixin, Base):
    """One message to one person. Status is only 'delivered' when a provider confirms it."""

    __tablename__ = "messages"

    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL"), index=True
    )
    recipient_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_recipients.id", ondelete="SET NULL")
    )
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), index=True
    )
    direction: Mapped[str] = mapped_column(
        String(10), default="outbound", server_default="outbound"
    )  # "outbound" or "inbound" (customer replies)
    channel: Mapped[Channel] = mapped_column(enum_type(Channel))
    to_address: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[MessageStatus] = mapped_column(
        enum_type(MessageStatus), default=MessageStatus.QUEUED
    )
    provider: Mapped[str | None] = mapped_column(String(50))
    provider_message_id: Mapped[str | None] = mapped_column(String(255), index=True)
    # True for fake development messages. Never confuse these with real delivery.
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)

    queued_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    accepted_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    sent_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    read_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    failed_at: Mapped[datetime | None] = mapped_column(TZDateTime)

    events: Mapped[list["MessageEvent"]] = relationship(cascade="all, delete-orphan")

    __table_args__ = (Index("ix_messages_org_status", "organization_id", "status"),)


class MessageEvent(IdMixin, OrgMixin, Base):
    """Every status update we receive about a message (webhooks, retries, errors)."""

    __tablename__ = "message_events"

    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(50))
    provider_status: Mapped[str | None] = mapped_column(String(100))
    payload: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )  # redacted provider data
    occurred_at: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=text("now()")
    )


class Integration(IdMixin, OrgMixin, TimestampMixin, Base):
    """Settings for WhatsApp / SMS / email / AI providers."""

    __tablename__ = "integrations"

    kind: Mapped[str] = mapped_column(String(20))  # whatsapp, sms, email, ai
    provider: Mapped[str] = mapped_column(String(50))  # e.g. "mock", "whatsapp_cloud"
    display_name: Mapped[str | None] = mapped_column(String(150))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    settings: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )  # NON-secret settings only
    credentials_encrypted: Mapped[str | None] = mapped_column(Text)  # encrypted secrets
    rate_limit_per_minute: Mapped[int] = mapped_column(
        Integer, default=30, server_default="30"
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "kind", "provider", name="uq_integration"),
    )


class WebhookEvent(IdMixin, Base):
    """Raw incoming webhook calls from providers, kept for debugging and auditing."""

    __tablename__ = "webhook_events"

    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), index=True
    )
    provider: Mapped[str] = mapped_column(String(50))
    event_type: Mapped[str | None] = mapped_column(String(100))
    signature_valid: Mapped[bool | None] = mapped_column(Boolean)
    payload: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    processed: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    processing_error: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=text("now()")
    )

    __table_args__ = (Index("ix_webhook_provider_processed", "provider", "processed"),)