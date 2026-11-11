"""Firewall API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FirewallRuleCreate(BaseModel):
    name: str = ""
    action: str = Field(default="allow", pattern="^(allow|deny)$")
    protocol: str = Field(default="any", pattern="^(any|tcp|udp|icmp)$")
    source: str = "any"
    destination: str = "any"
    port: str = "any"
    direction: str = Field(default="forward", pattern="^(ingress|egress|forward)$")
    priority: int = 100
    enabled: bool = True


class FirewallRuleOut(FirewallRuleCreate):
    id: int
    network_id: int
    hit_count: int = 0
    data_source: str = "software_simulation"

    model_config = {"from_attributes": True}


class FirewallStatus(BaseModel):
    network_id: int
    mode: str
    engine: str
    rule_count: int
    enabled_rules: int
    message: str


class FirewallTestRequest(BaseModel):
    source: str
    destination: str
    protocol: str = "icmp"
    port: str = "any"


class FirewallTestResult(BaseModel):
    network_id: int
    mode: str
    allowed: bool
    matched_rule_id: int | None
    matched_rule_name: str | None
    message: str
