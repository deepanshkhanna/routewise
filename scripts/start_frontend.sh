#!/usr/bin/env bash
# Start the Vite React frontend.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/frontend"

if [[ ! -d node_modules ]]; then
  echo "ERROR: frontend/node_modules missing. Run: cd frontend && npm install"
  exit 1
fi

echo "Starting RouteWise frontend on http://localhost:5173 ..."
exec npm run dev -- --host 127.0.0.1 --port 5173
