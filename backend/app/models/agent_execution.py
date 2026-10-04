from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    incident_id: Mapped[int | None] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    agent_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="started",
        index=True,
    )

    input_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    output_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )