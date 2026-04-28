from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.core.config import Settings, get_settings
from app.core.errors import AppError


@dataclass
class LiveKitSessionInfo:
    room_name: str
    participant_token: str
    expires_at: datetime
    livekit_url: str


class LiveKitService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def create_session(self, participant_name: str | None = None) -> LiveKitSessionInfo:
        room_name = f"mykare-session-{uuid4().hex}"
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=self.settings.session_token_ttl_minutes
        )
        livekit_url = self.settings.livekit_url or "wss://dev-livekit.local"

        if self.settings.livekit_api_key and self.settings.livekit_api_secret and self.settings.livekit_url:
            try:
                from livekit import api
            except ImportError as exc:
                if not self.settings.is_dev:
                    raise AppError(
                        error_code="provider_not_installed",
                        message="LiveKit SDK is not installed.",
                    ) from exc
            else:
                token = (
                    api.AccessToken(self.settings.livekit_api_key, self.settings.livekit_api_secret)
                    .with_identity((participant_name or "guest").replace(" ", "-"))
                    .with_name(participant_name or "Guest")
                    .with_grants(api.VideoGrants(room_join=True, room=room_name))
                    .to_jwt()
                )
                return LiveKitSessionInfo(
                    room_name=room_name,
                    participant_token=token,
                    expires_at=expires_at,
                    livekit_url=livekit_url,
                )

        if not self.settings.is_dev:
            raise AppError(
                error_code="provider_credentials_missing",
                message="LiveKit credentials are required outside development mode.",
            )

        token = f"dev-token-{uuid4().hex}"
        return LiveKitSessionInfo(
            room_name=room_name,
            participant_token=token,
            expires_at=expires_at,
            livekit_url=livekit_url,
        )
