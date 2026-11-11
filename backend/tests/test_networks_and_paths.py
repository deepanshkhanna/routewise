"""Persistence, path finding, optimization, and failure simulation tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def _override_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_db
    # Seed via API
    with TestClient(app) as test_client:
        seed = test_client.post("/api/networks/seed-default")
        assert seed.status_code == 200
        yield test_client
    app.dependency_overrides.clear()


def test_network_seeded_with_triangle(client: TestClient) -> None:
    networks = client.get("/api/networks")
    assert networks.status_code == 200
    assert len(networks.json()) >= 1
    net_id = networks.json()[0]["id"]
    detail = client.get(f"/api/networks/{net_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert len(body["routers"]) == 3
    assert len(body["links"]) == 3


def test_paths_and_optimize(client: TestClient) -> None:
    net_id = client.get("/api/networks").json()[0]["id"]
    paths = client.get(f"/api/networks/{net_id}/paths", params={"source": "R1", "destination": "R3"})
    assert paths.status_code == 200
    payload = paths.json()
    assert payload["data_source"] == "software_simulation"
    assert len(payload["candidate_paths"]) >= 2
    assert payload["protocol_selected_path"] is not None

    opt = client.get(
        f"/api/networks/{net_id}/optimize",
        params={"source": "R1", "destination": "R3"},
    )
    assert opt.status_code == 200
    recommendation = opt.json()
    assert recommendation["recommended_path"] is not None
    assert "score" in recommendation["recommended_path"]
    assert "software_simulation" in recommendation["explanation"]


def test_disable_link_changes_availability(client: TestClient) -> None:
    net_id = client.get("/api/networks").json()[0]["id"]
    detail = client.get(f"/api/networks/{net_id}").json()
    direct = next(link for link in detail["links"] if link["subnet"] == "10.0.13.0/30")

    before = client.get(
        f"/api/networks/{net_id}/paths",
        params={"source": "R1", "destination": "R3"},
    ).json()
    assert any(p["hops"] == ["R1", "R3"] for p in before["candidate_paths"])

    disabled = client.post(f"/api/networks/{net_id}/simulate/links/{direct['id']}/disable")
    assert disabled.status_code == 200
    assert disabled.json()["after_active_links"] == disabled.json()["before_active_links"] - 1

    after = client.get(
        f"/api/networks/{net_id}/paths",
        params={"source": "R1", "destination": "R3"},
    ).json()
    assert all(p["hops"] != ["R1", "R3"] for p in after["candidate_paths"])
    assert after["protocol_selected_path"]["hops"] == ["R1", "R2", "R3"]

    restored = client.post(f"/api/networks/{net_id}/simulate/links/{direct['id']}/enable")
    assert restored.status_code == 200


def test_ping_and_events(client: TestClient) -> None:
    net_id = client.get("/api/networks").json()[0]["id"]
    ping = client.post(
        f"/api/networks/{net_id}/diagnostics/ping",
        json={"source": "R1", "destination": "R3"},
    )
    assert ping.status_code == 200
    assert ping.json()["success"] is True
    assert ping.json()["data_source"] == "software_simulation"

    events = client.get(f"/api/networks/{net_id}/events")
    assert events.status_code == 200
    assert len(events.json()) >= 1


def test_dashboard_overview(client: TestClient) -> None:
    response = client.get("/api/dashboard/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["total_routers"] >= 3
    assert body["default_network_id"] is not None
