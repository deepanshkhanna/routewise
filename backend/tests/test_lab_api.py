"""Lab infrastructure API tests (mocked provider)."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.providers.base import ExecutionMode, LabStatus

client = TestClient(app)


def test_infrastructure_probe() -> None:
    with patch(
        "app.api.routes.lab.probe_infrastructure",
        return_value={
            "active_mode": "SOFTWARE_SIMULATION",
            "software": {"available": True},
            "real_lab": {"lab_deployed": False},
            "message": "SOFTWARE_SIMULATION active",
        },
    ):
        resp = client.get("/api/lab/infrastructure")
        assert resp.status_code == 200
        assert resp.json()["active_mode"] == "SOFTWARE_SIMULATION"


def test_deploy_returns_structured_result() -> None:
    fake = LabStatus(
        mode=ExecutionMode.UNAVAILABLE,
        docker_ok=True,
        containerlab_ok=True,
        lab_deployed=False,
        message="Cannot deploy: mocked",
        details={},
    )
    with patch("app.api.routes.lab.get_lab_provider") as gp:
        gp.return_value.deploy.return_value = fake
        resp = client.post("/api/lab/deploy")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is False
        assert "message" in body
