# Mykare Voice Agent Backend

Production-leaning FastAPI backend for the Mykare interview task.

## Features

- FastAPI API for sessions, appointments, summaries, and tool-facing endpoints
- SQLAlchemy models designed for Supabase Postgres
- Alembic migration setup
- Deterministic slot generation with double-booking prevention
- LiveKit session wiring with development-safe fallback tokens
- Agent scaffolding that reuses application services
- Fallback summary generation when LLM access is unavailable

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -e .[dev,voice]
```

3. Copy `.env.example` to `.env` and fill in credentials.
4. Run migrations:

```bash
alembic upgrade head
```

5. Start the API:

```bash
uvicorn app.main:app --reload
```

## Environment

The app defaults to SQLite for local development if `DATABASE_URL` is not set.
For deployment, set `DATABASE_URL` to the Supabase Postgres connection string.

## Tests

```bash
pytest
```
