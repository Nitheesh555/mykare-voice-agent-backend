from datetime import datetime
from uuid import UUID

from app.models.enums import EventType, IntentType, SessionStatus
from pydantic import BaseModel, ConfigDict


class ExtractionState(BaseModel):
    name: str | None = None
    phone_number: str | None = None
    intent: IntentType | None = None
    requested_date: str | None = None
    requested_time: str | None = None
    appointment_reference: str | None = None
    preferences: dict = {}
    missing_fields: list[str] = []


class SessionCreateRequest(BaseModel):
    participant_name: str | None = None


class SessionCreateResponse(BaseModel):
    session_id: UUID
    livekit_url: str
    room_name: str
    participant_token: str
    expires_at: datetime


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    livekit_room_name: str
    status: SessionStatus
    started_at: datetime
    ended_at: datetime | None
    latest_intent: IntentType | None
    extracted_entities_json: dict


class ConversationEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    event_type: EventType
    event_name: str | None
    payload_json: dict
    created_at: datetime


class SummaryResponse(BaseModel):
    session_id: UUID
    summary_text: str
    appointments: list[dict]
    preferences: dict
    cost: dict = {}
    generated_at: datetime
    model_name: str | None
