from app.models.enums import IntentType
from pydantic import BaseModel


class AgentExtractionState(BaseModel):
    name: str | None = None
    phone_number: str | None = None
    intent: IntentType | None = None
    requested_date: str | None = None
    requested_time: str | None = None
    appointment_reference: str | None = None
    preferences: dict = {}
    missing_fields: list[str] = []
