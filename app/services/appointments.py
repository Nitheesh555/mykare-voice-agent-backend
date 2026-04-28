from datetime import date, time
from uuid import UUID

from app.core.errors import AppError
from app.models.appointment import Appointment
from app.models.conversation import ConversationSession
from app.models.enums import AppointmentStatus
from app.schemas.appointments import (
    BookAppointmentRequest,
    CancelAppointmentRequest,
    ModifyAppointmentRequest,
)
from app.services.events import EventService
from app.services.slots import SlotService
from app.services.users import UserService
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class AppointmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserService(db)
        self.events = EventService(db)
        self.slots = SlotService()

    def _active_appointments_stmt(self, for_date: date):
        return select(Appointment).where(
            and_(
                Appointment.appointment_date == for_date,
                Appointment.status == AppointmentStatus.BOOKED,
            )
        )

    def list_for_user(self, phone_number: str) -> list[Appointment]:
        user = self.users.get_by_phone(phone_number)
        if not user:
            return []
        stmt = select(Appointment).where(Appointment.user_id == user.id).order_by(
            Appointment.appointment_date.asc(),
            Appointment.appointment_time.asc(),
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_available_slots(self, for_date: date) -> list[time]:
        all_slots = self.slots.generate_slots(for_date)
        booked = {
            appointment.appointment_time
            for appointment in self.db.execute(self._active_appointments_stmt(for_date)).scalars().all()
        }
        return [slot for slot in all_slots if slot not in booked]

    def book(self, payload: BookAppointmentRequest) -> Appointment:
        user = self.users.get_or_create(payload.phone_number, payload.name)
        if payload.appointment_time not in self.get_available_slots(payload.appointment_date):
            raise AppError(error_code="slot_unavailable", message="The requested slot is not available.")

        appointment = Appointment(
            user_id=user.id,
            appointment_date=payload.appointment_date,
            appointment_time=payload.appointment_time.replace(second=0, microsecond=0),
            status=AppointmentStatus.BOOKED,
            source_session_id=payload.session_id,
            notes=payload.notes,
        )
        self.db.add(appointment)
        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError(
                error_code="double_booking_conflict",
                message="An appointment already exists for that slot.",
            ) from exc
        if payload.session_id:
            session = self.db.get(ConversationSession, payload.session_id)
            if session:
                session.user_id = user.id
                extracted = {**session.extracted_entities_json}
                extracted.update(
                    {
                        "name": user.name,
                        "phone_number": user.phone_number,
                        "requested_date": payload.appointment_date.isoformat(),
                        "requested_time": payload.appointment_time.strftime("%H:%M"),
                    }
                )
                session.extracted_entities_json = extracted
                self.db.add(session)
                self.db.flush()
        return appointment

    def _resolve_appointment(
        self,
        *,
        phone_number: str,
        appointment_id: UUID | None,
        appointment_date: date | None,
        appointment_time: time | None,
    ) -> Appointment:
        user = self.users.get_by_phone(phone_number)
        if not user:
            raise AppError(error_code="user_not_found", message="No user found for that phone number.")

        stmt = select(Appointment).where(Appointment.user_id == user.id)
        if appointment_id:
            stmt = stmt.where(Appointment.id == appointment_id)
        else:
            stmt = stmt.where(
                and_(
                    Appointment.appointment_date == appointment_date,
                    Appointment.appointment_time == appointment_time,
                )
            )
        appointment = self.db.execute(stmt).scalar_one_or_none()
        if not appointment:
            raise AppError(error_code="appointment_not_found", message="Appointment not found.")
        return appointment

    def cancel(self, payload: CancelAppointmentRequest) -> Appointment:
        appointment = self._resolve_appointment(
            phone_number=payload.phone_number,
            appointment_id=payload.appointment_id,
            appointment_date=payload.appointment_date,
            appointment_time=payload.appointment_time,
        )
        appointment.status = AppointmentStatus.CANCELLED
        self.db.add(appointment)
        self.db.flush()
        return appointment

    def modify(self, payload: ModifyAppointmentRequest) -> Appointment:
        current_appointment = self._resolve_appointment(
            phone_number=payload.phone_number,
            appointment_id=payload.appointment_id,
            appointment_date=payload.current_appointment_date,
            appointment_time=payload.current_appointment_time,
        )
        if payload.new_appointment_time not in self.get_available_slots(payload.new_appointment_date):
            raise AppError(error_code="slot_unavailable", message="The new slot is not available.")

        current_appointment.status = AppointmentStatus.MODIFIED
        self.db.add(current_appointment)
        replacement = Appointment(
            user_id=current_appointment.user_id,
            appointment_date=payload.new_appointment_date,
            appointment_time=payload.new_appointment_time.replace(second=0, microsecond=0),
            status=AppointmentStatus.BOOKED,
            source_session_id=current_appointment.source_session_id,
            notes=current_appointment.notes,
        )
        self.db.add(replacement)
        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError(
                error_code="double_booking_conflict",
                message="An appointment already exists for the requested new slot.",
            ) from exc
        return replacement
