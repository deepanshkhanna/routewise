#!/usr/bin/env bash
# Start the FastAPI backend (does not deploy the lab).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/backend"

if [[ ! -d .venv ]]; then
  echo "ERROR: backend/.venv not found. Create it with:"
  echo "  cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# shellcheck disable=SC1091
if [[ -f .venv/Scripts/activate ]]; then
  # Git Bash on Windows
  source .venv/Scripts/activate
elif [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
else
  echo "ERROR: Cannot find venv activate script"
  exit 1
fi

echo "Starting RouteWise API on http://0.0.0.0:8000 ..."
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
