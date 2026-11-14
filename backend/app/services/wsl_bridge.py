"""Invoke Docker / ContainerLab via WSL2 when the Windows daemon is down.

Never opens an unauthenticated Docker TCP port. Prefers native Windows docker
when the daemon responds; otherwise falls back to `wsl.exe -e ...`.
"""

from __future__ import annotations

import logging
import platform
import shutil
import subprocess
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Cache native Windows docker availability and clab lookup so we don't pay
# a 1.5s named-pipe timeout on every single CLI call when Docker Desktop is off.
_NATIVE_DOCKER_DEAD_UNTIL: float = 0.0
_CLAB_CACHE: tuple[float, str | None] = (0.0, None)


@dataclass(frozen=True)
class BridgeResult:
    ok: bool
    stdout: str
    stderr: str
    returncode: int
    via: str  # "native" | "wsl" | "none"


def _is_windows() -> bool:
    return platform.system().lower() == "windows"


def wsl_available() -> bool:
    if not _is_windows():
        return False
    return shutil.which("wsl") is not None


def run_argv(args: list[str], *, timeout: int = 60, cwd: str | None = None) -> BridgeResult:
    """Run argv natively; on Windows failure for docker/clab, retry inside WSL."""
    global _NATIVE_DOCKER_DEAD_UNTIL
    now = time.monotonic()
    exe_base = (args[0] if args else "").replace("\\", "/").split("/")[-1].lower()
    is_docker_or_clab = exe_base in {
        "docker",
        "docker.exe",
        "clab",
        "clab.exe",
        "containerlab",
        "containerlab.exe",
    }

    if _is_windows() and is_docker_or_clab and now < _NATIVE_DOCKER_DEAD_UNTIL and wsl_available():
        return run_via_wsl(args, timeout=timeout, cwd=cwd)

    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            shell=False,
            cwd=cwd,
        )
        out = (completed.stdout or "").strip()
        err = (completed.stderr or "").strip()
        if completed.returncode == 0:
            return BridgeResult(
                ok=True,
                stdout=out,
                stderr=err,
                returncode=0,
                via="native",
            )
        # Fall through to WSL for docker/clab when Windows daemon is down.
        if not _should_try_wsl(args, err):
            return BridgeResult(
                ok=False,
                stdout=out,
                stderr=err,
                returncode=completed.returncode,
                via="native",
            )
        if _is_windows() and is_docker_or_clab:
            _NATIVE_DOCKER_DEAD_UNTIL = time.monotonic() + 60.0
    except FileNotFoundError:
        if not wsl_available():
            return BridgeResult(False, "", "executable not found", -1, "none")
        if _is_windows() and is_docker_or_clab:
            _NATIVE_DOCKER_DEAD_UNTIL = time.monotonic() + 60.0
    except subprocess.TimeoutExpired:
        return BridgeResult(False, "", f"timed out after {timeout}s", -1, "native")

    return run_via_wsl(args, timeout=timeout, cwd=cwd)


def _should_try_wsl(args: list[str], stderr: str) -> bool:
    if not wsl_available():
        return False
    exe = (args[0] if args else "").lower()
    if exe not in {"docker", "clab", "containerlab"} and not exe.endswith(
        ("docker.exe", "clab.exe", "containerlab.exe")
    ):
        # Absolute paths ending with docker/clab also qualify by basename.
        base = exe.replace("\\", "/").split("/")[-1]
        if base not in {"docker", "clab", "containerlab", "docker.exe", "clab.exe"}:
            return False
    text = (stderr or "").lower()
    markers = (
        "cannot connect",
        "error during connect",
        "dockerdesktoplinuxengine",
        "dockerdesktopwindowsengine",
        "the system cannot find the file specified",
        "is the docker daemon running",
        "failed to connect to the docker api",
        "pipe",
    )
    return any(m in text for m in markers) or True  # always try WSL for docker/clab on Win


def run_via_wsl(args: list[str], *, timeout: int = 60, cwd: str | None = None) -> BridgeResult:
    """Translate a Windows argv into `wsl -e bash -lc '...'` with safe quoting."""
    if not wsl_available():
        return BridgeResult(False, "", "WSL not available", -1, "none")

    # Map Windows project paths under /mnt/<drive>/...
    translated: list[str] = []
    for arg in args:
        translated.append(_to_wsl_path(arg) if _looks_like_windows_path(arg) else arg)

    # Prefer bare binary names inside WSL PATH.
    if translated:
        base = translated[0].replace("\\", "/").split("/")[-1].lower()
        if base in {"docker.exe", "docker"}:
            translated[0] = "docker"
        elif base in {"clab.exe", "clab", "containerlab.exe", "containerlab"}:
            translated[0] = "clab"

    remote_cwd = _to_wsl_path(cwd) if cwd else None
    quoted = " ".join(_bash_quote(a) for a in translated)
    if remote_cwd:
        script = f"cd {_bash_quote(remote_cwd)} && export PATH=/usr/bin:/usr/local/bin:$PATH && {quoted}"
    else:
        script = f"export PATH=/usr/bin:/usr/local/bin:$PATH && {quoted}"

    wsl_argv = ["wsl", "-e", "bash", "-lc", script]
    try:
        completed = subprocess.run(
            wsl_argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            shell=False,
        )
        return BridgeResult(
            ok=completed.returncode == 0,
            stdout=(completed.stdout or "").strip(),
            stderr=(completed.stderr or "").strip(),
            returncode=completed.returncode,
            via="wsl",
        )
    except subprocess.TimeoutExpired:
        return BridgeResult(False, "", f"WSL timed out after {timeout}s", -1, "wsl")
    except OSError as exc:
        return BridgeResult(False, "", str(exc), -1, "wsl")


def _looks_like_windows_path(value: str) -> bool:
    if len(value) >= 3 and value[1] == ":" and value[2] in {"\\", "/"}:
        return True
    return "\\" in value and not value.startswith("-")


def _to_wsl_path(path: str | None) -> str:
    if not path:
        return ""
    normalized = path.replace("\\", "/")
    if len(normalized) >= 2 and normalized[1] == ":":
        drive = normalized[0].lower()
        rest = normalized[2:].lstrip("/")
        return f"/mnt/{drive}/{rest}"
    return normalized


def _bash_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def which_clab() -> str | None:
    """Return a usable clab invocation token: native path or 'clab' via WSL."""
    global _CLAB_CACHE
    now = time.monotonic()
    if now < _CLAB_CACHE[0]:
        return _CLAB_CACHE[1]
    native = shutil.which("containerlab") or shutil.which("clab")
    if native:
        _CLAB_CACHE = (now + 60.0, native)
        return native
    if wsl_available():
        probe = run_via_wsl(["clab", "version"], timeout=20)
        if probe.ok or "version" in (probe.stdout + probe.stderr).lower():
            _CLAB_CACHE = (now + 60.0, "clab")
            return "clab"
    _CLAB_CACHE = (now + 15.0, None)
    return None
