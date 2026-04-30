from uuid import UUID

from app.db.session import get_db
from app.schemas.sessions import (
    ConversationEventResponse,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionResponse,
    SummaryResponse,
)
from app.services.events import EventService
from app.services.sessions import SessionService
from app.services.summaries import SummaryService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("", response_model=SessionCreateResponse)
def create_session(payload: SessionCreateRequest, db: Session = Depends(get_db)) -> SessionCreateResponse:
    service = SessionService(db)
    session, livekit_info = service.create_session(payload.participant_name)
    db.commit()
    return SessionCreateResponse(
        session_id=session.id,
        livekit_url=livekit_info.livekit_url,
        room_name=livekit_info.room_name,
        participant_token=livekit_info.participant_token,
        expires_at=livekit_info.expires_at,
    )


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: UUID, db: Session = Depends(get_db)) -> SessionResponse:
    session = SessionService(db).get_session(session_id)
    return SessionResponse.model_validate(session)


@router.post("/{session_id}/end", response_model=SummaryResponse)
def end_session(session_id: UUID, db: Session = Depends(get_db)) -> SummaryResponse:
    sessions = SessionService(db)
    summaries = SummaryService(db)
    sessions.end_session(session_id)
    summary = summaries.generate_summary(session_id)
    db.commit()
    return summaries.to_response(summary)


@router.get("/{session_id}/events", response_model=list[ConversationEventResponse])
def list_events(session_id: UUID, db: Session = Depends(get_db)) -> list[ConversationEventResponse]:
    events = EventService(db).list_events(session_id)
    return [ConversationEventResponse.model_validate(item) for item in events]


@router.get("/{session_id}/summary", response_model=SummaryResponse)
def get_summary(session_id: UUID, db: Session = Depends(get_db)) -> SummaryResponse:
    service = SummaryService(db)
    summary = service.generate_summary(session_id)
    db.commit()
    return service.to_response(summary)
