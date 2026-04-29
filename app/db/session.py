from collections.abc import Generator

from app.core.config import get_settings
from app.db.base import Base
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker


settings = get_settings()

if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False, "timeout": 30}
else:
    connect_args = {}

engine = create_engine(
    settings.database_url,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args,
)

# Enable WAL mode for SQLite — allows concurrent reads from worker + FastAPI
if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_wal_mode(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_and_tables() -> None:
    from app.models import appointment, conversation, user  # noqa: F401

    Base.metadata.create_all(bind=engine)
