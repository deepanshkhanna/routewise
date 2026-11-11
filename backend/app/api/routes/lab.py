"""Lab lifecycle and infrastructure status APIs."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.schemas.router import ProtocolReadinessResponse
from app.services.providers.factory import get_lab_provider, probe_infrastructure
from app.services.routing_service import RoutingService

router = APIRouter(tags=["lab"])


class LabActionResult(BaseModel):
    ok: bool
    mode: str
    message: str
    details: dict = {}


@router.get("/api/lab/infrastructure")
def infrastructure() -> dict:
    """Combined SOFTWARE_SIMULATION / REAL_LAB probe for Settings UI."""
    return probe_infrastructure()


@router.get("/api/lab/protocols", response_model=ProtocolReadinessResponse)
def protocol_readiness() -> ProtocolReadinessResponse:
    """Live Static / RIP / OSPF / BGP readiness for Routing Manager."""
    return RoutingService().protocol_readiness()


@router.get("/api/lab/inspect")
def inspect_lab() -> dict:
    provider = get_lab_provider()
    status = provider.status()
    return {
        "mode": status.mode.value,
        "docker_ok": status.docker_ok,
        "containerlab_ok": status.containerlab_ok,
        "lab_deployed": status.lab_deployed,
        "routers": status.routers,
        "message": status.message,
        "details": status.details,
    }


@router.post("/api/lab/deploy", response_model=LabActionResult)
def deploy_lab() -> LabActionResult:
    provider = get_lab_provider()
    status = provider.deploy()
    return LabActionResult(
        ok=status.lab_deployed,
        mode=status.mode.value,
        message=status.message,
        details=status.details,
    )


@router.post("/api/lab/destroy", response_model=LabActionResult)
def destroy_lab() -> LabActionResult:
    provider = get_lab_provider()
    status = provider.destroy()
    return LabActionResult(
        ok=not status.lab_deployed,
        mode=status.mode.value,
        message=status.message,
        details=status.details,
    )


@router.post("/api/lab/restart", response_model=LabActionResult)
def restart_lab() -> LabActionResult:
    provider = get_lab_provider()
    destroy = provider.destroy()
    status = provider.deploy()
    return LabActionResult(
        ok=status.lab_deployed,
        mode=status.mode.value,
        message=status.message,
        details={**destroy.details, **status.details},
    )
