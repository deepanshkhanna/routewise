"""Link/router failure simulation over persisted topology."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Event, Link, Router
from app.schemas.network import DiagnosticsResponse, SimulationResult
from app.services.network_service import NetworkService
from app.services.path_engine import PathEngine


class SimulationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.networks = NetworkService(db)

    def _active_link_count(self, network_id: int) -> int:
        links = self.db.query(Link).filter(Link.network_id == network_id).all()
        return sum(1 for link in links if link.enabled and link.status == "up")

    def set_link_state(self, network_id: int, link_id: int, enabled: bool) -> SimulationResult:
        self.networks.get_network(network_id)
        link = (
            self.db.query(Link)
            .filter(Link.id == link_id, Link.network_id == network_id)
            .first()
        )
        if not link:
            raise LookupError(f"Link {link_id} not found in network {network_id}")

        before = self._active_link_count(network_id)
        link.enabled = enabled
        link.status = "up" if enabled else "down"
        action = "enable_link" if enabled else "disable_link"
        desc = (
            f"Link {link.source_router}-{link.target_router} ({link.subnet}) "
            f"{'restored' if enabled else 'disabled'}."
        )
        event = Event(
            network_id=network_id,
            severity="warning" if not enabled else "info",
            category="simulation",
            description=desc,
            data_source="software_simulation",
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        after = self._active_link_count(network_id)
        return SimulationResult(
            network_id=network_id,
            action=action,
            target=f"link:{link_id}",
            before_active_links=before,
            after_active_links=after,
            message=desc,
            event_id=event.id,
        )

    def set_router_state(self, network_id: int, router_name: str, up: bool) -> SimulationResult:
        network = self.networks.get_network(network_id)
        router = next((r for r in network.routers if r.name == router_name), None)
        if not router:
            raise LookupError(f"Router {router_name} not found")
        before = self._active_link_count(network_id)
        router.status = "up" if up else "down"
        action = "restore_router" if up else "fail_router"
        desc = f"Router {router_name} marked {'up' if up else 'down'}."
        event = Event(
            network_id=network_id,
            severity="critical" if not up else "info",
            category="simulation",
            description=desc,
            data_source="software_simulation",
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        after = self._active_link_count(network_id)
        return SimulationResult(
            network_id=network_id,
            action=action,
            target=f"router:{router_name}",
            before_active_links=before,
            after_active_links=after,
            message=desc,
            event_id=event.id,
        )

    def ping(self, network_id: int, source: str, destination: str) -> DiagnosticsResponse:
        network = self.networks.get_network(network_id)
        engine = PathEngine(network.routers, network.links)
        path = engine.lowest_cost_path(source, destination)
        if source == destination:
            return DiagnosticsResponse(
                network_id=network_id,
                tool="ping",
                source=source,
                destination=destination,
                success=True,
                hops=[source],
                rtt_ms=0.1,
                message="Local ping succeeded (software_simulation).",
            )
        if not path:
            return DiagnosticsResponse(
                network_id=network_id,
                tool="ping",
                source=source,
                destination=destination,
                success=False,
                hops=[],
                rtt_ms=None,
                message="Destination unreachable under current topology (software_simulation).",
            )
        return DiagnosticsResponse(
            network_id=network_id,
            tool="ping",
            source=source,
            destination=destination,
            success=True,
            hops=path.hops,
            rtt_ms=round(path.total_latency_ms * 2, 2),
            message="Ping succeeded along lowest-cost available path (software_simulation).",
        )

    def traceroute(self, network_id: int, source: str, destination: str) -> DiagnosticsResponse:
        network = self.networks.get_network(network_id)
        engine = PathEngine(network.routers, network.links)
        path = engine.lowest_cost_path(source, destination)
        if not path:
            return DiagnosticsResponse(
                network_id=network_id,
                tool="traceroute",
                source=source,
                destination=destination,
                success=False,
                hops=[],
                rtt_ms=None,
                message="Traceroute failed — no available path (software_simulation).",
            )
        return DiagnosticsResponse(
            network_id=network_id,
            tool="traceroute",
            source=source,
            destination=destination,
            success=True,
            hops=path.hops,
            rtt_ms=round(path.total_latency_ms, 2),
            message="Traceroute follows protocol-selected lowest-cost path (software_simulation).",
        )
