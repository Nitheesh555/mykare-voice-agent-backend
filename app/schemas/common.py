from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict = {}


class TimestampedResponse(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
