from app.db.session import get_db
from sqlalchemy.orm import Session


def db_dependency() -> Session:
    return next(get_db())
