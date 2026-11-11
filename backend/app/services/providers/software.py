"""Software-simulation provider — always available without Docker."""

from __future__ import annotations

from app.services.providers.base import ExecutionMode, LabStatus, NetworkProvider


class SoftwareSimulationProvider(NetworkProvider):
    name = "software_simulation"
    mode = ExecutionMode.SOFTWARE_SIMULATION

    def status(self) -> LabStatus:
        return LabStatus(
            mode=ExecutionMode.SOFTWARE_SIMULATION,
            docker_ok=False,
            containerlab_ok=False,
            lab_deployed=False,
            routers=[
                {"id": "R1", "status": "simulated"},
                {"id": "R2", "status": "simulated"},
                {"id": "R3", "status": "simulated"},
            ],
            message=(
                "Active control plane is SOFTWARE_SIMULATION. "
                "Path/optimize/failover use the SQLite topology graph."
            ),
            details={"persistent": True, "frr": False},
        )

    def deploy(self) -> LabStatus:
        status = self.status()
        status.message = (
            "Deploy is a no-op for SOFTWARE_SIMULATION. "
            "Use ContainerLabProvider when Docker + ContainerLab are available."
        )
        return status

    def destroy(self) -> LabStatus:
        status = self.status()
        status.message = "Destroy is a no-op for SOFTWARE_SIMULATION."
        return status

    def set_link_enabled(self, link_name: str, enabled: bool) -> dict:
        return {
            "mode": self.mode.value,
            "ok": True,
            "link": link_name,
            "enabled": enabled,
            "message": "Link state changes are applied in SQLite by SimulationService.",
        }
