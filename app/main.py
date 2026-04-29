from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.db.session import create_db_and_tables
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Mykare Voice Agent Backend",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.state.settings = settings
    register_exception_handlers(app)
    app.include_router(api_router)

    return app


app = create_app()
