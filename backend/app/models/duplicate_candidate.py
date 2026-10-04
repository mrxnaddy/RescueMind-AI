from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DuplicateCandidate(Base):
    """A possible duplicate pair. A human must confirm before any merge.

    incident_id           -> the newer incident that was checked
    candidate_incident_id -> the earlier incident it may duplicate
    status                -> pending, confirmed or rejected
    """

    __tablename__ = "duplicate_candidates"
    __table_args__ = (
        UniqueConstraint(
            "incident_id",
            "candidate_incident_id",
            name="uq_duplicate_candidates_pair",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    incident_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_incident_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    similarity: Mapped[float] = mapped_column(Float, nullable=False)
    factors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    reviewed_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utc_now,
        nullable=False,
    )