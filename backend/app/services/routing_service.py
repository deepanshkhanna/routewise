"""High-level routing lab queries built on DockerService."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.config import (
    ALLOWED_ROUTER_IDS,
    ROUTER_INVENTORY,
    TOPOLOGY_LINKS,
    get_settings,
)
from app.schemas.router import (
    LabStatusResponse,
    OspfNeighbor,
    OspfNeighborsResponse,
    ProtocolReadinessResponse,
    ProtocolStatusItem,
    RouteEntry,
    RouterContainerStatus,
    RouterInfo,
    RouterRoutesResponse,
    RoutersListResponse,
    TopologyLink,
    TopologyNode,
    TopologyResponse,
)
from app.services.docker_service import ContainerState, DockerErrorKind, DockerService
from app.services.providers.factory import probe_infrastructure

logger = logging.getLogger(__name__)

SHOW_IP_ROUTE_JSON = "show ip route json"
SHOW_IP_ROUTE = "show ip route"
SHOW_OSPF_NEIGHBOR_JSON = "show ip ospf neighbor json"
SHOW_OSPF_NEIGHBOR = "show ip ospf neighbor"
SHOW_IP_RIP = "show ip rip"
SHOW_IP_RIP_STATUS = "show ip rip status"


class RoutingService:
    """Orchestrate lab status and read-only router inspection."""

    def __init__(self, docker: DockerService | None = None) -> None:
        self.settings = get_settings()
        self.docker = docker or DockerService(self.settings)

    def validate_router_id(self, router_id: str) -> str:
        rid = router_id.upper()
        if rid not in ALLOWED_ROUTER_IDS:
            raise ValueError(
                f"Router id must be one of: {', '.join(sorted(ALLOWED_ROUTER_IDS))}"
            )
        return rid

    def lab_status(self) -> LabStatusResponse:
        expected = sorted(ALLOWED_ROUTER_IDS)
        docker_info = self.docker.docker_available()
        if not docker_info.ok:
            overall: str
            if docker_info.error_kind == DockerErrorKind.CLI_MISSING:
                overall = "unavailable"
            elif docker_info.error_kind == DockerErrorKind.TIMEOUT:
                overall = "unknown"
            else:
                overall = "unavailable"
            return LabStatusResponse(
                lab_name=self.settings.lab_name,
                status=overall,  # type: ignore[arg-type]
                running=False,
                expected_routers=expected,
                containers_found=[],
                routers=[
                    RouterContainerStatus(
                        router_id=rid,
                        container_name=self.docker.container_name(rid),
                        status="unknown",
                    )
                    for rid in expected
                ],
                docker_ok=False,
                message=docker_info.error or "Docker is unavailable",
            )

        router_states: list[RouterContainerStatus] = []
        found_running: list[str] = []
        for rid in expected:
            name = self.docker.container_name(rid)
            state, _probe = self.docker.inspect_container_state(name)
            router_states.append(
                RouterContainerStatus(
                    router_id=rid,
                    container_name=name,
                    status=state,
                )
            )
            if state == "running":
                found_running.append(name)

        states = {item.status for item in router_states}
        if states == {"running"}:
            overall_status = "running"
            message = "RouteWise Docker lab is running."
        elif "unknown" in states and not (states & {"running", "stopped"}):
            overall_status = "unknown"
            message = "Unable to determine lab status from Docker."
        elif states <= {"unavailable"}:
            overall_status = "unavailable"
            message = "Docker lab containers were not found. Deploy the lab to continue."
        elif "running" in states:
            overall_status = "stopped"
            message = "Partial lab containers found; topology may be incomplete."
        else:
            overall_status = "stopped"
            message = "Lab containers exist but are not running."

        return LabStatusResponse(
            lab_name=self.settings.lab_name,
            status=overall_status,  # type: ignore[arg-type]
            running=overall_status == "running",
            expected_routers=expected,
            containers_found=found_running,
            routers=router_states,
            docker_ok=True,
            message=message,
        )

    def list_routers(self) -> RoutersListResponse:
        status = self.lab_status()
        status_by_id = {item.router_id: item.status for item in status.routers}
        routers: list[RouterInfo] = []
        for rid, meta in ROUTER_INVENTORY.items():
            container = self.docker.container_name(rid)
            state = status_by_id.get(rid, "unknown")
            available = state == "running"
            routers.append(
                RouterInfo(
                    id=rid,
                    container_name=container,
                    loopback=meta["loopback"],
                    protocol=meta["protocol"],
                    available=available,
                    status=state,
                )
            )
        return RoutersListResponse(
            lab_running=status.running,
            routers=routers,
            message=status.message,
        )

    def get_topology(self) -> TopologyResponse:
        """Configured topology only — not live router reachability."""
        nodes = [
            TopologyNode(id=rid, label=rid, loopback=meta["loopback"])
            for rid, meta in ROUTER_INVENTORY.items()
        ]
        links = [TopologyLink(**link) for link in TOPOLOGY_LINKS]  # type: ignore[arg-type]
        return TopologyResponse(
            name="routewise-triangle",
            protocol="OSPF",
            area="0",
            nodes=nodes,
            links=links,
        )

    def get_routes(self, router_id: str) -> RouterRoutesResponse:
        rid = self.validate_router_id(router_id)
        container = self.docker.container_name(rid)
        gate = self._gate_router_access(rid, container, resource="routes")
        if gate is not None:
            return gate  # type: ignore[return-value]

        json_result = self.docker.vtysh_show(container, SHOW_IP_ROUTE_JSON)
        if json_result.ok and json_result.stdout:
            parsed = self._parse_routes_json(json_result.stdout)
            if parsed is not None:
                return RouterRoutesResponse(
                    router_id=rid,
                    available=True,
                    status="online",
                    routes=parsed,
                    raw_output=json_result.stdout,
                    message="Routing table retrieved.",
                )

        text_result = self.docker.vtysh_show(container, SHOW_IP_ROUTE)
        if not text_result.ok:
            failed = text_result if text_result.error_kind != DockerErrorKind.NONE else json_result
            error_code, message = self._map_exec_failure(failed)
            logger.warning("Failed to read routes for %s: %s", rid, message)
            return RouterRoutesResponse(
                router_id=rid,
                available=False,
                status="error",
                routes=[],
                raw_output="",
                message=message,
                error_code=error_code,
            )

        routes = self._parse_routes_text(text_result.stdout)
        return RouterRoutesResponse(
            router_id=rid,
            available=True,
            status="online",
            routes=routes,
            raw_output=text_result.stdout,
            message="Routing table retrieved.",
        )

    def protocol_readiness(self) -> ProtocolReadinessResponse:
        """Probe Static / RIP / OSPF / BGP readiness for the Routing Manager UI."""
        infra = probe_infrastructure()
        mode = infra.get("active_mode", "SOFTWARE_SIMULATION")
        lab_deployed = bool(infra.get("real_lab", {}).get("lab_deployed"))

        static = ProtocolStatusItem(
            id="static",
            name="Static",
            state="operational",
            badge="ok",
            label="Operational (DB)",
            source="software_simulation",
            detail="Static routes persisted in SQLite.",
        )
        bgp = ProtocolStatusItem(
            id="bgp",
            name="BGP",
            state="planned",
            badge="muted",
            label="Future extension",
            source="unavailable",
            detail="bgpd disabled in lab daemons.",
        )

        if not lab_deployed:
            ospf = ProtocolStatusItem(
                id="ospf",
                name="OSPF",
                state="unavailable",
                badge="warn",
                label="Lab not deployed",
                source="unavailable",
                detail="Deploy ContainerLab to activate OSPF.",
            )
            rip = ProtocolStatusItem(
                id="rip",
                name="RIP v2",
                state="unavailable",
                badge="warn",
                label="Lab not deployed",
                source="unavailable",
                detail="Deploy ContainerLab to activate RIP v2.",
            )
            return ProtocolReadinessResponse(
                mode=mode,
                lab_deployed=False,
                protocols=[static, rip, ospf, bgp],
                message="REAL_LAB required for RIP/OSPF operational status.",
            )

        ospf_payload = self.get_ospf_neighbors("R1")
        full_neighbors = [
            n
            for n in ospf_payload.neighbors
            if "full" in (n.state or "").lower() or "full" in (n.raw or "").lower()
        ]
        if not full_neighbors and ospf_payload.raw_output:
            # Fallback: count Full adjacency lines from raw vtysh text/json.
            full_count = sum(
                1
                for ln in ospf_payload.raw_output.splitlines()
                if re.search(r"\bFull\b", ln, flags=re.IGNORECASE)
            )
            if full_count:
                full_neighbors = [OspfNeighbor(local_router="R1", state="Full")] * full_count
        if ospf_payload.available and full_neighbors:
            ospf = ProtocolStatusItem(
                id="ospf",
                name="OSPF",
                state="operational",
                badge="ok",
                label=f"Operational (FRR · {len(full_neighbors)} Full)",
                source="real_lab",
                detail=f"R1 OSPF Full neighbors: {len(full_neighbors)}",
            )
        elif ospf_payload.available and ospf_payload.neighbors:
            ospf = ProtocolStatusItem(
                id="ospf",
                name="OSPF",
                state="degraded",
                badge="warn",
                label="Converging",
                source="real_lab",
                detail="Neighbors present but not all Full yet.",
            )
        else:
            ospf = ProtocolStatusItem(
                id="ospf",
                name="OSPF",
                state="degraded",
                badge="warn",
                label="Daemon up, no neighbors",
                source="real_lab",
                detail=ospf_payload.message or "No OSPF neighbors on R1.",
            )

        rip = self._probe_rip_status()
        return ProtocolReadinessResponse(
            mode=mode,
            lab_deployed=True,
            protocols=[static, rip, ospf, bgp],
            message="Protocol status from live FRR inspection where available.",
        )

    def _probe_rip_status(self) -> ProtocolStatusItem:
        container = self.docker.container_name("R1")
        state, _ = self.docker.inspect_container_state(container)
        if state != "running":
            return ProtocolStatusItem(
                id="rip",
                name="RIP v2",
                state="unavailable",
                badge="warn",
                label="Router offline",
                source="unavailable",
                detail="R1 container not running.",
            )

        status = self.docker.vtysh_show(container, SHOW_IP_RIP_STATUS)
        table = self.docker.vtysh_show(container, SHOW_IP_RIP)
        combined = f"{status.stdout}\n{table.stdout}".lower()

        if not status.ok and not table.ok:
            return ProtocolStatusItem(
                id="rip",
                name="RIP v2",
                state="unavailable",
                badge="warn",
                label="ripd not responding",
                source="real_lab",
                detail=status.error or table.error or "show ip rip failed",
            )

        # ripd operational when status/table returns without "not running"
        if "not running" in combined or "is not running" in combined:
            return ProtocolStatusItem(
                id="rip",
                name="RIP v2",
                state="unavailable",
                badge="warn",
                label="ripd not running",
                source="real_lab",
                detail="Enable ripd in lab daemons and redeploy.",
            )

        route_lines = [
            ln
            for ln in (table.stdout or "").splitlines()
            if ln.strip() and not ln.strip().lower().startswith(("codes:", "status"))
        ]
        if "version 2" in combined or "rip" in combined or route_lines:
            detail = (
                f"RIP table lines={len(route_lines)}"
                if route_lines
                else "ripd responding (RIPv2 configured)."
            )
            return ProtocolStatusItem(
                id="rip",
                name="RIP v2",
                state="operational",
                badge="ok",
                label="Operational (FRR)",
                source="real_lab",
                detail=detail,
            )

        return ProtocolStatusItem(
            id="rip",
            name="RIP v2",
            state="degraded",
            badge="warn",
            label="Configured, empty table",
            source="real_lab",
            detail="ripd up but no RIP routes learned yet.",
        )

    def get_ospf_neighbors(self, router_id: str) -> OspfNeighborsResponse:
        rid = self.validate_router_id(router_id)
        container = self.docker.container_name(rid)
        gate = self._gate_router_access(rid, container, resource="ospf")
        if gate is not None:
            return gate  # type: ignore[return-value]

        json_result = self.docker.vtysh_show(container, SHOW_OSPF_NEIGHBOR_JSON)
        if json_result.ok and json_result.stdout:
            parsed = self._parse_ospf_json(rid, json_result.stdout)
            # Empty neighbor dict is not success — fall through to text parse.
            if parsed:
                return OspfNeighborsResponse(
                    router_id=rid,
                    available=True,
                    status="online",
                    neighbors=parsed,
                    raw_output=json_result.stdout,
                    message="OSPF neighbor table retrieved.",
                )

        text_result = self.docker.vtysh_show(container, SHOW_OSPF_NEIGHBOR)
        if not text_result.ok:
            failed = text_result if text_result.error_kind != DockerErrorKind.NONE else json_result
            error_code, message = self._map_exec_failure(failed)
            logger.warning("Failed to read OSPF neighbors for %s: %s", rid, message)
            return OspfNeighborsResponse(
                router_id=rid,
                available=False,
                status="error",
                neighbors=[],
                raw_output="",
                message=message,
                error_code=error_code,
            )

        neighbors = self._parse_ospf_text(rid, text_result.stdout)
        return OspfNeighborsResponse(
            router_id=rid,
            available=True,
            status="online",
            neighbors=neighbors,
            raw_output=text_result.stdout,
            message="OSPF neighbor table retrieved.",
        )

    def _gate_router_access(
        self,
        rid: str,
        container: str,
        resource: str,
    ) -> RouterRoutesResponse | OspfNeighborsResponse | None:
        state, probe = self.docker.inspect_container_state(container)
        if state == "running":
            return None

        error_code, message = self._map_state_to_error(state, probe.error_kind, resource)
        common = {
            "router_id": rid,
            "available": False,
            "status": state,
            "raw_output": "",
            "message": message,
            "error_code": error_code,
        }
        if resource == "routes":
            return RouterRoutesResponse(routes=[], **common)
        return OspfNeighborsResponse(neighbors=[], **common)

    @staticmethod
    def _map_state_to_error(
        state: ContainerState,
        kind: DockerErrorKind,
        resource: str,
    ) -> tuple[str, str]:
        noun = "routing table" if resource == "routes" else "OSPF neighbors"
        if kind == DockerErrorKind.CLI_MISSING:
            return "docker_cli_missing", f"Docker CLI is unavailable; cannot read {noun}."
        if kind == DockerErrorKind.DAEMON_UNAVAILABLE:
            return "docker_daemon_unavailable", f"Docker daemon is unreachable; cannot read {noun}."
        if kind == DockerErrorKind.TIMEOUT:
            return "docker_timeout", f"Docker timed out while checking router for {noun}."
        if state == "stopped":
            return "router_stopped", f"Router container is stopped; cannot read {noun}."
        if state == "unavailable":
            return "router_not_found", f"Router container was not found; deploy the lab to read {noun}."
        return "router_unknown", f"Router state is unknown; cannot read {noun}."

    @staticmethod
    def _map_exec_failure(result: Any) -> tuple[str, str]:
        kind = getattr(result, "error_kind", DockerErrorKind.EXEC_FAILED)
        if kind == DockerErrorKind.TIMEOUT:
            return "docker_timeout", "FRR inspection command timed out."
        if kind == DockerErrorKind.NOT_FOUND:
            return "router_not_found", "Router container was not found."
        if kind == DockerErrorKind.DAEMON_UNAVAILABLE:
            return "docker_daemon_unavailable", "Docker daemon is unreachable."
        if kind == DockerErrorKind.CLI_MISSING:
            return "docker_cli_missing", "Docker CLI is unavailable."
        if kind == DockerErrorKind.REJECTED:
            return "command_rejected", "Inspection command was rejected."
        return "frr_command_failed", "Failed to execute FRR inspection command."

    @staticmethod
    def http_status_for_error(error_code: str | None) -> int:
        mapping = {
            "docker_cli_missing": 503,
            "docker_daemon_unavailable": 503,
            "docker_timeout": 504,
            "router_not_found": 404,
            "router_stopped": 409,
            "router_unknown": 503,
            "frr_command_failed": 502,
            "command_rejected": 400,
        }
        return mapping.get(error_code or "", 200)

    @staticmethod
    def _parse_routes_json(raw: str) -> list[RouteEntry] | None:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            logger.info("Route JSON parse failed; falling back to text")
            return None

        entries: list[RouteEntry] = []
        if isinstance(payload, dict):
            for destination, value in payload.items():
                nexthops = value if isinstance(value, list) else [value]
                for item in nexthops:
                    if not isinstance(item, dict):
                        continue
                    nh = ""
                    nh_list = item.get("nexthops")
                    if isinstance(nh_list, list) and nh_list and isinstance(nh_list[0], dict):
                        nh = str(nh_list[0].get("ip", "") or "")
                    elif item.get("nexthop"):
                        nh = str(item.get("nexthop"))
                    entries.append(
                        RouteEntry(
                            destination=str(destination),
                            nexthop=nh,
                            protocol=str(item.get("protocol", item.get("type", ""))),
                            metric=str(item.get("metric", "")),
                            raw=json.dumps(item),
                        )
                    )
        elif isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    entries.append(
                        RouteEntry(
                            destination=str(item.get("prefix", item.get("destination", ""))),
                            nexthop=str(item.get("nexthop", "")),
                            protocol=str(item.get("protocol", "")),
                            metric=str(item.get("metric", "")),
                            raw=json.dumps(item),
                        )
                    )
        else:
            return None
        return entries

    @staticmethod
    def _parse_routes_text(raw: str) -> list[RouteEntry]:
        entries: list[RouteEntry] = []
        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("Codes:") or stripped.startswith("Gateway"):
                continue
            parts = stripped.split()
            destination = parts[1] if len(parts) > 1 else ""
            protocol = parts[0] if parts else ""
            nexthop = ""
            via_match = re.search(r"via\s+(\S+)", stripped)
            if via_match:
                nexthop = via_match.group(1)
            entries.append(
                RouteEntry(
                    destination=destination,
                    nexthop=nexthop,
                    protocol=protocol,
                    raw=stripped,
                )
            )
        return entries

    @staticmethod
    def _parse_ospf_json(local_router: str, raw: str) -> list[OspfNeighbor] | None:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return None

        neighbors: list[OspfNeighbor] = []

        def add_neighbor(item: dict[str, Any]) -> None:
            neighbors.append(
                OspfNeighbor(
                    local_router=local_router,
                    neighbor_id=str(item.get("neighborId", item.get("neighbor_id", ""))),
                    priority=str(item.get("priority", "")),
                    state=str(item.get("state", item.get("nbrState", ""))),
                    address=str(
                        item.get("ifaceAddress", item.get("address", item.get("ipAddress", "")))
                    ),
                    interface=str(item.get("ifaceName", item.get("interface", ""))),
                    raw=json.dumps(item),
                )
            )

        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    add_neighbor(item)
        elif isinstance(payload, dict):
            # FRR 10.x: {"neighbors": {"2.2.2.2": [{nbrState: Full/-, ...}], ...}}
            nested = payload.get("neighbors")
            if isinstance(nested, dict):
                for nbr_id, entries in nested.items():
                    if isinstance(entries, list):
                        for item in entries:
                            if isinstance(item, dict):
                                add_neighbor({**item, "neighborId": str(nbr_id)})
                    elif isinstance(entries, dict):
                        add_neighbor({**entries, "neighborId": str(nbr_id)})
            else:
                # Legacy: neighbors keyed by interface name.
                for key, value in payload.items():
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                if "interface" not in item and "ifaceName" not in item:
                                    item = {**item, "interface": key}
                                add_neighbor(item)
                    elif isinstance(value, dict):
                        add_neighbor({**value, "interface": value.get("interface", key)})
        else:
            return None
        return neighbors

    @staticmethod
    def _parse_ospf_text(local_router: str, raw: str) -> list[OspfNeighbor]:
        neighbors: list[OspfNeighbor] = []
        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped or "Neighbor ID" in stripped or stripped.startswith("OSPFv"):
                continue
            parts = stripped.split()
            if len(parts) < 5:
                neighbors.append(OspfNeighbor(local_router=local_router, raw=stripped))
                continue
            neighbors.append(
                OspfNeighbor(
                    local_router=local_router,
                    neighbor_id=parts[0],
                    priority=parts[1],
                    state=parts[2],
                    address=parts[3] if len(parts) > 3 else "",
                    interface=parts[-1],
                    raw=stripped,
                )
            )
        return neighbors
