from app.agent.prompts import SYSTEM_PROMPT


def build_agent_config() -> dict:
    return {
        "name": "mykare-frontdesk-agent",
        "system_prompt": SYSTEM_PROMPT,
        "providers": {
            "stt": "deepgram",
            "tts": "cartesia",
            "llm": "openai",
        },
    }


def run_worker() -> None:
    try:
        from livekit.agents import cli
    except ImportError as exc:
        raise RuntimeError("livekit-agents is required to run the worker.") from exc

    cli.run_app(build_agent_config())
