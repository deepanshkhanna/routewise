"""Dashboard aggregate endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import Event, Link, Network, Router
from app.db.session import get_db
from app.schemas.network import DashboardOverview, EventOut
from app.services.network_service import NetworkService
from app.services.routing_service import RoutingService

router = APIRouter(tags=["dashboard"])


@router.get("/api/dashboard/overview", response_model=DashboardOverview)
def overview(db: Session = Depends(get_db)) -> DashboardOverview:
    NetworkService(db).seed_default_triangle()

    networks = db.query(Network).count()
    routers = db.query(Router).all()
    links = db.query(Link).all()
    active_routers = sum(1 for r in routers if r.status == "up")
    active_links = sum(1 for link in links if link.enabled and link.status == "up")
    failed_links = len(links) - active_links
    events = db.query(Event).order_by(Event.id.desc()).limit(8).all()

    lab = RoutingService().lab_status()
    default = db.query(Network).order_by(Network.id.asc()).first()

    return DashboardOverview(
        data_source="software_simulation",
        networks=networks,
        total_routers=len(routers),
        active_routers=active_routers,
        total_links=len(links),
        active_links=active_links,
        failed_links=failed_links,
        lab_running=lab.running,
        recent_events=[EventOut.model_validate(e) for e in events],
        default_network_id=default.id if default else None,
        message=(
            "Overview metrics come from the SQLite software-simulation topology. "
            f"ContainerLab FRR lab running={lab.running}."
        ),
    )
