"""LiveKit Agent Worker — livekit-agents 1.5.x compatible."""
import asyncio
import logging
import os

from dotenv import load_dotenv

load_dotenv()

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.agents.metrics import LLMMetrics, STTMetrics, TTSMetrics
from livekit.plugins import cartesia, deepgram, openai, silero

from app.agent.prompts import get_system_prompt
from app.db.session import SessionLocal
from app.models.conversation import ConversationSession
from app.agent.tools import AgentToolbox
from app.core.errors import AppError
from sqlalchemy import select

logger = logging.getLogger(__name__)


def _get_session_by_room(room_name: str) -> ConversationSession | None:
    """Lookup DB session by LiveKit room name."""
    db = SessionLocal()
    try:
        stmt = select(ConversationSession).where(
            ConversationSession.livekit_room_name == room_name
        )
        return db.execute(stmt).scalar_one_or_none()
    finally:
        db.close()


async def entrypoint(ctx: JobContext) -> None:
    """Main agent entrypoint — called once per LiveKit room job."""
    await ctx.connect()

    room_name = ctx.room.name
    logger.info("Agent joined room: %s", room_name)

    # Look up the session created by the FastAPI endpoint
    db_session = _get_session_by_room(room_name)
    if db_session is None:
        logger.warning("No DB session found for room %s — aborting.", room_name)
        return

    session_id = db_session.id
    logger.info("Linked to session_id: %s", session_id)

    # Build tool wrappers bound to this session's DB context
    db = SessionLocal()
    toolbox = AgentToolbox(db, session_id)

    # --- Define LiveKit function tools ---

    @function_tool()
    async def identify_user(phone_number: str, name: str | None = None) -> dict:
        """Identify the user by phone number. Ask phone number if not provided."""
        result = toolbox.identify_user(phone_number=phone_number, name=name)
        db.commit()
        return result

    @function_tool()
    async def fetch_slots(requested_date: str) -> dict:
        """Fetch available appointment slots for the given date (YYYY-MM-DD)."""
        from datetime import date
        parsed = date.fromisoformat(requested_date)
        result = toolbox.fetch_slots(requested_date=parsed)
        db.commit()
        return result

    @function_tool()
    async def book_appointment(
        phone_number: str,
        name: str,
        requested_date: str,
        requested_time: str,
    ) -> dict:
        """Book an appointment. Date: YYYY-MM-DD, Time: HH:MM."""
        from datetime import date, time
        parsed_date = date.fromisoformat(requested_date)
        h, m = map(int, requested_time.split(":"))
        parsed_time = time(h, m)
        try:
            result = toolbox.book_appointment(
                phone_number=phone_number,
                name=name,
                requested_date=parsed_date,
                requested_time=parsed_time,
            )
            db.commit()
        except AppError as exc:
            db.rollback()
            return {"error": exc.message}
        return result

    @function_tool()
    async def retrieve_appointments(phone_number: str) -> dict:
        """Retrieve all appointments for a user by phone number."""
        result = toolbox.retrieve_appointments(phone_number=phone_number)
        db.commit()
        return result

    @function_tool()
    async def cancel_appointment(
        phone_number: str,
        appointment_id: str | None = None,
        requested_date: str | None = None,
        requested_time: str | None = None,
    ) -> dict:
        """Cancel an appointment by ID or by date/time."""
        from datetime import date, time
        from uuid import UUID
        try:
            result = toolbox.cancel_appointment(
                phone_number=phone_number,
                appointment_id=UUID(appointment_id) if appointment_id else None,
                requested_date=date.fromisoformat(requested_date) if requested_date else None,
                requested_time=time.fromisoformat(requested_time) if requested_time else None,
            )
            db.commit()
        except AppError as exc:
            db.rollback()
            return {"error": exc.message}
        return result

    @function_tool()
    async def modify_appointment(
        phone_number: str,
        new_date: str,
        new_time: str,
        appointment_id: str | None = None,
        current_date: str | None = None,
        current_time: str | None = None,
    ) -> dict:
        """Modify an existing appointment to a new date/time."""
        from datetime import date, time
        from uuid import UUID
        try:
            result = toolbox.modify_appointment(
                phone_number=phone_number,
                appointment_id=UUID(appointment_id) if appointment_id else None,
                current_date=date.fromisoformat(current_date) if current_date else None,
                current_time=time.fromisoformat(current_time) if current_time else None,
                new_date=date.fromisoformat(new_date),
                new_time=time.fromisoformat(new_time),
            )
            db.commit()
        except AppError as exc:
            db.rollback()
            return {"error": exc.message}
        return result

    @function_tool()
    async def end_conversation() -> dict:
        """End the conversation, generate a summary, and close the session."""
        try:
            result = toolbox.end_conversation(cost=cost_data)
            db.commit()
        except Exception as exc:
            logger.error("end_conversation tool error: %s", exc)
            # Ensure session is marked ended even if summary generation fails
            try:
                db.rollback()
                toolbox.sessions.end_session(session_id)
                db.commit()
            except Exception:
                pass
            result = {"summary_text": "Summary unavailable due to an error."}

        # Disconnect from the room after a short delay so the agent can
        # finish saying goodbye before the call drops.
        async def _disconnect_after_delay() -> None:
            await asyncio.sleep(3)
            try:
                await ctx.room.disconnect()
            except Exception as e:
                logger.warning("Room disconnect error: %s", e)

        asyncio.create_task(_disconnect_after_delay())
        return result

    # Accumulates usage metrics throughout the call; read by end_conversation.
    cost_data: dict = {
        "llm_prompt_tokens": 0,
        "llm_completion_tokens": 0,
        "tts_characters": 0,
        "stt_audio_seconds": 0.0,
    }

    tools = [
        identify_user,
        fetch_slots,
        book_appointment,
        retrieve_appointments,
        cancel_appointment,
        modify_appointment,
        end_conversation,
    ]

    # --- Build and start the voice pipeline ---
    agent = Agent(
        instructions=get_system_prompt(),  # fresh date injected each call
        tools=tools,
        stt=deepgram.STT(),
        llm=openai.LLM(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        ),
        tts=cartesia.TTS(),
        vad=silero.VAD.load(),
    )

    session = AgentSession()

    @session.on("metrics_collected")
    def _on_metrics(event) -> None:
        m = event.metrics
        if isinstance(m, LLMMetrics):
            cost_data["llm_prompt_tokens"] += m.prompt_tokens
            cost_data["llm_completion_tokens"] += m.completion_tokens
        elif isinstance(m, TTSMetrics):
            cost_data["tts_characters"] += m.characters_count
        elif isinstance(m, STTMetrics):
            cost_data["stt_audio_seconds"] += m.audio_duration

    await session.start(agent=agent, room=ctx.room)

    await session.generate_reply(
        instructions="Greet the user warmly as a Mykare healthcare front-desk assistant and ask how you can help them today."
    )


def run_worker() -> None:
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))


if __name__ == "__main__":
    run_worker()
