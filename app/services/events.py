from uuid import UUID

from app.models.conversation import ConversationEvent
from app.models.enums import EventType
from sqlalchemy import select
from sqlalchemy.orm import Session


class EventService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_event(
        self,
        *,
        session_id: UUID,
        event_type: EventType,
        event_name: str | None = None,
        payload: dict | None = None,
    ) -> ConversationEvent:
        event = ConversationEvent(
            session_id=session_id,
            event_type=event_type,
            event_name=event_name,
            payload_json=payload or {},
        )
        self.db.add(event)
        self.db.flush()
        return event

    def list_events(self, session_id: UUID) -> list[ConversationEvent]:
        stmt = (
            select(ConversationEvent)
            .where(ConversationEvent.session_id == session_id)
            .order_by(ConversationEvent.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())
