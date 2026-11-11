"""Firewall policy engine tests (software simulation)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _network_id() -> int:
    seeded = client.post("/api/networks/seed-default")
    assert seeded.status_code in {200, 201}
    return seeded.json()["id"]


def test_firewall_rule_crud_and_test() -> None:
    nid = _network_id()
    status = client.get(f"/api/networks/{nid}/firewall/status")
    assert status.status_code == 200
    body = status.json()
    assert body["engine"] in {"software_policy_engine", "nftables"}
    assert "mode" in body

    # Clear leftover rules from prior API smoke tests on the shared SQLite DB.
    existing = client.get(f"/api/networks/{nid}/firewall/rules")
    assert existing.status_code == 200
    for rule in existing.json():
        client.delete(f"/api/networks/{nid}/firewall/rules/{rule['id']}")

    created = client.post(
        f"/api/networks/{nid}/firewall/rules",
        json={
            "name": "deny-icmp-demo",
            "action": "deny",
            "protocol": "icmp",
            "source": "10.0.12.1",
            "destination": "10.0.23.2",
            "port": "any",
            "priority": 10,
        },
    )
    assert created.status_code == 201
    rule = created.json()
    assert rule["action"] == "deny"

    rules = client.get(f"/api/networks/{nid}/firewall/rules")
    assert rules.status_code == 200
    assert any(r["id"] == rule["id"] for r in rules.json())

    denied = client.post(
        f"/api/networks/{nid}/firewall/test",
        json={
            "source": "10.0.12.1",
            "destination": "10.0.23.2",
            "protocol": "icmp",
        },
    )
    assert denied.status_code == 200
    assert denied.json()["allowed"] is False
    assert denied.json()["matched_rule_id"] == rule["id"]

    disabled = client.post(f"/api/networks/{nid}/firewall/rules/{rule['id']}/disable")
    assert disabled.status_code == 200
    assert disabled.json()["enabled"] is False

    allowed = client.post(
        f"/api/networks/{nid}/firewall/test",
        json={
            "source": "10.0.12.1",
            "destination": "10.0.23.2",
            "protocol": "icmp",
        },
    )
    assert allowed.status_code == 200
    assert allowed.json()["allowed"] is True

    deleted = client.delete(f"/api/networks/{nid}/firewall/rules/{rule['id']}")
    assert deleted.status_code == 204


def test_firewall_rejects_bad_cidr() -> None:
    nid = _network_id()
    bad = client.post(
        f"/api/networks/{nid}/firewall/rules",
        json={
            "name": "bad",
            "action": "deny",
            "protocol": "tcp",
            "source": "not-an-ip",
            "destination": "any",
        },
    )
    assert bad.status_code == 400
