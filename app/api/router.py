from app.api.routes import health, sessions, tools
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
api_router.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])
