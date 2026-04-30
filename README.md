# Mykare Voice Agent — Backend

FastAPI backend for the Mykare AI voice appointment agent. Handles session management, appointment booking, LiveKit room wiring, and hosts the LiveKit agent worker.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + Uvicorn |
| Agent | LiveKit Agents |
| STT | Deepgram |
| TTS | Cartesia |
| LLM | OpenAI (gpt-4o-mini) |
| DB | SQLite (dev) / PostgreSQL (prod) |
| ORM | SQLAlchemy 2 + Alembic |

## Features

- Voice session lifecycle — create room, issue LiveKit token, track state
- 6 agent tools: `identify_user`, `fetch_slots`, `book_appointment`, `retrieve_appointments`, `cancel_appointment`, `modify_appointment`
- Double-booking prevention with deterministic slot generation
- Conversation event streaming for real-time UI updates
- Call summary generation with cost tracking (tokens, TTS chars, STT seconds)
- Health check endpoint at `/health`

## Local Development

**Requirements:** Python 3.12+

```bash
# 1. Create and activate a virtual environment
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate

# 2. Install all dependencies including voice providers
pip install -e ".[dev,voice]"

# 3. Copy and fill in environment variables
cp .env.example .env

# 4. Start the API server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

**To run the LiveKit agent worker** (separate terminal):

```bash
python -m app.agent.worker start
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | No | Defaults to `sqlite:///./mykare.db` |
| `LIVEKIT_URL` | Yes (prod) | LiveKit Cloud WebSocket URL |
| `LIVEKIT_API_KEY` | Yes (prod) | LiveKit API key |
| `LIVEKIT_API_SECRET` | Yes (prod) | LiveKit API secret |
| `OPENAI_API_KEY` | Yes (prod) | OpenAI key for LLM + summaries |
| `OPENAI_MODEL` | No | Defaults to `gpt-4o-mini` |
| `DEEPGRAM_API_KEY` | Yes (prod) | Deepgram key for STT |
| `CARTESIA_API_KEY` | Yes (prod) | Cartesia key for TTS |
| `APP_ENV` | No | `development` / `production` |
| `DEFAULT_TIMEZONE` | No | Defaults to `Asia/Kolkata` |

## Docker (Local)

Runs the API and agent worker as separate containers sharing the same image:

```bash
docker compose up --build
```

API → `http://localhost:8000`

## Deployment — Railway

The project includes a `railway.toml` pre-configured for Railway deployment.

### 1. Deploy the API service

1. Push this repo to GitHub
2. Railway → **New Project** → **Deploy from GitHub repo** → select this repo
3. Railway picks up `railway.toml` and builds the `Dockerfile` automatically
4. Add **PostgreSQL** plugin: **+ New** → **Database** → **PostgreSQL** (injects `DATABASE_URL` automatically)
5. Set environment variables in the service **Variables** tab (see table above)
6. Railway generates a public URL — test with:
   ```
   curl https://your-app.up.railway.app/health
   ```

### 2. Deploy the Worker service

1. In the same Railway project, click **+ New** → **GitHub Repo** → select this repo again
2. Go to the new service → **Settings** → set **Custom Start Command**:
   ```
   python -m app.agent.worker start
   ```
3. Add the same environment variables as the API service
4. Deploy

## API Overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check and provider status |
| POST | `/api/v1/sessions` | Create a new voice session + LiveKit room |
| POST | `/api/v1/sessions/{id}/end` | End session and generate summary |
| GET | `/api/v1/sessions/{id}/events` | Stream conversation events |
| GET | `/api/v1/sessions/{id}/summary` | Retrieve call summary |

## Tests

```bash
pytest
```
