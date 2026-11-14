"""ContainerLab / FRR provider — real lab operations when environment allows."""

from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import get_settings
from app.services.docker_service import DockerErrorKind, DockerService
from app.services.providers.base import ExecutionMode, LabStatus, NetworkProvider
from app.services.wsl_bridge import which_clab, run_argv

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[4]
LAB_DIR = PROJECT_ROOT / "lab"
TOPOLOGY_FILE = LAB_DIR / "routewise.clab.yml"


class ContainerLabProvider(NetworkProvider):
    name = "containerlab"
    mode = ExecutionMode.REAL_LAB

    def __init__(self) -> None:
        self.settings = get_settings()
        self.docker = DockerService(self.settings)

    def status(self) -> LabStatus:
        docker = self.docker.docker_available()
        clab = which_clab()
        routers: list[dict] = []
        deployed = False
        if docker.ok:
            for suffix, rid in (("r1", "R1"), ("r2", "R2"), ("r3", "R3")):
                name = f"clab-{self.settings.lab_name}-{suffix}"
                state, _probe = self.docker.inspect_container_state(name)
                routers.append(
                    {
                        "id": rid,
                        "container": name,
                        "status": state,
                    }
                )
            deployed = all(r["status"] == "running" for r in routers) and len(routers) == 3

        if not docker.ok:
            mode = ExecutionMode.UNAVAILABLE
            message = f"Docker unavailable: {docker.error}"
        elif not clab:
            mode = ExecutionMode.UNAVAILABLE
            message = "ContainerLab binary not found (install in WSL or PATH)."
        elif deployed:
            mode = ExecutionMode.REAL_LAB
            message = "RouteWise ContainerLab FRR lab is deployed and running."
        else:
            mode = ExecutionMode.UNAVAILABLE
            message = "ContainerLab available but routewise lab is not fully deployed."

        return LabStatus(
            mode=mode,
            docker_ok=docker.ok,
            containerlab_ok=bool(clab),
            lab_deployed=deployed,
            routers=routers,
            message=message,
            details={
                "topology_file": str(TOPOLOGY_FILE),
                "lab_name": self.settings.lab_name,
                "containerlab": clab,
                "docker_error_kind": (
                    docker.error_kind.value if not docker.ok else DockerErrorKind.NONE.value
                ),
            },
        )

    def deploy(self) -> LabStatus:
        status = self.status()
        if not status.docker_ok:
            status.mode = ExecutionMode.UNAVAILABLE
            status.message = "Cannot deploy: Docker daemon unreachable."
            return status
        if not status.containerlab_ok:
            status.mode = ExecutionMode.UNAVAILABLE
            status.message = "Cannot deploy: ContainerLab not installed."
            return status
        if not TOPOLOGY_FILE.exists():
            status.mode = ExecutionMode.UNAVAILABLE
            status.message = f"Topology missing: {TOPOLOGY_FILE}"
            return status

        clab = which_clab() or "clab"
        bridge = run_argv(
            [clab, "deploy", "-t", str(TOPOLOGY_FILE)],
            timeout=300,
            cwd=str(LAB_DIR),
        )
        logger.info(
            "containerlab deploy ok=%s via=%s out=%s err=%s",
            bridge.ok,
            bridge.via,
            bridge.stdout[:500],
            bridge.stderr[:500],
        )
        refreshed = self.status()
        if bridge.ok or refreshed.lab_deployed:
            # Avoid Docker restart-without-veths (breaks eth1/eth2 OSPF links).
            for suffix in ("r1", "r2", "r3", "fw1"):
                run_argv(
                    [
                        "docker",
                        "update",
                        "--restart=no",
                        f"clab-{self.settings.lab_name}-{suffix}",
                    ],
                    timeout=20,
                )
            refreshed = self.status()
            refreshed.message = "ContainerLab deploy completed."
            if refreshed.lab_deployed:
                refreshed.mode = ExecutionMode.REAL_LAB
        else:
            refreshed.mode = ExecutionMode.UNAVAILABLE
            refreshed.message = f"Deploy failed: {bridge.stderr or bridge.stdout or 'unknown error'}"
        return refreshed

    def destroy(self) -> LabStatus:
        status = self.status()
        if not status.containerlab_ok:
            status.message = "Cannot destroy: ContainerLab not installed."
            return status
        clab = which_clab() or "clab"
        bridge = run_argv(
            [clab, "destroy", "-t", str(TOPOLOGY_FILE), "--cleanup"],
            timeout=180,
            cwd=str(LAB_DIR),
        )
        refreshed = self.status()
        refreshed.message = (
            "Lab destroy completed."
            if bridge.ok or not refreshed.lab_deployed
            else f"Destroy failed: {bridge.stderr or bridge.stdout}"
        )
        return refreshed

    def inspect_routes(self, router_name: str) -> dict:
        mapping = {"R1": "r1", "R2": "r2", "R3": "r3"}
        suffix = mapping.get(router_name.upper())
        if not suffix:
            return {"mode": ExecutionMode.UNAVAILABLE.value, "message": "Invalid router"}
        container = f"clab-{self.settings.lab_name}-{suffix}"
        result = self.docker.vtysh_show(container, "show ip route json")
        if not result.ok:
            result = self.docker.vtysh_show(container, "show ip route")
        return {
            "mode": ExecutionMode.REAL_LAB.value if result.ok else ExecutionMode.UNAVAILABLE.value,
            "router": router_name.upper(),
            "container": container,
            "ok": result.ok,
            "raw_output": result.stdout if result.ok else "",
            "message": result.error or "ok",
        }

    def set_link_enabled(self, link_name: str, enabled: bool) -> dict:
        """Flip a lab data-plane interface (eth1/eth2) inside a router container."""
        # link_name format: R1-eth1 or clab-routewise-r1:eth1
        parts = link_name.replace(":", "-").split("-")
        if len(parts) < 2:
            return {
                "mode": ExecutionMode.UNAVAILABLE.value,
                "ok": False,
                "message": "Expected link_name like R1-eth1",
            }
        router = parts[0].upper()
        iface = parts[-1]
        mapping = {"R1": "r1", "R2": "r2", "R3": "r3"}
        suffix = mapping.get(router)
        if not suffix or iface not in {"eth1", "eth2"}:
            return {
                "mode": ExecutionMode.UNAVAILABLE.value,
                "ok": False,
                "message": "Only R1|R2|R3 eth1|eth2 supported",
            }
        container = f"clab-{self.settings.lab_name}-{suffix}"
        action = "up" if enabled else "down"
        bridge = run_argv(
            ["docker", "exec", container, "ip", "link", "set", iface, action],
            timeout=30,
        )
        return {
            "mode": ExecutionMode.REAL_LAB.value if bridge.ok else ExecutionMode.UNAVAILABLE.value,
            "ok": bridge.ok,
            "container": container,
            "interface": iface,
            "action": action,
            "message": "ok" if bridge.ok else (bridge.stderr or bridge.stdout),
        }
