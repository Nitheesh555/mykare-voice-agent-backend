from collections.abc import Generator

from app.core.config import get_settings
from app.db.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, future=True, pool_pre_ping=True, connect_args=connect_args)
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
