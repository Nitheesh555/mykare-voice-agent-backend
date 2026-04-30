import uuid
from datetime import datetime

from app.db.base import Base
from app.models.enums import EventType, IntentType, SessionStatus
from app.models.mixins import UUIDPrimaryKeyMixin, utcnow
from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


def json_type():
    return JSON().with_variant(JSONB, "postgresql")


class ConversationSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "conversation_sessions"

    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    livekit_room_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status"),
        nullable=False,
        default=SessionStatus.CREATED,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    latest_intent: Mapped[IntentType | None] = mapped_column(
        Enum(IntentType, name="intent_type"),
        nullable=True,
    )
    extracted_entities_json: Mapped[dict] = mapped_column(json_type(), default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user = relationship("User", back_populates="sessions")
    events = relationship("ConversationEvent", back_populates="session", cascade="all, delete-orphan")
    summary = relationship("ConversationSummary", back_populates="session", uselist=False)
    appointments = relationship("Appointment", back_populates="source_session")


class ConversationEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "conversation_events"
    __table_args__ = (Index("ix_conversation_events_session_id_created_at", "session_id", "created_at"),)

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversation_sessions.id"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[EventType] = mapped_column(Enum(EventType, name="event_type"), nullable=False)
    event_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_json: Mapped[dict] = mapped_column(json_type(), default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    session = relationship("ConversationSession", back_populates="events")


class ConversationSummary(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "conversation_summaries"
    __table_args__ = (Index("ix_conversation_summaries_session_id", "session_id"),)

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversation_sessions.id"),
        nullable=False,
        unique=True,
    )
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    appointments_json: Mapped[list[dict]] = mapped_column(json_type(), default=list, nullable=False)
    preferences_json: Mapped[dict] = mapped_column(json_type(), default=dict, nullable=False)
    cost_json: Mapped[dict] = mapped_column(json_type(), default=dict, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    session = relationship("ConversationSession", back_populates="summary")
