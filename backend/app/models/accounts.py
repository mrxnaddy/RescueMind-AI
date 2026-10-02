from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, SoftDeleteMixin, TimestampMixin, TZDateTime


class Organization(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    """One property dealer business (a 'tenant')."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    business_email: Mapped[str | None] = mapped_column(String(255))
    business_phone: Mapped[str | None] = mapped_column(String(30))
    timezone: Mapped[str] = mapped_column(
        String(64), default="Asia/Karachi", server_default="Asia/Karachi"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    # Global emergency stop: when False, no campaign may send any message.
    messaging_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true()
    )

    users: Mapped[list["User"]] = relationship(back_populates="organization")


class Role(IdMixin, TimestampMixin, Base):
    """Super Admin, Property Dealer Owner, Sales Agent, Campaign Manager, Viewer."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str | None] = mapped_column(String(255))


class User(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    # Nullable because a Super Admin does not belong to one organization.
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))  # never plain text
    full_name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(30))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    last_login_at: Mapped[datetime | None] = mapped_column(TZDateTime)

    organization: Mapped["Organization"] = relationship(back_populates="users")
    role: Mapped["Role"] = relationship()