"""Read-only Docker inspection helpers with fixed command templates."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Literal

from app.core.config import ALLOWED_VTYSH_COMMANDS, ROUTER_INVENTORY, Settings, get_settings
from app.services.wsl_bridge import run_argv

logger = logging.getLogger(__name__)


class DockerErrorKind(str, Enum):
    NONE = "none"
    CLI_MISSING = "cli_missing"
    DAEMON_UNAVAILABLE = "daemon_unavailable"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    EXEC_FAILED = "exec_failed"
    REJECTED = "rejected"
    OS_ERROR = "os_error"


ContainerState = Literal["running", "stopped", "unavailable", "unknown"]


@dataclass(frozen=True)
class CommandResult:
    ok: bool
    stdout: str
    stderr: str
    returncode: int
    error: str | None = None
    error_kind: DockerErrorKind = DockerErrorKind.NONE


class DockerService:
    """Execute allow-listed Docker CLI operations with timeouts."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def container_name(self, router_id: str) -> str:
        meta = ROUTER_INVENTORY[router_id]
        return f"clab-{self.settings.lab_name}-{meta['container_suffix']}"

    def _classify_failure(self, stderr: str, returncode: int) -> DockerErrorKind:
        text = (stderr or "").lower()
        daemon_markers = (
            "cannot connect",
            "failed to connect to the docker api",
            "is the docker daemon running",
            "error during connect",
            "dockerdesktoplinuxengine",
            "dockerdesktopwindowsengine",
            "the system cannot find the file specified",
        )
        if any(marker in text for marker in daemon_markers):
            return DockerErrorKind.DAEMON_UNAVAILABLE
        if "no such object" in text or "no such container" in text:
            return DockerErrorKind.NOT_FOUND
        if returncode != 0:
            return DockerErrorKind.EXEC_FAILED
        return DockerErrorKind.NONE

    def _safe_error_message(self, kind: DockerErrorKind, fallback: str) -> str:
        """Return a client-safe message without filesystem paths or raw dumps."""
        mapping = {
            DockerErrorKind.CLI_MISSING: "Docker CLI is not available on PATH",
            DockerErrorKind.DAEMON_UNAVAILABLE: "Docker daemon is unreachable",
            DockerErrorKind.TIMEOUT: "Docker command timed out",
            DockerErrorKind.NOT_FOUND: "Container not found",
            DockerErrorKind.EXEC_FAILED: "Docker command failed",
            DockerErrorKind.REJECTED: "Command rejected by allow-list",
            DockerErrorKind.OS_ERROR: "Operating system error while running Docker",
        }
        return mapping.get(kind, fallback or "Docker operation failed")

    def _run(self, args: list[str]) -> CommandResult:
        """Run a fixed argv list; never interpolate untrusted shell strings."""
        if not args or args[0] != "docker":
            logger.error("Rejected non-docker argv: %s", args[:1])
            return CommandResult(
                ok=False,
                stdout="",
                stderr="",
                returncode=-1,
                error=self._safe_error_message(DockerErrorKind.REJECTED, ""),
                error_kind=DockerErrorKind.REJECTED,
            )

        timeout = self.settings.docker_timeout_seconds
        bridge = run_argv(args, timeout=timeout)
        if bridge.ok:
            return CommandResult(
                ok=True,
                stdout=bridge.stdout,
                stderr=bridge.stderr,
                returncode=0,
            )

        kind = self._classify_failure(bridge.stderr, bridge.returncode)
        if "not found" in (bridge.stderr or "").lower() and bridge.via == "none":
            kind = DockerErrorKind.CLI_MISSING
        if "timed out" in (bridge.stderr or "").lower():
            kind = DockerErrorKind.TIMEOUT
        logger.warning(
            "Docker command failed kind=%s via=%s rc=%s cmd=%s",
            kind.value,
            bridge.via,
            bridge.returncode,
            args,
        )
        return CommandResult(
            ok=False,
            stdout=bridge.stdout,
            stderr=bridge.stderr,
            returncode=bridge.returncode,
            error=self._safe_error_message(kind, "Docker command failed"),
            error_kind=kind,
        )

    def docker_available(self) -> CommandResult:
        """Verify Docker CLI and daemon via `docker info`."""
        return self._run(["docker", "info", "--format", "{{.ServerVersion}}"])

    def inspect_container_state(self, container: str) -> tuple[ContainerState, CommandResult]:
        """
        Return normalized container state.

        States:
        - running: container exists and is running
        - stopped: container exists but is not running
        - unavailable: container does not exist / not found
        - unknown: Docker CLI/daemon issues or unexpected inspect output
        """
        result = self._run(
            [
                "docker",
                "inspect",
                "-f",
                "{{.State.Status}}",
                container,
            ]
        )
        if result.ok:
            status = result.stdout.strip().lower()
            if status == "running":
                return "running", result
            if status in {"created", "exited", "dead", "paused", "restarting", "removing"}:
                return "stopped", result
            return "unknown", result

        if result.error_kind in {
            DockerErrorKind.CLI_MISSING,
            DockerErrorKind.DAEMON_UNAVAILABLE,
            DockerErrorKind.TIMEOUT,
            DockerErrorKind.OS_ERROR,
        }:
            return "unknown", result
        if result.error_kind == DockerErrorKind.NOT_FOUND:
            return "unavailable", result
        return "unavailable", result

    def container_running(self, container: str) -> CommandResult:
        """Backward-compatible running probe used by older callers/tests."""
        state, result = self.inspect_container_state(container)
        if state == "running":
            return CommandResult(
                ok=True,
                stdout="true",
                stderr=result.stderr,
                returncode=0,
            )
        return CommandResult(
            ok=False,
            stdout="false",
            stderr=result.stderr,
            returncode=result.returncode,
            error=result.error,
            error_kind=result.error_kind,
        )

    def vtysh_show(self, container: str, show_command: str) -> CommandResult:
        """Run a predefined vtysh show command inside an allow-listed container name pattern."""
        if show_command not in ALLOWED_VTYSH_COMMANDS:
            logger.error("Rejected non-allowlisted vtysh command")
            return CommandResult(
                ok=False,
                stdout="",
                stderr="",
                returncode=-1,
                error=self._safe_error_message(DockerErrorKind.REJECTED, ""),
                error_kind=DockerErrorKind.REJECTED,
            )

        # Only allow ContainerLab RouteWise container names.
        expected_prefix = f"clab-{self.settings.lab_name}-"
        allowed_names = {
            f"{expected_prefix}{meta['container_suffix']}"
            for meta in ROUTER_INVENTORY.values()
        }
        if container not in allowed_names:
            logger.error("Rejected non-allowlisted container name")
            return CommandResult(
                ok=False,
                stdout="",
                stderr="",
                returncode=-1,
                error=self._safe_error_message(DockerErrorKind.REJECTED, ""),
                error_kind=DockerErrorKind.REJECTED,
            )

        return self._run(
            [
                "docker",
                "exec",
                container,
                "vtysh",
                "-c",
                show_command,
            ]
        )
