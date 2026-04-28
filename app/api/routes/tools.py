from datetime import date

from app.core.errors import AppError
from app.db.session import get_db
from app.schemas.appointments import (
    AppointmentResponse,
    BookAppointmentRequest,
    BookAppointmentResponse,
    CancelAppointmentRequest,
    FetchSlotsResponse,
    IdentifyUserRequest,
    IdentifyUserResponse,
    ModifyAppointmentRequest,
    RetrieveAppointmentsRequest,
)
from app.services.appointments import AppointmentService
from app.services.users import UserService
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/identify-user", response_model=IdentifyUserResponse)
def identify_user(payload: IdentifyUserRequest, db: Session = Depends(get_db)) -> IdentifyUserResponse:
    users = UserService(db)
    appointments = AppointmentService(db)
    user = users.get_or_create(payload.phone_number, payload.name)
    db.commit()
    return IdentifyUserResponse(
        user_id=user.id,
        name=user.name,
        phone_number=user.phone_number,
        appointments=[AppointmentResponse.model_validate(item) for item in appointments.list_for_user(user.phone_number)],
    )


@router.get("/fetch-slots", response_model=FetchSlotsResponse)
def fetch_slots(date: date = Query(alias="date"), db: Session = Depends(get_db)) -> FetchSlotsResponse:
    service = AppointmentService(db)
    slots = service.get_available_slots(date)
    return FetchSlotsResponse(date=date, available_slots=service.slots.serialize_slots(slots))


@router.post("/book-appointment", response_model=BookAppointmentResponse)
def book_appointment(payload: BookAppointmentRequest, db: Session = Depends(get_db)) -> BookAppointmentResponse:
    service = AppointmentService(db)
    appointment = service.book(payload)
    db.commit()
    return BookAppointmentResponse(
        message=f"Appointment booked for {appointment.appointment_date} at {appointment.appointment_time.strftime('%H:%M')}.",
        appointment=AppointmentResponse.model_validate(appointment),
    )


@router.post("/retrieve-appointments", response_model=list[AppointmentResponse])
def retrieve_appointments(
    payload: RetrieveAppointmentsRequest,
    db: Session = Depends(get_db),
) -> list[AppointmentResponse]:
    service = AppointmentService(db)
    appointments = service.list_for_user(payload.phone_number)
    return [AppointmentResponse.model_validate(item) for item in appointments]


@router.post("/cancel-appointment", response_model=AppointmentResponse)
def cancel_appointment(
    payload: CancelAppointmentRequest,
    db: Session = Depends(get_db),
) -> AppointmentResponse:
    service = AppointmentService(db)
    appointment = service.cancel(payload)
    db.commit()
    return AppointmentResponse.model_validate(appointment)


@router.post("/modify-appointment", response_model=AppointmentResponse)
def modify_appointment(
    payload: ModifyAppointmentRequest,
    db: Session = Depends(get_db),
) -> AppointmentResponse:
    service = AppointmentService(db)
    appointment = service.modify(payload)
    db.commit()
    return AppointmentResponse.model_validate(appointment)
