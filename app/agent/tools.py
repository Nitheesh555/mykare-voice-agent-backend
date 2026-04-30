from datetime import date, time
from uuid import UUID

from app.models.enums import EventType, IntentType
from app.schemas.appointments import (
    BookAppointmentRequest,
    CancelAppointmentRequest,
    ModifyAppointmentRequest,
)
from app.services.appointments import AppointmentService
from app.services.events import EventService
from app.services.sessions import SessionService
from app.services.summaries import SummaryService
from sqlalchemy.orm import Session


class AgentToolbox:
    def __init__(self, db: Session, session_id: UUID) -> None:
        self.db = db
        self.session_id = session_id
        self.appointments = AppointmentService(db)
        self.events = EventService(db)
        self.sessions = SessionService(db)
        self.summaries = SummaryService(db)

    def _emit(self, event_type: EventType, event_name: str, payload: dict) -> None:
        self.events.create_event(
            session_id=self.session_id,
            event_type=event_type,
            event_name=event_name,
            payload=payload,
        )

    def identify_user(self, *, phone_number: str, name: str | None = None) -> dict:
        self._emit(EventType.TOOL_STARTED, "identify_user", {"phone_number": phone_number})
        user = self.appointments.users.get_or_create(phone_number, name)
        appointments = self.appointments.list_for_user(phone_number)
        session = self.sessions.get_session(self.session_id)
        session.user_id = user.id
        self.sessions.update_extraction_state(
            session,
            updates={"name": user.name, "phone_number": user.phone_number},
        )
        result = {
            "user_id": str(user.id),
            "name": user.name,
            "phone_number": user.phone_number,
            "appointments": [
                {
                    "id": str(item.id),
                    "date": item.appointment_date.isoformat(),
                    "time": item.appointment_time.strftime("%H:%M"),
                    "status": item.status.value,
                }
                for item in appointments
            ],
        }
        self._emit(EventType.TOOL_SUCCEEDED, "identify_user", result)
        return result

    def fetch_slots(self, *, requested_date: date) -> dict:
        self._emit(EventType.TOOL_STARTED, "fetch_slots", {"date": requested_date.isoformat()})
        slots = self.appointments.get_available_slots(requested_date)
        result = {"date": requested_date.isoformat(), "slots": self.appointments.slots.serialize_slots(slots)}
        session = self.sessions.get_session(self.session_id)
        self.sessions.update_extraction_state(
            session,
            updates={"requested_date": requested_date.isoformat()},
            latest_intent=IntentType.BOOK,
        )
        self._emit(EventType.TOOL_SUCCEEDED, "fetch_slots", result)
        return result

    def book_appointment(self, *, phone_number: str, name: str, requested_date: date, requested_time: time) -> dict:
        self._emit(
            EventType.TOOL_STARTED,
            "book_appointment",
            {"phone_number": phone_number, "date": requested_date.isoformat(), "time": requested_time.strftime("%H:%M")},
        )
        appointment = self.appointments.book(
            BookAppointmentRequest(
                phone_number=phone_number,
                name=name,
                appointment_date=requested_date,
                appointment_time=requested_time,
                session_id=self.session_id,
            )
        )
        session = self.sessions.get_session(self.session_id)
        self.sessions.update_extraction_state(
            session,
            updates={
                "name": name,
                "phone_number": phone_number,
                "requested_date": requested_date.isoformat(),
                "requested_time": requested_time.strftime("%H:%M"),
            },
            latest_intent=IntentType.BOOK,
        )
        result = {"appointment_id": str(appointment.id), "status": appointment.status.value}
        self._emit(EventType.TOOL_SUCCEEDED, "book_appointment", result)
        return result

    def retrieve_appointments(self, *, phone_number: str) -> dict:
        self._emit(EventType.TOOL_STARTED, "retrieve_appointments", {"phone_number": phone_number})
        appointments = self.appointments.list_for_user(phone_number)
        result = {
            "appointments": [
                {
                    "id": str(item.id),
                    "date": item.appointment_date.isoformat(),
                    "time": item.appointment_time.strftime("%H:%M"),
                    "status": item.status.value,
                }
                for item in appointments
            ]
        }
        self._emit(EventType.TOOL_SUCCEEDED, "retrieve_appointments", result)
        return result

    def cancel_appointment(
        self,
        *,
        phone_number: str,
        appointment_id: UUID | None = None,
        requested_date: date | None = None,
        requested_time: time | None = None,
    ) -> dict:
        self._emit(EventType.TOOL_STARTED, "cancel_appointment", {"phone_number": phone_number})
        appointment = self.appointments.cancel(
            CancelAppointmentRequest(
                phone_number=phone_number,
                appointment_id=appointment_id,
                appointment_date=requested_date,
                appointment_time=requested_time,
            )
        )
        result = {"appointment_id": str(appointment.id), "status": appointment.status.value}
        self._emit(EventType.TOOL_SUCCEEDED, "cancel_appointment", result)
        return result

    def modify_appointment(
        self,
        *,
        phone_number: str,
        appointment_id: UUID | None,
        current_date: date | None,
        current_time: time | None,
        new_date: date,
        new_time: time,
    ) -> dict:
        self._emit(EventType.TOOL_STARTED, "modify_appointment", {"phone_number": phone_number})
        appointment = self.appointments.modify(
            ModifyAppointmentRequest(
                phone_number=phone_number,
                appointment_id=appointment_id,
                current_appointment_date=current_date,
                current_appointment_time=current_time,
                new_appointment_date=new_date,
                new_appointment_time=new_time,
            )
        )
        result = {
            "appointment_id": str(appointment.id),
            "new_date": appointment.appointment_date.isoformat(),
            "new_time": appointment.appointment_time.strftime("%H:%M"),
            "status": appointment.status.value,
        }
        self._emit(EventType.TOOL_SUCCEEDED, "modify_appointment", result)
        return result

    def end_conversation(self, cost: dict | None = None) -> dict:
        self._emit(EventType.TOOL_STARTED, "end_conversation", {})
        self.sessions.end_session(self.session_id)
        summary = self.summaries.generate_summary(self.session_id, cost=cost)
        result = {"summary_text": summary.summary_text}
        self._emit(EventType.TOOL_SUCCEEDED, "end_conversation", result)
        return result
