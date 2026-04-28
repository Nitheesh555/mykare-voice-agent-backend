from __future__ import annotations

from typing import Annotated
from datetime import date, time
from uuid import UUID

from app.models.enums import AppointmentStatus
from pydantic import BaseModel, ConfigDict, Field, model_validator


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    appointment_date: date
    appointment_time: time
    status: AppointmentStatus
    notes: str | None = None


class IdentifyUserRequest(BaseModel):
    phone_number: str = Field(min_length=8, max_length=20)
    name: str | None = Field(default=None, max_length=255)


class IdentifyUserResponse(BaseModel):
    user_id: UUID
    name: str | None
    phone_number: str
    appointments: list[AppointmentResponse]


class FetchSlotsResponse(BaseModel):
    date: date
    available_slots: list[str]


class BookAppointmentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    phone_number: str = Field(min_length=8, max_length=20)
    name: str = Field(min_length=1, max_length=255)
    appointment_date: Annotated[date, Field(alias="date")]
    appointment_time: Annotated[time, Field(alias="time")]
    session_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=500)


class BookAppointmentResponse(BaseModel):
    message: str
    appointment: AppointmentResponse


class RetrieveAppointmentsRequest(BaseModel):
    phone_number: str = Field(min_length=8, max_length=20)


class CancelAppointmentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    phone_number: str = Field(min_length=8, max_length=20)
    appointment_id: UUID | None = None
    appointment_date: Annotated[date | None, Field(alias="date")] = None
    appointment_time: Annotated[time | None, Field(alias="time")] = None

    @model_validator(mode="after")
    def validate_reference(self) -> "CancelAppointmentRequest":
        if self.appointment_id is None and (
            self.appointment_date is None or self.appointment_time is None
        ):
            raise ValueError("Provide either appointment_id or both date and time.")
        return self


class ModifyAppointmentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    phone_number: str = Field(min_length=8, max_length=20)
    appointment_id: UUID | None = None
    current_appointment_date: Annotated[date | None, Field(alias="current_date")] = None
    current_appointment_time: Annotated[time | None, Field(alias="current_time")] = None
    new_appointment_date: Annotated[date, Field(alias="new_date")]
    new_appointment_time: Annotated[time, Field(alias="new_time")]

    @model_validator(mode="after")
    def validate_reference(self) -> "ModifyAppointmentRequest":
        if self.appointment_id is None and (
            self.current_appointment_date is None or self.current_appointment_time is None
        ):
            raise ValueError("Provide either appointment_id or both current_date and current_time.")
        return self
