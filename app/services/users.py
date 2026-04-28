import re

from app.core.errors import AppError
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.orm import Session

PHONE_PATTERN = re.compile(r"^\+?[1-9]\d{7,14}$")


def normalize_phone_number(phone_number: str) -> str:
    normalized = re.sub(r"[^\d+]", "", phone_number.strip())
    if not PHONE_PATTERN.match(normalized):
        raise AppError(error_code="invalid_phone_number", message="Phone number format is invalid.")
    return normalized


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_phone(self, phone_number: str) -> User | None:
        normalized = normalize_phone_number(phone_number)
        stmt = select(User).where(User.phone_number == normalized)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_or_create(self, phone_number: str, name: str | None = None) -> User:
        normalized = normalize_phone_number(phone_number)
        existing = self.get_by_phone(normalized)
        if existing:
            if name and existing.name != name:
                existing.name = name
                self.db.add(existing)
                self.db.flush()
            return existing

        user = User(name=name, phone_number=normalized)
        self.db.add(user)
        self.db.flush()
        return user
