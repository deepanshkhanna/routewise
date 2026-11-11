"""Persisted network topology APIs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.network import (
    EventOut,
    LinkCreate,
    LinkOut,
    NetworkCreate,
    NetworkOut,
    NetworkSummary,
    RouterCreate,
    RouterOut,
    StaticRouteCreate,
    StaticRouteOut,
)
from app.services.network_service import NetworkService

router = APIRouter(tags=["networks"])


@router.get("/api/networks", response_model=list[NetworkSummary])
def list_networks(db: Session = Depends(get_db)) -> list[NetworkSummary]:
    return NetworkService(db).list_networks()


@router.post("/api/networks", response_model=NetworkOut, status_code=201)
def create_network(payload: NetworkCreate, db: Session = Depends(get_db)) -> NetworkOut:
    try:
        network = NetworkService(db).create_network(payload)
        return NetworkService(db).to_out(network)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/networks/{network_id}", response_model=NetworkOut)
def get_network(network_id: int, db: Session = Depends(get_db)) -> NetworkOut:
    try:
        network = NetworkService(db).get_network(network_id)
        return NetworkService(db).to_out(network)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/api/networks/{network_id}", status_code=204)
def delete_network(network_id: int, db: Session = Depends(get_db)) -> None:
    try:
        NetworkService(db).delete_network(network_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/networks/{network_id}/routers", response_model=RouterOut, status_code=201)
def add_router(
    network_id: int,
    payload: RouterCreate,
    db: Session = Depends(get_db),
) -> RouterOut:
    try:
        return RouterOut.model_validate(NetworkService(db).add_router(network_id, payload))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/networks/{network_id}/links", response_model=LinkOut, status_code=201)
def add_link(
    network_id: int,
    payload: LinkCreate,
    db: Session = Depends(get_db),
) -> LinkOut:
    try:
        return LinkOut.model_validate(NetworkService(db).add_link(network_id, payload))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/networks/{network_id}/events", response_model=list[EventOut])
def list_events(network_id: int, db: Session = Depends(get_db)) -> list[EventOut]:
    try:
        events = NetworkService(db).list_events(network_id)
        return [EventOut.model_validate(e) for e in events]
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/api/networks/{network_id}/static-routes",
    response_model=StaticRouteOut,
    status_code=201,
)
def add_static_route(
    network_id: int,
    payload: StaticRouteCreate,
    db: Session = Depends(get_db),
) -> StaticRouteOut:
    try:
        route = NetworkService(db).add_static_route(network_id, payload)
        return StaticRouteOut.model_validate(route)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/networks/{network_id}/static-routes", response_model=list[StaticRouteOut])
def list_static_routes(network_id: int, db: Session = Depends(get_db)) -> list[StaticRouteOut]:
    try:
        routes = NetworkService(db).list_static_routes(network_id)
        return [StaticRouteOut.model_validate(r) for r in routes]
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/networks/seed-default", response_model=NetworkOut)
def seed_default(db: Session = Depends(get_db)) -> NetworkOut:
    network = NetworkService(db).seed_default_triangle()
    return NetworkService(db).to_out(network)
