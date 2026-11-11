"""Provider boundary between software simulation and real ContainerLab/FRR."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExecutionMode(str, Enum):
    SOFTWARE_SIMULATION = "SOFTWARE_SIMULATION"
    REAL_LAB = "REAL_LAB"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class LabStatus:
    mode: ExecutionMode
    docker_ok: bool
    containerlab_ok: bool
    lab_deployed: bool
    routers: list[dict[str, Any]] = field(default_factory=list)
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


class NetworkProvider(ABC):
    """Abstract network execution backend."""

    name: str
    mode: ExecutionMode

    @abstractmethod
    def status(self) -> LabStatus:
        raise NotImplementedError

    @abstractmethod
    def deploy(self) -> LabStatus:
        raise NotImplementedError

    @abstractmethod
    def destroy(self) -> LabStatus:
        raise NotImplementedError

    def inspect_routes(self, router_name: str) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "router": router_name,
            "routes": [],
            "message": "Not implemented for this provider",
        }

    def set_link_enabled(self, link_name: str, enabled: bool) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "ok": False,
            "message": "Link control not implemented for this provider",
        }
