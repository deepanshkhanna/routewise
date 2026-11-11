"""DockerService unit tests with mocked WSL/native bridge."""

from __future__ import annotations

from unittest.mock import patch

from app.core.config import ALLOWED_VTYSH_COMMANDS
from app.services.docker_service import DockerErrorKind, DockerService
from app.services.wsl_bridge import BridgeResult


def test_container_names_match_containerlab() -> None:
    svc = DockerService()
    assert svc.container_name("R1") == "clab-routewise-r1"
    assert svc.container_name("R2") == "clab-routewise-r2"
    assert svc.container_name("R3") == "clab-routewise-r3"


def test_bridge_success_path() -> None:
    svc = DockerService()
    with patch(
        "app.services.docker_service.run_argv",
        return_value=BridgeResult(True, "29.1.3", "", 0, "wsl"),
    ) as run:
        result = svc.docker_available()
        assert result.ok
        assert result.stdout == "29.1.3"
        assert run.call_args.args[0][0] == "docker"


def test_vtysh_rejects_arbitrary_command() -> None:
    svc = DockerService()
    result = svc.vtysh_show("clab-routewise-r1", "show running-config")
    assert not result.ok
    assert result.error_kind == DockerErrorKind.REJECTED
    assert "show running-config" not in ALLOWED_VTYSH_COMMANDS


def test_vtysh_rejects_non_allowlisted_container() -> None:
    svc = DockerService()
    result = svc.vtysh_show("evil-container", "show ip route")
    assert not result.ok
    assert result.error_kind == DockerErrorKind.REJECTED


def test_timeout_is_handled() -> None:
    svc = DockerService()
    with patch(
        "app.services.docker_service.run_argv",
        return_value=BridgeResult(False, "", "timed out after 10s", -1, "native"),
    ):
        result = svc.docker_available()
        assert not result.ok
        assert result.error_kind == DockerErrorKind.TIMEOUT


def test_cli_missing_is_handled() -> None:
    svc = DockerService()
    with patch(
        "app.services.docker_service.run_argv",
        return_value=BridgeResult(False, "", "executable not found", -1, "none"),
    ):
        result = svc.docker_available()
        assert not result.ok
        assert result.error_kind == DockerErrorKind.CLI_MISSING


def test_windows_daemon_pipe_error_classified() -> None:
    svc = DockerService()
    stderr = (
        "failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; "
        "check if the path is correct and if the daemon is running: "
        "open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified."
    )
    with patch(
        "app.services.docker_service.run_argv",
        return_value=BridgeResult(False, "", stderr, 1, "native"),
    ):
        result = svc.docker_available()
        assert not result.ok
        assert result.error_kind == DockerErrorKind.DAEMON_UNAVAILABLE


def test_non_docker_argv_rejected() -> None:
    svc = DockerService()
    result = svc._run(["bash", "-c", "id"])
    assert not result.ok
    assert result.error_kind == DockerErrorKind.REJECTED
