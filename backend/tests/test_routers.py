"""Router list and inspection API tests with mocked Docker/FRR."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.docker_service import CommandResult, DockerErrorKind

client = TestClient(app)


def _result(
    ok: bool = True,
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
    error: str | None = None,
    error_kind: DockerErrorKind = DockerErrorKind.NONE,
) -> CommandResult:
    return CommandResult(
        ok=ok,
        stdout=stdout,
        stderr=stderr,
        returncode=returncode,
        error=error,
        error_kind=error_kind,
    )


def test_router_list_returns_three_configured_routers() -> None:
    with patch("app.services.routing_service.DockerService") as docker_cls:
        docker = docker_cls.return_value
        docker.docker_available.return_value = _result(ok=True, stdout="24.0.0")
        docker.container_name.side_effect = lambda rid: f"clab-routewise-{rid.lower()}"
        docker.inspect_container_state.return_value = (
            "unavailable",
            _result(
                ok=False,
                error="Container not found",
                error_kind=DockerErrorKind.NOT_FOUND,
                returncode=1,
            ),
        )

        response = client.get("/api/routers")
        assert response.status_code == 200
        payload = response.json()
        ids = [r["id"] for r in payload["routers"]]
        assert ids == ["R1", "R2", "R3"]
        assert payload["lab_running"] is False
        for router in payload["routers"]:
            assert router["available"] is False
            assert router["protocol"] == "OSPF"
            assert router["loopback"].endswith("/32")


def test_invalid_router_id_rejected() -> None:
    response = client.get("/api/routers/R99/routes")
    assert response.status_code == 400
    body = response.json()
    assert "detail" in body


def test_invalid_router_id_rejected_for_ospf() -> None:
    response = client.get("/api/routers/hack;rm/ospf-neighbors")
    assert response.status_code == 400


def test_missing_container_handled() -> None:
    with patch("app.services.routing_service.DockerService") as docker_cls:
        docker = docker_cls.return_value
        docker.container_name.return_value = "clab-routewise-r1"
        docker.inspect_container_state.return_value = (
            "unavailable",
            _result(
                ok=False,
                error="Container not found",
                error_kind=DockerErrorKind.NOT_FOUND,
                returncode=1,
            ),
        )
        response = client.get("/api/routers/R1/routes")
        assert response.status_code == 404
        payload = response.json()
        assert payload["error_code"] == "router_not_found"
        assert payload["available"] is False
        assert payload["routes"] == []


def test_stopped_router_handled() -> None:
    with patch("app.services.routing_service.DockerService") as docker_cls:
        docker = docker_cls.return_value
        docker.container_name.return_value = "clab-routewise-r2"
        docker.inspect_container_state.return_value = (
            "stopped",
            _result(ok=True, stdout="exited"),
        )
        response = client.get("/api/routers/R2/ospf-neighbors")
        assert response.status_code == 409
        payload = response.json()
        assert payload["error_code"] == "router_stopped"
        assert payload["neighbors"] == []


def test_routes_with_mocked_json_output() -> None:
    route_json = """
    {
      "192.168.2.2/32": [
        {
          "prefix": "192.168.2.2/32",
          "protocol": "ospf",
          "metric": 20,
          "nexthops": [{"ip": "10.0.12.2", "interfaceName": "eth1"}]
        }
      ]
    }
    """
    with patch("app.services.routing_service.DockerService") as docker_cls:
        docker = docker_cls.return_value
        docker.container_name.return_value = "clab-routewise-r1"
        docker.inspect_container_state.return_value = ("running", _result(ok=True, stdout="running"))

        def vtysh(container: str, cmd: str) -> CommandResult:
            if cmd == "show ip route json":
                return _result(ok=True, stdout=route_json)
            return _result(ok=False, error="unused", error_kind=DockerErrorKind.EXEC_FAILED, returncode=1)

        docker.vtysh_show.side_effect = vtysh
        response = client.get("/api/routers/R1/routes")
        assert response.status_code == 200
        payload = response.json()
        assert payload["available"] is True
        assert payload["routes"][0]["destination"] == "192.168.2.2/32"
        assert payload["routes"][0]["nexthop"] == "10.0.12.2"
        assert payload["routes"][0]["protocol"] == "ospf"


def test_ospf_neighbors_with_mocked_text_output() -> None:
    text = """
Neighbor ID     Pri State           Dead Time Address         Interface
2.2.2.2           1 Full/DR           00:00:35 10.0.12.2       eth1:10.0.12.1
3.3.3.3           1 Full/Backup       00:00:38 10.0.13.2       eth2:10.0.13.1
"""
    with patch("app.services.routing_service.DockerService") as docker_cls:
        docker = docker_cls.return_value
        docker.container_name.return_value = "clab-routewise-r1"
        docker.inspect_container_state.return_value = ("running", _result(ok=True, stdout="running"))

        def vtysh(container: str, cmd: str) -> CommandResult:
            if cmd == "show ip ospf neighbor json":
                return _result(
                    ok=False,
                    error="json unsupported",
                    error_kind=DockerErrorKind.EXEC_FAILED,
                    returncode=1,
                )
            if cmd == "show ip ospf neighbor":
                return _result(ok=True, stdout=text)
            return _result(ok=False, error="unexpected", error_kind=DockerErrorKind.EXEC_FAILED, returncode=1)

        docker.vtysh_show.side_effect = vtysh
        response = client.get("/api/routers/R1/ospf-neighbors")
        assert response.status_code == 200
        payload = response.json()
        assert payload["available"] is True
        assert len(payload["neighbors"]) == 2
        assert payload["neighbors"][0]["local_router"] == "R1"
        assert payload["neighbors"][0]["neighbor_id"] == "2.2.2.2"
        assert "Full" in payload["neighbors"][0]["state"]


def test_lab_status_handles_docker_unavailable() -> None:
    with patch("app.services.routing_service.DockerService") as docker_cls:
        docker = docker_cls.return_value
        docker.docker_available.return_value = _result(
            ok=False,
            error="Docker daemon is unreachable",
            error_kind=DockerErrorKind.DAEMON_UNAVAILABLE,
            returncode=1,
        )
        docker.container_name.side_effect = lambda rid: f"clab-routewise-{rid.lower()}"
        response = client.get("/api/lab/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["running"] is False
        assert payload["status"] == "unavailable"
        assert payload["docker_ok"] is False
        assert len(payload["routers"]) == 3


def test_arbitrary_command_not_accepted_via_path() -> None:
    # Path parameters cannot inject vtysh/docker commands.
    response = client.get("/api/routers/R1%3Bshow%20running-config/routes")
    assert response.status_code == 400
