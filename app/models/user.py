from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)

    appointments = relationship("Appointment", back_populates="user")
    sessions = relationship("ConversationSession", back_populates="user")
