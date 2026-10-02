from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
from app.models.enums import (
    Channel,
    ConsentStatus,
    CustomerType,
    FurnishingStatus,
    PropertyPurpose,
    PropertyUse,
    SuppressionReason,
)


class Customer(IdMixin, OrgMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "customers"

    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(20))  # international format, e.g. +923001234567
    email: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    occupation: Mapped[str | None] = mapped_column(String(100))
    customer_type: Mapped[CustomerType] = mapped_column(
        enum_type(CustomerType), default=CustomerType.GENERAL_INQUIRY, index=True
    )
    custom_fields: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )

    requirements: Mapped[list["CustomerRequirement"]] = relationship(
        cascade="all, delete-orphan"
    )
    consents: Mapped[list["CustomerConsent"]] = relationship(cascade="all, delete-orphan")
    tags: Mapped[list["CustomerTag"]] = relationship(cascade="all, delete-orphan")

    __table_args__ = (
        # No two active customers in one organization may share a phone or email.
        Index(
            "uq_customers_org_phone",
            "organization_id",
            "phone",
            unique=True,
            postgresql_where=text("phone IS NOT NULL AND deleted_at IS NULL"),
        ),
        Index(
            "uq_customers_org_email",
            "organization_id",
            "email",
            unique=True,
            postgresql_where=text("email IS NOT NULL AND deleted_at IS NULL"),
        ),
        Index("ix_customers_org_city", "organization_id", "city"),
    )


class CustomerRequirement(IdMixin, OrgMixin, TimestampMixin, Base):
    """What a customer is looking for (used by the matching engine)."""

    __tablename__ = "customer_requirements"

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    property_categories: Mapped[list[str]] = mapped_column(
        ARRAY(String(32)), default=list, server_default=text("'{}'")
    )
    preferred_locations: Mapped[list[str]] = mapped_column(
        ARRAY(String(150)), default=list, server_default=text("'{}'")
    )
    purpose: Mapped[PropertyPurpose | None] = mapped_column(enum_type(PropertyPurpose))
    use_preference: Mapped[PropertyUse | None] = mapped_column(enum_type(PropertyUse))
    min_budget: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    max_budget: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    min_area: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    max_area: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    area_unit: Mapped[str] = mapped_column(String(20), default="sqft", server_default="sqft")
    min_bedrooms: Mapped[int | None] = mapped_column(Integer)
    min_bathrooms: Mapped[int | None] = mapped_column(Integer)
    furnishing_preference: Mapped[FurnishingStatus | None] = mapped_column(
        enum_type(FurnishingStatus)
    )
    required_amenities: Mapped[list[str]] = mapped_column(
        ARRAY(String(100)), default=list, server_default=text("'{}'")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint(
            "max_budget IS NULL OR min_budget IS NULL OR max_budget >= min_budget",
            name="ck_requirements_budget_range",
        ),
        CheckConstraint(
            "max_area IS NULL OR min_area IS NULL OR max_area >= min_area",
            name="ck_requirements_area_range",
        ),
    )


class CustomerGroup(IdMixin, OrgMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "customer_groups"

    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text)


class CustomerGroupMember(IdMixin, OrgMixin, CreatedAtMixin, Base):
    __tablename__ = "customer_group_members"

    group_id: Mapped[int] = mapped_column(
        ForeignKey("customer_groups.id", ondelete="CASCADE"), index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )

    __table_args__ = (
        UniqueConstraint("group_id", "customer_id", name="uq_group_member"),
    )


class CustomerTag(IdMixin, OrgMixin, CreatedAtMixin, Base):
    __tablename__ = "customer_tags"

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    tag: Mapped[str] = mapped_column(String(50))

    __table_args__ = (UniqueConstraint("customer_id", "tag", name="uq_customer_tag"),)


class CustomerConsent(IdMixin, OrgMixin, CreatedAtMixin, Base):
    """
    Consent HISTORY per channel. Rows are never overwritten:
    the newest row for a customer + channel is the current consent state.
    """

    __tablename__ = "customer_consents"

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    channel: Mapped[Channel] = mapped_column(enum_type(Channel))
    status: Mapped[ConsentStatus] = mapped_column(enum_type(ConsentStatus))
    source: Mapped[str] = mapped_column(String(100))  # e.g. "website_form", "whatsapp_optin"
    evidence_note: Mapped[str | None] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=text("now()")
    )
    recorded_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    __table_args__ = (
        Index("ix_consents_customer_channel", "customer_id", "channel", "recorded_at"),
    )


class SuppressionEntry(IdMixin, OrgMixin, CreatedAtMixin, Base):
    """Phone numbers / emails that must NEVER be contacted on a channel."""

    __tablename__ = "suppression_lists"

    channel: Mapped[Channel] = mapped_column(enum_type(Channel))
    address: Mapped[str] = mapped_column(String(255))  # phone number or email
    reason: Mapped[SuppressionReason] = mapped_column(enum_type(SuppressionReason))
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), index=True
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "channel", "address", name="uq_suppression_entry"
        ),
    )