import uuid
from datetime import date, time

from app.db.base import Base
from app.models.enums import AppointmentStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from sqlalchemy import Date, Enum, ForeignKey, Index, String, Time, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Appointment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "appointments"
    __table_args__ = (
        Index(
            "uq_appointments_active_slot",
            "appointment_date",
            "appointment_time",
            unique=True,
            postgresql_where=text("status = 'BOOKED'"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False)
    appointment_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status"),
        nullable=False,
        default=AppointmentStatus.BOOKED,
    )
    source_session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversation_sessions.id"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    user = relationship("User", back_populates="appointments")
    source_session = relationship("ConversationSession", back_populates="appointments")
