#!/usr/bin/env bash
# Deploy the ContainerLab FRR topology (WSL / Linux only).
# Does NOT modify the Windows host routing table.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAB_DIR="$ROOT/lab"
TOPOLOGY="$LAB_DIR/routewise.clab.yml"

if ! command -v containerlab >/dev/null 2>&1; then
  echo "ERROR: containerlab not found on PATH."
  echo "Install ContainerLab inside WSL2 Ubuntu, then re-run this script from WSL."
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker not found on PATH."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker daemon is not reachable. Start Docker Desktop first."
  exit 1
fi

if [[ ! -f "$TOPOLOGY" ]]; then
  echo "ERROR: Topology file missing: $TOPOLOGY"
  exit 1
fi

echo "Deploying RouteWise lab from $TOPOLOGY ..."
cd "$LAB_DIR"
containerlab deploy -t routewise.clab.yml

# Prevent Docker from restarting routers without recreating ContainerLab veth links.
for c in clab-routewise-r1 clab-routewise-r2 clab-routewise-r3 clab-routewise-fw1; do
  docker update --restart=no "$c" >/dev/null 2>&1 || true
done

echo "Lab deploy completed."
echo "Inspect with: docker ps --filter name=clab-routewise"
