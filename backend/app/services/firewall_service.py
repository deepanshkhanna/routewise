"""Firewall policy management for the isolated RouteWise lab."""

from __future__ import annotations

import ipaddress
import logging

from sqlalchemy.orm import Session

from app.db.models import Event, FirewallRule
from app.schemas.firewall import (
    FirewallRuleCreate,
    FirewallStatus,
    FirewallTestRequest,
    FirewallTestResult,
)
from app.services.network_service import NetworkService
from app.services.providers.factory import probe_infrastructure
from app.services.wsl_bridge import run_argv

logger = logging.getLogger(__name__)

FW_CONTAINER = "clab-routewise-fw1"


class FirewallService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.networks = NetworkService(db)

    def _mode(self) -> str:
        try:
            infra = probe_infrastructure()
            return infra.get("active_mode", "SOFTWARE_SIMULATION")
        except Exception:  # noqa: BLE001
            logger.exception("Infrastructure probe failed; defaulting to SOFTWARE_SIMULATION")
            return "SOFTWARE_SIMULATION"

    def status(self, network_id: int) -> FirewallStatus:
        self.networks.get_network(network_id)
        rules = self.list_rules(network_id)
        mode = self._mode()
        engine = "nftables" if mode == "REAL_LAB" else "software_policy_engine"
        return FirewallStatus(
            network_id=network_id,
            mode=mode,
            engine=engine,
            rule_count=len(rules),
            enabled_rules=sum(1 for r in rules if r.enabled),
            message=(
                "Firewall policies tracked in SQLite. "
                + (
                    "REAL_LAB deploy can apply nftables inside lab containers when available."
                    if mode == "REAL_LAB"
                    else "SOFTWARE_SIMULATION evaluates allow/deny without touching the host firewall."
                )
            ),
        )

    def list_rules(self, network_id: int) -> list[FirewallRule]:
        self.networks.get_network(network_id)
        return (
            self.db.query(FirewallRule)
            .filter(FirewallRule.network_id == network_id)
            .order_by(FirewallRule.priority.asc(), FirewallRule.id.asc())
            .all()
        )

    def create_rule(self, network_id: int, payload: FirewallRuleCreate) -> FirewallRule:
        self.networks.get_network(network_id)
        self._validate_endpoints(payload.source, payload.destination)
        rule = FirewallRule(
            network_id=network_id,
            **payload.model_dump(),
            data_source="software_simulation",
        )
        self.db.add(rule)
        self.db.add(
            Event(
                network_id=network_id,
                severity="info",
                category="firewall",
                description=f"Firewall rule added: {payload.action} {payload.protocol} {payload.source}->{payload.destination}:{payload.port}",
                data_source="software_simulation",
            )
        )
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete_rule(self, network_id: int, rule_id: int) -> None:
        rule = (
            self.db.query(FirewallRule)
            .filter(FirewallRule.network_id == network_id, FirewallRule.id == rule_id)
            .first()
        )
        if not rule:
            raise LookupError(f"Firewall rule {rule_id} not found")
        self.db.delete(rule)
        self.db.add(
            Event(
                network_id=network_id,
                severity="warning",
                category="firewall",
                description=f"Firewall rule {rule_id} deleted",
                data_source="software_simulation",
            )
        )
        self.db.commit()

    def set_enabled(self, network_id: int, rule_id: int, enabled: bool) -> FirewallRule:
        rule = (
            self.db.query(FirewallRule)
            .filter(FirewallRule.network_id == network_id, FirewallRule.id == rule_id)
            .first()
        )
        if not rule:
            raise LookupError(f"Firewall rule {rule_id} not found")
        rule.enabled = enabled
        self.db.add(
            Event(
                network_id=network_id,
                severity="info",
                category="firewall",
                description=f"Firewall rule {rule_id} {'enabled' if enabled else 'disabled'}",
                data_source="software_simulation",
            )
        )
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def apply_to_lab(self, network_id: int) -> dict:
        """Push enabled rules into the isolated fw1 nftables table (lab only)."""
        self.networks.get_network(network_id)
        mode = self._mode()
        if mode != "REAL_LAB":
            return {
                "ok": False,
                "mode": mode,
                "message": "REAL_LAB not active — rules remain in SQLite only.",
            }

        # Ensure table/chain exist inside fw1.
        for cmd in (
            ["docker", "exec", FW_CONTAINER, "nft", "add", "table", "inet", "routewise"],
            [
                "docker",
                "exec",
                FW_CONTAINER,
                "nft",
                "add",
                "chain",
                "inet",
                "routewise",
                "input",
                "{ type filter hook input priority 0 ; policy accept ; }",
            ],
        ):
            run_argv(cmd, timeout=30)

        flush = run_argv(
            ["docker", "exec", FW_CONTAINER, "nft", "flush", "chain", "inet", "routewise", "input"],
            timeout=30,
        )
        applied = 0
        errors: list[str] = []
        for rule in self.list_rules(network_id):
            if not rule.enabled:
                continue
            nft_args = self._to_nft_args(rule)
            if not nft_args:
                errors.append(f"rule {rule.id} skipped (unsupported combo)")
                continue
            bridge = run_argv(
                ["docker", "exec", FW_CONTAINER, "nft", "add", "rule", "inet", "routewise", "input", *nft_args],
                timeout=30,
            )
            if bridge.ok:
                applied += 1
                rule.data_source = "real_lab_nftables"
            else:
                errors.append(f"rule {rule.id}: {bridge.stderr or bridge.stdout}")
        self.db.add(
            Event(
                network_id=network_id,
                severity="info",
                category="firewall",
                description=f"Applied {applied} firewall rules to {FW_CONTAINER}",
                data_source="real_lab",
            )
        )
        self.db.commit()
        listing = run_argv(
            ["docker", "exec", FW_CONTAINER, "nft", "list", "table", "inet", "routewise"],
            timeout=30,
        )
        return {
            "ok": flush.ok or applied > 0,
            "mode": "REAL_LAB",
            "applied": applied,
            "errors": errors,
            "container": FW_CONTAINER,
            "ruleset": listing.stdout if listing.ok else "",
            "message": f"Applied {applied} rules to isolated lab container {FW_CONTAINER}.",
        }

    @staticmethod
    def _to_nft_args(rule: FirewallRule) -> list[str] | None:
        """Map a stored rule to allowlisted nft argv fragments (no shell)."""
        args: list[str] = []
        if rule.protocol != "any":
            if rule.protocol == "icmp":
                args.extend(["ip", "protocol", "icmp"])
            elif rule.protocol in {"tcp", "udp"}:
                args.extend(["ip", "protocol", rule.protocol])
                if rule.port != "any":
                    args.extend([rule.protocol, "dport", str(rule.port)])
            else:
                return None
        if rule.source != "any":
            args.extend(["ip", "saddr", rule.source])
        if rule.destination != "any":
            args.extend(["ip", "daddr", rule.destination])
        args.append("counter")
        args.append("accept" if rule.action == "allow" else "drop")
        return args

    def test(self, network_id: int, payload: FirewallTestRequest) -> FirewallTestResult:
        """Evaluate first-match policy in software (never touches host firewall)."""
        self.networks.get_network(network_id)
        rules = [r for r in self.list_rules(network_id) if r.enabled]
        mode = self._mode()
        for rule in rules:
            if not self._protocol_match(rule.protocol, payload.protocol):
                continue
            if not self._endpoint_match(rule.source, payload.source):
                continue
            if not self._endpoint_match(rule.destination, payload.destination):
                continue
            if not self._port_match(rule.port, payload.port):
                continue
            rule.hit_count += 1
            self.db.commit()
            allowed = rule.action == "allow"
            return FirewallTestResult(
                network_id=network_id,
                mode=mode if mode == "REAL_LAB" else "SOFTWARE_SIMULATION",
                allowed=allowed,
                matched_rule_id=rule.id,
                matched_rule_name=rule.name or f"rule-{rule.id}",
                message=(
                    f"Matched rule #{rule.id} action={rule.action}. "
                    "Evaluation source=software_policy_engine "
                    "(host Windows firewall untouched)."
                ),
            )
        return FirewallTestResult(
            network_id=network_id,
            mode="SOFTWARE_SIMULATION",
            allowed=True,
            matched_rule_id=None,
            matched_rule_name=None,
            message="No matching rule — default allow in software lab policy engine.",
        )

    @staticmethod
    def _validate_endpoints(source: str, destination: str) -> None:
        for label, value in (("source", source), ("destination", destination)):
            if value == "any":
                continue
            try:
                if "/" in value:
                    ipaddress.ip_network(value, strict=False)
                else:
                    ipaddress.ip_address(value)
            except ValueError as exc:
                raise ValueError(f"Invalid {label}: {value}") from exc

    @staticmethod
    def _protocol_match(rule_proto: str, packet_proto: str) -> bool:
        return rule_proto == "any" or rule_proto.lower() == packet_proto.lower()

    @staticmethod
    def _port_match(rule_port: str, packet_port: str) -> bool:
        return rule_port == "any" or rule_port == packet_port or packet_port == "any"

    @staticmethod
    def _endpoint_match(rule_ep: str, packet_ep: str) -> bool:
        if rule_ep == "any" or packet_ep == "any":
            return True
        try:
            if "/" in rule_ep:
                return ipaddress.ip_address(packet_ep) in ipaddress.ip_network(rule_ep, strict=False)
            return rule_ep == packet_ep
        except ValueError:
            return rule_ep == packet_ep
