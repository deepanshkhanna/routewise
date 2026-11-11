"""Schemas for persisted networks, paths, optimization, and simulation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RouterCreate(BaseModel):
    name: str
    loopback: str = ""
    router_id: str = ""
    protocol: str = "OSPF"
    status: str = "up"


class RouterOut(RouterCreate):
    id: int
    network_id: int

    model_config = {"from_attributes": True}


class LinkCreate(BaseModel):
    name: str = ""
    source_router: str
    target_router: str
    subnet: str = ""
    source_ip: str = ""
    target_ip: str = ""
    cost: float = 10.0
    bandwidth_mbps: float = 1000.0
    latency_ms: float = 5.0
    packet_loss_pct: float = 0.0
    status: str = "up"
    enabled: bool = True


class LinkOut(LinkCreate):
    id: int
    network_id: int

    model_config = {"from_attributes": True}


class NetworkCreate(BaseModel):
    name: str
    description: str = ""


class NetworkOut(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    routers: list[RouterOut] = Field(default_factory=list)
    links: list[LinkOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class NetworkSummary(BaseModel):
    id: int
    name: str
    description: str
    router_count: int
    link_count: int
    active_links: int
    failed_links: int


class EventOut(BaseModel):
    id: int
    network_id: int
    severity: str
    category: str
    description: str
    data_source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PathHop(BaseModel):
    from_router: str
    to_router: str
    link_id: int
    subnet: str
    cost: float
    latency_ms: float
    packet_loss_pct: float


class CandidatePath(BaseModel):
    hops: list[str]
    hop_count: int
    total_cost: float
    total_latency_ms: float
    avg_packet_loss_pct: float
    available: bool
    links: list[PathHop]
    score: float | None = None
    score_breakdown: dict[str, float] = Field(default_factory=dict)


class PathExploreResponse(BaseModel):
    network_id: int
    source: str
    destination: str
    data_source: str = "software_simulation"
    protocol_selected_path: CandidatePath | None = None
    candidate_paths: list[CandidatePath]
    message: str = ""


class OptimizeResponse(BaseModel):
    network_id: int
    source: str
    destination: str
    data_source: str = "software_simulation"
    recommended_path: CandidatePath | None
    protocol_selected_path: CandidatePath | None
    candidates: list[CandidatePath]
    explanation: str
    formula: str = "S = 0.35L + 0.25P + 0.20H + 0.20C (normalized; lower is better)"


class SimulationResult(BaseModel):
    network_id: int
    action: str
    target: str
    data_source: str = "software_simulation"
    before_active_links: int
    after_active_links: int
    message: str
    event_id: int | None = None


class DiagnosticsRequest(BaseModel):
    source: str
    destination: str


class DiagnosticsResponse(BaseModel):
    network_id: int
    tool: str
    source: str
    destination: str
    success: bool
    data_source: str = "software_simulation"
    hops: list[str] = Field(default_factory=list)
    rtt_ms: float | None = None
    message: str


class StaticRouteCreate(BaseModel):
    router_name: str
    destination: str
    next_hop: str
    metric: int = 1


class StaticRouteOut(StaticRouteCreate):
    id: int
    network_id: int

    model_config = {"from_attributes": True}


class DashboardOverview(BaseModel):
    data_source: str
    networks: int
    total_routers: int
    active_routers: int
    total_links: int
    active_links: int
    failed_links: int
    lab_running: bool
    recent_events: list[EventOut]
    default_network_id: int | None = None
    message: str
