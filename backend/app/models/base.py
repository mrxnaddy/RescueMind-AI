from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

# A timestamp that remembers its time zone.
TZDateTime = DateTime(timezone=True)


class Base(DeclarativeBase):
    """All models inherit from this."""


def enum_type(enum_cls) -> SAEnum:
    """Store an enum as readable text (e.g. 'available') with a length limit."""
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=32,
        validate_strings=True,
        values_callable=lambda members: [m.value for m in members],
    )


class IdMixin:
    id: Mapped[int] = mapped_column(primary_key=True)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(TZDateTime, server_default=func.now())


class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=func.now(), onupdate=func.now()
    )


class SoftDeleteMixin:
    """Records are marked deleted instead of being erased."""

    deleted_at: Mapped[datetime | None] = mapped_column(TZDateTime, nullable=True)


class OrgMixin:
    """Every business record belongs to one organization (data isolation)."""

    @declared_attr
    def organization_id(cls) -> Mapped[int]:
        return mapped_column(
            ForeignKey("organizations.id", ondelete="CASCADE"), index=True
        )