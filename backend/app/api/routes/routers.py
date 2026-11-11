"""Router inventory and inspection endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.router import (
    ErrorResponse,
    OspfNeighborsResponse,
    RouterRoutesResponse,
    RoutersListResponse,
)
from app.services.routing_service import RoutingService

router = APIRouter(tags=["routers"])


@router.get(
    "/api/routers",
    response_model=RoutersListResponse,
    summary="List configured routers",
)
async def list_routers() -> RoutersListResponse:
    """Return R1–R3 inventory with live Docker availability."""
    service = RoutingService()
    return service.list_routers()


@router.get(
    "/api/routers/{router_id}/routes",
    response_model=RouterRoutesResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": RouterRoutesResponse},
        409: {"model": RouterRoutesResponse},
        502: {"model": RouterRoutesResponse},
        503: {"model": RouterRoutesResponse},
        504: {"model": RouterRoutesResponse},
    },
    summary="Read FRR routing table",
)
async def router_routes(router_id: str) -> RouterRoutesResponse | JSONResponse:
    """Return the routing table for an allow-listed router (R1|R2|R3)."""
    service = RoutingService()
    try:
        payload = service.get_routes(router_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"detail": str(exc), "error_code": "invalid_router_id"},
        ) from exc

    if payload.error_code:
        status = RoutingService.http_status_for_error(payload.error_code)
        return JSONResponse(status_code=status, content=payload.model_dump())
    return payload


@router.get(
    "/api/routers/{router_id}/ospf-neighbors",
    response_model=OspfNeighborsResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": OspfNeighborsResponse},
        409: {"model": OspfNeighborsResponse},
        502: {"model": OspfNeighborsResponse},
        503: {"model": OspfNeighborsResponse},
        504: {"model": OspfNeighborsResponse},
    },
    summary="Read FRR OSPF neighbors",
)
async def router_ospf_neighbors(router_id: str) -> OspfNeighborsResponse | JSONResponse:
    """Return OSPF neighbors for an allow-listed router (R1|R2|R3)."""
    service = RoutingService()
    try:
        payload = service.get_ospf_neighbors(router_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"detail": str(exc), "error_code": "invalid_router_id"},
        ) from exc

    if payload.error_code:
        status = RoutingService.http_status_for_error(payload.error_code)
        return JSONResponse(status_code=status, content=payload.model_dump())
    return payload
