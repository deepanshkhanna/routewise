#!/usr/bin/env bash
# Destroy the ContainerLab FRR topology.
# Does NOT modify the Windows host routing table.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAB_DIR="$ROOT/lab"
TOPOLOGY="$LAB_DIR/routewise.clab.yml"

if ! command -v containerlab >/dev/null 2>&1; then
  echo "ERROR: containerlab not found on PATH."
  exit 1
fi

if [[ ! -f "$TOPOLOGY" ]]; then
  echo "ERROR: Topology file missing: $TOPOLOGY"
  exit 1
fi

echo "Destroying RouteWise lab ..."
cd "$LAB_DIR"
containerlab destroy -t routewise.clab.yml --cleanup
echo "Lab destroyed."
