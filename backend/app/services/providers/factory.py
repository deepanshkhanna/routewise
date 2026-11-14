"""Select the best available network provider."""

from __future__ import annotations

import time

from app.services.providers.base import ExecutionMode, LabStatus, NetworkProvider
from app.services.providers.containerlab import ContainerLabProvider
from app.services.providers.software import SoftwareSimulationProvider

_INFRA_CACHE: tuple[float, dict] | None = None


def invalidate_infrastructure_cache() -> None:
    global _INFRA_CACHE
    _INFRA_CACHE = None


def probe_infrastructure(ttl_seconds: float = 4.0) -> dict:
    """Return combined infrastructure health for Settings UI."""
    global _INFRA_CACHE
    now = time.monotonic()
    if _INFRA_CACHE is not None and now < _INFRA_CACHE[0]:
        return _INFRA_CACHE[1]

    software = SoftwareSimulationProvider().status()
    real = ContainerLabProvider().status()
    active = ExecutionMode.REAL_LAB if real.lab_deployed else ExecutionMode.SOFTWARE_SIMULATION
    payload = {
        "active_mode": active.value,
        "software": {
            "mode": software.mode.value,
            "message": software.message,
            "available": True,
        },
        "real_lab": {
            "mode": real.mode.value,
            "docker_ok": real.docker_ok,
            "containerlab_ok": real.containerlab_ok,
            "lab_deployed": real.lab_deployed,
            "routers": real.routers,
            "message": real.message,
            "details": real.details,
        },
        "message": (
            "REAL_LAB active."
            if active == ExecutionMode.REAL_LAB
            else "SOFTWARE_SIMULATION active; real lab unavailable or not deployed."
        ),
    }
    _INFRA_CACHE = (now + ttl_seconds, payload)
    return payload


def get_active_provider() -> NetworkProvider:
    real = ContainerLabProvider()
    status = real.status()
    if status.lab_deployed:
        return real
    return SoftwareSimulationProvider()


def get_lab_provider() -> ContainerLabProvider:
    return ContainerLabProvider()


def combined_lab_status() -> LabStatus:
    infra = probe_infrastructure()
    if infra["active_mode"] == ExecutionMode.REAL_LAB.value:
        return get_lab_provider().status()
    return SoftwareSimulationProvider().status()
