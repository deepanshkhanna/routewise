#!/usr/bin/env bash
# Verify local development prerequisites for RouteWise.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ok=0
fail=0

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

check_any() {
  local label="$1"
  shift
  local cmd
  for cmd in "$@"; do
    if have_cmd "$cmd"; then
      local ver
      ver="$("$cmd" --version 2>&1 | head -n 1)"
      echo "[OK]  $label ($ver)"
      ok=$((ok + 1))
      return 0
    fi
  done
  echo "[MISS] $label"
  fail=$((fail + 1))
  return 1
}

echo "RouteWise environment check"
echo "Project root: $ROOT"
echo

check_any "python" python python3 || true
check_any "node" node || true
check_any "npm" npm || true
check_any "docker" docker || true
check_any "git" git || true

if have_cmd containerlab; then
  echo "[OK]  containerlab ($(containerlab version 2>/dev/null | head -n 1))"
  ok=$((ok + 1))
else
  echo "[MISS] containerlab (install in WSL before deploying the lab)"
  fail=$((fail + 1))
fi

if have_cmd docker && docker info >/dev/null 2>&1; then
  echo "[OK]  docker daemon reachable"
  ok=$((ok + 1))
else
  echo "[MISS] docker daemon not reachable (start Docker Desktop)"
  fail=$((fail + 1))
fi

echo
echo "Note: On Windows, prefer Git Bash or PowerShell for frontend/backend."
echo "      ContainerLab deploy/destroy should run inside WSL2 Ubuntu."
echo
echo "Summary: $ok checks passed, $fail missing/failed"
# Do not hard-fail solely because containerlab is missing during init.
if [[ "$fail" -gt 0 ]]; then
  exit 1
fi
