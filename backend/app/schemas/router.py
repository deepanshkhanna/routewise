"""Pydantic schemas for router, lab, and topology API responses."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str


class RouterContainerStatus(BaseModel):
    router_id: str
    container_name: str
    status: Literal["running", "stopped", "unavailable", "unknown"]


class LabStatusResponse(BaseModel):
    lab_name: str
    status: Literal["running", "stopped", "unavailable", "unknown"]
    running: bool
    expected_routers: list[str]
    containers_found: list[str]
    routers: list[RouterContainerStatus] = Field(default_factory=list)
    docker_ok: bool = False
    message: str


class RouterInfo(BaseModel):
    id: str
    container_name: str
    loopback: str
    protocol: str
    available: bool
    status: str


class RoutersListResponse(BaseModel):
    lab_running: bool
    routers: list[RouterInfo]
    message: str = ""


class RouteEntry(BaseModel):
    destination: str = ""
    nexthop: str = ""
    protocol: str = ""
    metric: str = ""
    raw: str = ""


class RouterRoutesResponse(BaseModel):
    router_id: str
    available: bool
    status: str
    routes: list[RouteEntry] = Field(default_factory=list)
    raw_output: str = ""
    message: str = ""
    error_code: str | None = None


class OspfNeighbor(BaseModel):
    local_router: str = ""
    neighbor_id: str = ""
    priority: str = ""
    state: str = ""
    address: str = ""
    interface: str = ""
    raw: str = ""


class OspfNeighborsResponse(BaseModel):
    router_id: str
    available: bool
    status: str
    neighbors: list[OspfNeighbor] = Field(default_factory=list)
    raw_output: str = ""
    message: str = ""
    error_code: str | None = None


class TopologyLink(BaseModel):
    id: str
    source: str
    target: str
    subnet: str
    endpoints: dict[str, str]


class TopologyNode(BaseModel):
    id: str
    label: str
    loopback: str


class TopologyResponse(BaseModel):
    name: str
    protocol: str
    area: str
    nodes: list[TopologyNode]
    links: list[TopologyLink]


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None


class ProtocolStatusItem(BaseModel):
    id: str
    name: str
    state: Literal["operational", "degraded", "unavailable", "planned"]
    badge: Literal["ok", "warn", "err", "muted"]
    label: str
    source: str
    detail: str = ""


class ProtocolReadinessResponse(BaseModel):
    mode: str
    lab_deployed: bool
    protocols: list[ProtocolStatusItem]
    message: str = ""

