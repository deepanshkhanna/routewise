"""Health and lab status endpoints."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.router import HealthResponse, LabStatusResponse
from app.services.routing_service import RoutingService

router = APIRouter(tags=["health"])


@router.get(
    "/api/health",
    response_model=HealthResponse,
    summary="Application health",
)
async def health() -> HealthResponse:
    """Return API liveness. Independent of Docker/lab state."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
    )


@router.get(
    "/api/lab/status",
    response_model=LabStatusResponse,
    summary="Docker lab status",
)
async def lab_status() -> LabStatusResponse:
    """Report whether R1–R3 ContainerLab containers are running."""
    service = RoutingService()
    return service.lab_status()
