from enum import StrEnum


class AppointmentStatus(StrEnum):
    BOOKED = "booked"
    CANCELLED = "cancelled"
    MODIFIED = "modified"


class SessionStatus(StrEnum):
    CREATED = "created"
    ACTIVE = "active"
    ENDED = "ended"
    FAILED = "failed"


class EventType(StrEnum):
    USER_TRANSCRIPT = "user_transcript"
    AGENT_TRANSCRIPT = "agent_transcript"
    TOOL_STARTED = "tool_started"
    TOOL_SUCCEEDED = "tool_succeeded"
    TOOL_FAILED = "tool_failed"
    SYSTEM = "system"


class IntentType(StrEnum):
    BOOK = "book"
    RETRIEVE = "retrieve"
    CANCEL = "cancel"
    MODIFY = "modify"
    GENERAL = "general"
    END = "end"
