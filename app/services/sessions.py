from datetime import datetime, timezone
from uuid import UUID

from app.core.errors import AppError
from app.models.conversation import ConversationSession
from app.models.enums import EventType, IntentType, SessionStatus
from app.schemas.sessions import ExtractionState
from app.services.events import EventService
from app.services.livekit import LiveKitService, LiveKitSessionInfo
from sqlalchemy import select
from sqlalchemy.orm import Session


class SessionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.events = EventService(db)
        self.livekit = LiveKitService()

    def create_session(self, participant_name: str | None = None) -> tuple[ConversationSession, LiveKitSessionInfo]:
        livekit_info = self.livekit.create_session(participant_name)
        session = ConversationSession(
            livekit_room_name=livekit_info.room_name,
            status=SessionStatus.CREATED,
            extracted_entities_json=ExtractionState().model_dump(),
        )
        self.db.add(session)
        self.db.flush()
        self.events.create_event(
            session_id=session.id,
            event_type=EventType.SYSTEM,
            event_name="session_started",
            payload={"room_name": livekit_info.room_name},
        )
        return session, livekit_info

    def get_session(self, session_id: UUID) -> ConversationSession:
        stmt = select(ConversationSession).where(ConversationSession.id == session_id)
        session = self.db.execute(stmt).scalar_one_or_none()
        if not session:
            raise AppError(error_code="session_not_found", message="Conversation session not found.")
        return session

    def update_extraction_state(
        self,
        session: ConversationSession,
        *,
        updates: dict,
        latest_intent: IntentType | None = None,
    ) -> ConversationSession:
        merged = {**session.extracted_entities_json, **updates}
        session.extracted_entities_json = merged
        if latest_intent:
            session.latest_intent = latest_intent
        if session.status == SessionStatus.CREATED:
            session.status = SessionStatus.ACTIVE
        self.db.add(session)
        self.db.flush()
        return session

    def end_session(self, session_id: UUID) -> ConversationSession:
        session = self.get_session(session_id)
        session.status = SessionStatus.ENDED
        session.ended_at = datetime.now(timezone.utc)
        self.db.add(session)
        self.db.flush()
        self.events.create_event(
            session_id=session.id,
            event_type=EventType.SYSTEM,
            event_name="session_ended",
            payload={"ended_at": session.ended_at.isoformat()},
        )
        return session
