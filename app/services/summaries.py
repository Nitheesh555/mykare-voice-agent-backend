from datetime import datetime, timezone
from uuid import UUID

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.conversation import ConversationSummary
from app.models.enums import EventType
from app.models.user import User
from app.schemas.sessions import SummaryResponse
from app.services.appointments import AppointmentService
from app.services.events import EventService
from app.services.sessions import SessionService
from app.services.users import UserService
from sqlalchemy import select
from sqlalchemy.orm import Session


class SummaryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.events = EventService(db)
        self.sessions = SessionService(db)
        self.appointments = AppointmentService(db)
        self.users = UserService(db)

    def get_summary(self, session_id: UUID) -> ConversationSummary:
        stmt = select(ConversationSummary).where(ConversationSummary.session_id == session_id)
        summary = self.db.execute(stmt).scalar_one_or_none()
        if not summary:
            raise AppError(error_code="summary_not_found", message="Summary not generated yet.", http_status=404)
        return summary

    def generate_summary(self, session_id: UUID) -> ConversationSummary:
        existing = self.db.execute(
            select(ConversationSummary).where(ConversationSummary.session_id == session_id)
        ).scalar_one_or_none()
        if existing:
            return existing

        session = self.sessions.get_session(session_id)
        events = self.events.list_events(session_id)
        appointments_json: list[dict] = []
        preferences = session.extracted_entities_json.get("preferences", {})
        phone_number = None
        if session.user_id:
            user = self.db.get(User, session.user_id)
            phone_number = getattr(user, "phone_number", None)
        if not phone_number:
            phone_number = session.extracted_entities_json.get("phone_number")
        if phone_number:
            appointments_json = [
                {
                    "id": str(item.id),
                    "date": item.appointment_date.isoformat(),
                    "time": item.appointment_time.strftime("%H:%M"),
                    "status": item.status.value,
                }
                for item in self.appointments.list_for_user(phone_number)
            ]

        summary_text, model_name = self._generate_summary_text(session.extracted_entities_json, events, appointments_json)
        summary = ConversationSummary(
            session_id=session_id,
            summary_text=summary_text,
            appointments_json=appointments_json,
            preferences_json=preferences,
            generated_at=datetime.now(timezone.utc),
            model_name=model_name,
        )
        self.db.add(summary)
        self.db.flush()
        self.events.create_event(
            session_id=session_id,
            event_type=EventType.SYSTEM,
            event_name="summary_generated",
            payload={"model_name": model_name or "fallback"},
        )
        return summary

    def _generate_summary_text(
        self,
        extraction_state: dict,
        events: list,
        appointments_json: list[dict],
    ) -> tuple[str, str | None]:
        if self.settings.openai_api_key:
            try:
                from openai import OpenAI
            except ImportError:
                pass
            else:
                client = OpenAI(api_key=self.settings.openai_api_key)
                transcript_lines = [
                    f"{event.event_type.value}: {event.payload_json.get('text') or event.payload_json.get('message') or event.payload_json}"
                    for event in events
                ]
                prompt = "\n".join(
                    [
                        "Summarize this healthcare scheduling call.",
                        f"Entities: {extraction_state}",
                        f"Appointments: {appointments_json}",
                        "Conversation:",
                        *transcript_lines,
                    ]
                )
                response = client.responses.create(
                    model=self.settings.openai_model,
                    input=prompt,
                )
                text = getattr(response, "output_text", "").strip()
                if text:
                    return text, self.settings.openai_model

        caller = extraction_state.get("name") or "The caller"
        intent = extraction_state.get("intent") or "general assistance"
        summary_text = (
            f"{caller} contacted the Mykare assistant for {intent}. "
            f"Captured phone number: {extraction_state.get('phone_number') or 'not provided'}. "
            f"Requested date/time: {extraction_state.get('requested_date') or 'n/a'} "
            f"{extraction_state.get('requested_time') or ''}".strip()
        )
        if appointments_json:
            summary_text += f" Appointments on record: {len(appointments_json)}."
        return summary_text, None

    def to_response(self, summary: ConversationSummary) -> SummaryResponse:
        return SummaryResponse(
            session_id=summary.session_id,
            summary_text=summary.summary_text,
            appointments=summary.appointments_json,
            preferences=summary.preferences_json,
            generated_at=summary.generated_at,
            model_name=summary.model_name,
        )
