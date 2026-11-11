"""Topology endpoint tests — configured design data only."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_topology_returns_triangle() -> None:
    response = client.get("/api/topology")
    assert response.status_code == 200
    data = response.json()
    assert data["protocol"] == "OSPF"
    assert data["area"] == "0"
    assert len(data["nodes"]) == 3
    assert len(data["links"]) == 3

    loopbacks = {node["id"]: node["loopback"] for node in data["nodes"]}
    assert loopbacks == {
        "R1": "192.168.1.1/32",
        "R2": "192.168.2.2/32",
        "R3": "192.168.3.3/32",
    }

    subnets = {link["subnet"] for link in data["links"]}
    assert subnets == {"10.0.12.0/30", "10.0.23.0/30", "10.0.13.0/30"}
