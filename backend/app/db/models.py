"""SQLAlchemy models for persisted topologies and events."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Network(Base):
    __tablename__ = "networks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    routers: Mapped[list[Router]] = relationship(
        "Router",
        back_populates="network",
        cascade="all, delete-orphan",
    )
    links: Mapped[list[Link]] = relationship(
        "Link",
        back_populates="network",
        cascade="all, delete-orphan",
    )
    events: Mapped[list[Event]] = relationship(
        "Event",
        back_populates="network",
        cascade="all, delete-orphan",
    )


class Router(Base):
    __tablename__ = "routers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    network_id: Mapped[int] = mapped_column(ForeignKey("networks.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    loopback: Mapped[str] = mapped_column(String(64), default="")
    router_id: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(32), default="up")  # up|down
    protocol: Mapped[str] = mapped_column(String(32), default="OSPF")

    network: Mapped[Network] = relationship("Network", back_populates="routers")


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    network_id: Mapped[int] = mapped_column(ForeignKey("networks.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(64), default="")
    source_router: Mapped[str] = mapped_column(String(64), nullable=False)
    target_router: Mapped[str] = mapped_column(String(64), nullable=False)
    subnet: Mapped[str] = mapped_column(String(64), default="")
    source_ip: Mapped[str] = mapped_column(String(64), default="")
    target_ip: Mapped[str] = mapped_column(String(64), default="")
    cost: Mapped[float] = mapped_column(Float, default=10.0)
    bandwidth_mbps: Mapped[float] = mapped_column(Float, default=1000.0)
    latency_ms: Mapped[float] = mapped_column(Float, default=5.0)
    packet_loss_pct: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="up")  # up|down
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    network: Mapped[Network] = relationship("Network", back_populates="links")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    network_id: Mapped[int] = mapped_column(ForeignKey("networks.id"), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="info")
    category: Mapped[str] = mapped_column(String(64), default="system")
    description: Mapped[str] = mapped_column(Text, default="")
    data_source: Mapped[str] = mapped_column(String(64), default="software_simulation")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    network: Mapped[Network] = relationship("Network", back_populates="events")


class StaticRoute(Base):
    __tablename__ = "static_routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    network_id: Mapped[int] = mapped_column(ForeignKey("networks.id"), nullable=False)
    router_name: Mapped[str] = mapped_column(String(64), nullable=False)
    destination: Mapped[str] = mapped_column(String(64), nullable=False)
    next_hop: Mapped[str] = mapped_column(String(64), nullable=False)
    metric: Mapped[int] = mapped_column(Integer, default=1)


class FirewallRule(Base):
    """Isolated lab firewall policy (software-tracked; optional nftables apply in REAL_LAB)."""

    __tablename__ = "firewall_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    network_id: Mapped[int] = mapped_column(ForeignKey("networks.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), default="")
    action: Mapped[str] = mapped_column(String(16), default="allow")  # allow|deny
    protocol: Mapped[str] = mapped_column(String(16), default="any")  # any|tcp|udp|icmp
    source: Mapped[str] = mapped_column(String(64), default="any")
    destination: Mapped[str] = mapped_column(String(64), default="any")
    port: Mapped[str] = mapped_column(String(32), default="any")
    direction: Mapped[str] = mapped_column(String(16), default="forward")
    priority: Mapped[int] = mapped_column(Integer, default=100)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    data_source: Mapped[str] = mapped_column(String(64), default="software_simulation")
