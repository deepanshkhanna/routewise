"""Network topology persistence and seeding."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session, joinedload

from app.db.models import Event, Link, Network, Router, StaticRoute
from app.schemas.network import (
    LinkCreate,
    NetworkCreate,
    NetworkOut,
    NetworkSummary,
    RouterCreate,
    StaticRouteCreate,
)

logger = logging.getLogger(__name__)

DEFAULT_NETWORK_NAME = "RouteWise Triangle Lab"


class NetworkService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def seed_default_triangle(self) -> Network:
        existing = (
            self.db.query(Network).filter(Network.name == DEFAULT_NETWORK_NAME).first()
        )
        if existing:
            return existing

        network = Network(
            name=DEFAULT_NETWORK_NAME,
            description=(
                "Default three-router OSPF triangle matching lab/routewise.clab.yml. "
                "Managed via software_simulation until ContainerLab is deployed."
            ),
        )
        self.db.add(network)
        self.db.flush()

        routers = [
            Router(
                network_id=network.id,
                name="R1",
                loopback="192.168.1.1/32",
                router_id="1.1.1.1",
                protocol="OSPF",
            ),
            Router(
                network_id=network.id,
                name="R2",
                loopback="192.168.2.2/32",
                router_id="2.2.2.2",
                protocol="OSPF",
            ),
            Router(
                network_id=network.id,
                name="R3",
                loopback="192.168.3.3/32",
                router_id="3.3.3.3",
                protocol="OSPF",
            ),
        ]
        self.db.add_all(routers)

        # Asymmetric latency so optimization can prefer R1-R3 direct vs via R2.
        links = [
            Link(
                network_id=network.id,
                name="R1-R2",
                source_router="R1",
                target_router="R2",
                subnet="10.0.12.0/30",
                source_ip="10.0.12.1/30",
                target_ip="10.0.12.2/30",
                cost=10,
                latency_ms=8,
                packet_loss_pct=0.5,
            ),
            Link(
                network_id=network.id,
                name="R2-R3",
                source_router="R2",
                target_router="R3",
                subnet="10.0.23.0/30",
                source_ip="10.0.23.1/30",
                target_ip="10.0.23.2/30",
                cost=10,
                latency_ms=9,
                packet_loss_pct=1.0,
            ),
            Link(
                network_id=network.id,
                name="R1-R3",
                source_router="R1",
                target_router="R3",
                subnet="10.0.13.0/30",
                source_ip="10.0.13.1/30",
                target_ip="10.0.13.2/30",
                cost=15,
                latency_ms=4,
                packet_loss_pct=0.0,
            ),
        ]
        self.db.add_all(links)
        self.db.add(
            Event(
                network_id=network.id,
                severity="info",
                category="system",
                description="Default triangle topology seeded (software_simulation).",
                data_source="software_simulation",
            )
        )
        self.db.commit()
        logger.info("Seeded default network id=%s", network.id)
        return self.get_network(network.id)

    def list_networks(self) -> list[NetworkSummary]:
        networks = self.db.query(Network).all()
        summaries: list[NetworkSummary] = []
        for net in networks:
            links = self.db.query(Link).filter(Link.network_id == net.id).all()
            routers = self.db.query(Router).filter(Router.network_id == net.id).all()
            active = sum(1 for link in links if link.enabled and link.status == "up")
            failed = len(links) - active
            summaries.append(
                NetworkSummary(
                    id=net.id,
                    name=net.name,
                    description=net.description,
                    router_count=len(routers),
                    link_count=len(links),
                    active_links=active,
                    failed_links=failed,
                )
            )
        return summaries

    def get_network(self, network_id: int) -> Network:
        network = (
            self.db.query(Network)
            .options(joinedload(Network.routers), joinedload(Network.links))
            .filter(Network.id == network_id)
            .first()
        )
        if not network:
            raise LookupError(f"Network {network_id} not found")
        return network

    def create_network(self, payload: NetworkCreate) -> Network:
        network = Network(name=payload.name, description=payload.description)
        self.db.add(network)
        self.db.commit()
        self.db.refresh(network)
        self._event(network.id, "info", "topology", f"Network '{network.name}' created.")
        return self.get_network(network.id)

    def delete_network(self, network_id: int) -> None:
        network = self.get_network(network_id)
        self.db.delete(network)
        self.db.commit()

    def add_router(self, network_id: int, payload: RouterCreate) -> Router:
        self.get_network(network_id)
        router = Router(network_id=network_id, **payload.model_dump())
        self.db.add(router)
        self.db.commit()
        self.db.refresh(router)
        self._event(network_id, "info", "topology", f"Router {router.name} added.")
        return router

    def add_link(self, network_id: int, payload: LinkCreate) -> Link:
        network = self.get_network(network_id)
        names = {r.name for r in network.routers}
        if payload.source_router not in names or payload.target_router not in names:
            raise ValueError("Link endpoints must reference existing routers in the network")
        if payload.source_router == payload.target_router:
            raise ValueError("Link source and target must differ")
        link = Link(network_id=network_id, **payload.model_dump())
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        self._event(
            network_id,
            "info",
            "topology",
            f"Link {link.source_router}-{link.target_router} added.",
        )
        return link

    def add_static_route(self, network_id: int, payload: StaticRouteCreate) -> StaticRoute:
        network = self.get_network(network_id)
        names = {r.name for r in network.routers}
        if payload.router_name not in names:
            raise ValueError("Static route router_name must exist in the network")
        route = StaticRoute(network_id=network_id, **payload.model_dump())
        self.db.add(route)
        self.db.commit()
        self.db.refresh(route)
        self._event(
            network_id,
            "info",
            "routing",
            f"Static route on {route.router_name}: {route.destination} via {route.next_hop}",
        )
        return route

    def list_static_routes(self, network_id: int) -> list[StaticRoute]:
        self.get_network(network_id)
        return (
            self.db.query(StaticRoute)
            .filter(StaticRoute.network_id == network_id)
            .order_by(StaticRoute.id.asc())
            .all()
        )

    def list_events(self, network_id: int, limit: int = 50) -> list[Event]:
        self.get_network(network_id)
        return (
            self.db.query(Event)
            .filter(Event.network_id == network_id)
            .order_by(Event.id.desc())
            .limit(limit)
            .all()
        )

    def to_out(self, network: Network) -> NetworkOut:
        return NetworkOut.model_validate(network)

    def _event(self, network_id: int, severity: str, category: str, description: str) -> Event:
        event = Event(
            network_id=network_id,
            severity=severity,
            category=category,
            description=description,
            data_source="software_simulation",
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
