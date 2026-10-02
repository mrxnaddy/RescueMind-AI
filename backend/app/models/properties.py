import secrets
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
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
    CreatedAtMixin,
    IdMixin,
    OrgMixin,
    SoftDeleteMixin,
    TimestampMixin,
    TZDateTime,
    enum_type,
)
from app.models.enums import (
    FurnishingStatus,
    MatchStatus,
    PropertyCategory,
    PropertyPurpose,
    PropertyStatus,
    PropertyUse,
)


def _new_public_token() -> str:
    """Unguessable token for public property links."""
    return secrets.token_urlsafe(24)


class Property(IdMixin, OrgMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "properties"

    title: Mapped[str] = mapped_column(String(255))
    reference: Mapped[str] = mapped_column(String(50))  # e.g. "NPD-0001"
    category: Mapped[PropertyCategory] = mapped_column(enum_type(PropertyCategory), index=True)
    purpose: Mapped[PropertyPurpose] = mapped_column(enum_type(PropertyPurpose), index=True)
    use_type: Mapped[PropertyUse] = mapped_column(
        enum_type(PropertyUse), default=PropertyUse.RESIDENTIAL
    )
    status: Mapped[PropertyStatus] = mapped_column(
        enum_type(PropertyStatus), default=PropertyStatus.DRAFT
    )

    description: Mapped[str | None] = mapped_column(Text)
    ai_description: Mapped[str | None] = mapped_column(Text)

    price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    previous_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))  # for price-drop alerts
    currency: Mapped[str] = mapped_column(String(3), default="PKR", server_default="PKR")
    is_negotiable: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())

    city: Mapped[str] = mapped_column(String(100), index=True)
    neighborhood: Mapped[str | None] = mapped_column(String(150))
    address: Mapped[str | None] = mapped_column(String(500))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))

    covered_area: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    plot_area: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    area_unit: Mapped[str] = mapped_column(String(20), default="sqft", server_default="sqft")
    bedrooms: Mapped[int | None] = mapped_column(Integer)
    bathrooms: Mapped[int | None] = mapped_column(Integer)
    floor_number: Mapped[int | None] = mapped_column(Integer)
    total_floors: Mapped[int | None] = mapped_column(Integer)
    furnishing: Mapped[FurnishingStatus | None] = mapped_column(enum_type(FurnishingStatus))
    construction_year: Mapped[int | None] = mapped_column(Integer)
    parking_spaces: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    nearby_landmarks: Mapped[list[str]] = mapped_column(
        ARRAY(String(150)), default=list, server_default=text("'{}'")
    )
    video_url: Mapped[str | None] = mapped_column(String(500))
    virtual_tour_url: Mapped[str | None] = mapped_column(String(500))

    # PRIVATE owner information: never shown on public links or in messages.
    owner_name: Mapped[str | None] = mapped_column(String(200))
    owner_phone: Mapped[str | None] = mapped_column(String(30))
    owner_notes: Mapped[str | None] = mapped_column(Text)

    assigned_agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    # Public / private link support
    public_token: Mapped[str] = mapped_column(
        String(64), unique=True, default=_new_public_token
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())

    images: Mapped[list["PropertyImage"]] = relationship(cascade="all, delete-orphan")
    documents: Mapped[list["PropertyDocument"]] = relationship(cascade="all, delete-orphan")
    amenities: Mapped[list["PropertyAmenity"]] = relationship(cascade="all, delete-orphan")
    tags: Mapped[list["PropertyTag"]] = relationship(cascade="all, delete-orphan")

    __table_args__ = (
        Index(
            "uq_properties_org_reference",
            "organization_id",
            "reference",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_properties_org_status", "organization_id", "status"),
        Index("ix_properties_search", "organization_id", "city", "purpose", "category"),
        CheckConstraint("price >= 0", name="ck_properties_price_nonneg"),
    )


class PropertyImage(IdMixin, OrgMixin, TimestampMixin, Base):
    __tablename__ = "property_images"

    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True
    )
    storage_path: Mapped[str] = mapped_column(String(500))
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class PropertyDocument(IdMixin, OrgMixin, TimestampMixin, Base):
    __tablename__ = "property_documents"

    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True
    )
    storage_path: Mapped[str] = mapped_column(String(500))
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    doc_type: Mapped[str | None] = mapped_column(String(50))  # e.g. "brochure", "floor_plan"
    is_private: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())


class PropertyAmenity(IdMixin, OrgMixin, CreatedAtMixin, Base):
    __tablename__ = "property_amenities"

    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))

    __table_args__ = (
        UniqueConstraint("property_id", "name", name="uq_property_amenity"),
    )


class PropertyTag(IdMixin, OrgMixin, CreatedAtMixin, Base):
    __tablename__ = "property_tags"

    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True
    )
    tag: Mapped[str] = mapped_column(String(50))

    __table_args__ = (UniqueConstraint("property_id", "tag", name="uq_property_tag"),)


class PropertyMatch(IdMixin, OrgMixin, TimestampMixin, Base):
    """A suggested customer <-> property match, with score and reasons."""

    __tablename__ = "property_matches"

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True
    )
    score: Mapped[int] = mapped_column(Integer)  # 0 to 100
    reasons: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    status: Mapped[MatchStatus] = mapped_column(
        enum_type(MatchStatus), default=MatchStatus.SUGGESTED
    )
    approved_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column(TZDateTime)

    __table_args__ = (
        UniqueConstraint("customer_id", "property_id", name="uq_match_customer_property"),
        CheckConstraint("score >= 0 AND score <= 100", name="ck_match_score_range"),
    )