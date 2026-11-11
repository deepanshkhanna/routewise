"""RoutingService unit tests with a fake DockerService."""

from __future__ import annotations

from app.services.docker_service import CommandResult, DockerErrorKind, DockerService
from app.services.routing_service import RoutingService


class FakeDocker(DockerService):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[str, tuple, dict]] = []
        self._states: dict[str, str] = {}
        self._vtysh: dict[str, CommandResult] = {}
        self._docker_ok = True

    def set_state(self, router_id: str, state: str) -> None:
        self._states[self.container_name(router_id)] = state

    def docker_available(self) -> CommandResult:
        if self._docker_ok:
            return CommandResult(ok=True, stdout="24.0.0", stderr="", returncode=0)
        return CommandResult(
            ok=False,
            stdout="",
            stderr="",
            returncode=1,
            error="Docker daemon is unreachable",
            error_kind=DockerErrorKind.DAEMON_UNAVAILABLE,
        )

    def inspect_container_state(self, container: str):  # type: ignore[override]
        state = self._states.get(container, "unavailable")
        if state == "unavailable":
            return state, CommandResult(
                ok=False,
                stdout="",
                stderr="",
                returncode=1,
                error="Container not found",
                error_kind=DockerErrorKind.NOT_FOUND,
            )
        return state, CommandResult(ok=True, stdout=state, stderr="", returncode=0)

    def vtysh_show(self, container: str, show_command: str) -> CommandResult:
        # Ensure allow-list still enforced by parent for rejection tests.
        if show_command not in {
            "show ip route",
            "show ip route json",
            "show ip ospf neighbor",
            "show ip ospf neighbor json",
            "show interface",
        }:
            return super().vtysh_show(container, show_command)
        key = f"{container}:{show_command}"
        self.calls.append(("vtysh_show", (container, show_command), {}))
        return self._vtysh.get(
            key,
            CommandResult(
                ok=False,
                stdout="",
                stderr="",
                returncode=1,
                error="not stubbed",
                error_kind=DockerErrorKind.EXEC_FAILED,
            ),
        )


def test_lab_status_all_running() -> None:
    docker = FakeDocker()
    for rid in ("R1", "R2", "R3"):
        docker.set_state(rid, "running")
    service = RoutingService(docker=docker)
    status = service.lab_status()
    assert status.running is True
    assert status.status == "running"
    assert set(status.containers_found) == {
        "clab-routewise-r1",
        "clab-routewise-r2",
        "clab-routewise-r3",
    }


def test_routes_prefers_json() -> None:
    docker = FakeDocker()
    docker.set_state("R1", "running")
    docker._vtysh["clab-routewise-r1:show ip route json"] = CommandResult(
        ok=True,
        stdout='{"10.0.23.0/30":[{"protocol":"ospf","metric":20,"nexthops":[{"ip":"10.0.12.2"}]}]}',
        stderr="",
        returncode=0,
    )
    service = RoutingService(docker=docker)
    result = service.get_routes("R1")
    assert result.available is True
    assert result.routes[0].destination == "10.0.23.0/30"
    assert result.routes[0].nexthop == "10.0.12.2"
    assert result.error_code is None


def test_http_status_mapping() -> None:
    assert RoutingService.http_status_for_error("router_not_found") == 404
    assert RoutingService.http_status_for_error("router_stopped") == 409
    assert RoutingService.http_status_for_error("docker_timeout") == 504
    assert RoutingService.http_status_for_error("frr_command_failed") == 502
