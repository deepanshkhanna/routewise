"""Path exploration, optimization, simulation, and diagnostics APIs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.network import (
    DiagnosticsRequest,
    DiagnosticsResponse,
    OptimizeResponse,
    PathExploreResponse,
    SimulationResult,
)
from app.services.network_service import NetworkService
from app.services.optimizer import recommend
from app.services.path_engine import PathEngine
from app.services.simulation_service import SimulationService

router = APIRouter(tags=["analysis"])


@router.get("/api/networks/{network_id}/paths", response_model=PathExploreResponse)
def explore_paths(
    network_id: int,
    source: str = Query(...),
    destination: str = Query(...),
    db: Session = Depends(get_db),
) -> PathExploreResponse:
    try:
        network = NetworkService(db).get_network(network_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    engine = PathEngine(network.routers, network.links)
    candidates = engine.all_simple_paths(source.upper(), destination.upper())
    selected = engine.lowest_cost_path(source.upper(), destination.upper())
    return PathExploreResponse(
        network_id=network_id,
        source=source.upper(),
        destination=destination.upper(),
        protocol_selected_path=selected,
        candidate_paths=candidates,
        message=(
            "Paths computed from persisted topology (software_simulation). "
            "Not FRR FIB data."
        ),
    )


@router.get("/api/networks/{network_id}/optimize", response_model=OptimizeResponse)
def optimize_path(
    network_id: int,
    source: str = Query(...),
    destination: str = Query(...),
    db: Session = Depends(get_db),
) -> OptimizeResponse:
    try:
        network = NetworkService(db).get_network(network_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    engine = PathEngine(network.routers, network.links)
    src, dst = source.upper(), destination.upper()
    candidates = engine.all_simple_paths(src, dst)
    selected = engine.lowest_cost_path(src, dst)
    return recommend(network_id, src, dst, candidates, selected)


@router.post(
    "/api/networks/{network_id}/simulate/links/{link_id}/disable",
    response_model=SimulationResult,
)
def disable_link(
    network_id: int,
    link_id: int,
    db: Session = Depends(get_db),
) -> SimulationResult:
    try:
        return SimulationService(db).set_link_state(network_id, link_id, enabled=False)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/api/networks/{network_id}/simulate/links/{link_id}/enable",
    response_model=SimulationResult,
)
def enable_link(
    network_id: int,
    link_id: int,
    db: Session = Depends(get_db),
) -> SimulationResult:
    try:
        return SimulationService(db).set_link_state(network_id, link_id, enabled=True)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/api/networks/{network_id}/simulate/routers/{router_name}/fail",
    response_model=SimulationResult,
)
def fail_router(
    network_id: int,
    router_name: str,
    db: Session = Depends(get_db),
) -> SimulationResult:
    try:
        return SimulationService(db).set_router_state(network_id, router_name.upper(), up=False)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/api/networks/{network_id}/simulate/routers/{router_name}/restore",
    response_model=SimulationResult,
)
def restore_router(
    network_id: int,
    router_name: str,
    db: Session = Depends(get_db),
) -> SimulationResult:
    try:
        return SimulationService(db).set_router_state(network_id, router_name.upper(), up=True)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/api/networks/{network_id}/diagnostics/ping",
    response_model=DiagnosticsResponse,
)
def ping(
    network_id: int,
    payload: DiagnosticsRequest,
    db: Session = Depends(get_db),
) -> DiagnosticsResponse:
    try:
        return SimulationService(db).ping(
            network_id,
            payload.source.upper(),
            payload.destination.upper(),
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/api/networks/{network_id}/diagnostics/traceroute",
    response_model=DiagnosticsResponse,
)
def traceroute(
    network_id: int,
    payload: DiagnosticsRequest,
    db: Session = Depends(get_db),
) -> DiagnosticsResponse:
    try:
        return SimulationService(db).traceroute(
            network_id,
            payload.source.upper(),
            payload.destination.upper(),
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
