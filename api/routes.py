"""
Aggregator for all API Endpoints.
"""
from fastapi import APIRouter

from api.endpoints import upload, chat, dashboard
from api.schemas import HealthResponse
from core.config import settings
from core.session import session_store

router = APIRouter()

router.include_router(upload.router, tags=["Upload"])
router.include_router(chat.router, tags=["Chat"])
router.include_router(dashboard.router, tags=["Dashboard"])

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Returns system health and active sessions."""
    return HealthResponse(
        status="healthy",
        model=settings.MODEL_NAME,
        active_sessions=len(session_store.sessions),
        version="1.0.0"
    )
