# RouteWise Implementation Plan

## Pre-sprint audit summary

Existing strengths: FastAPI health/lab/router inspect APIs, FRR ContainerLab configs, React dashboard shell.

Gaps closed this sprint: SQLite persistence, topology seed, path engine, optimization scoring, failure simulation, diagnostics, dashboard aggregate, frontend wiring for Path/Optimize/Simulation/Events.

## Completed phases

### Phase A — Persistence foundation ✅
- SQLAlchemy SQLite models + seed triangle
- `/api/networks*` CRUD subset

### Phase B — Path / optimize / failure ✅
- Path enumeration + lowest-cost protocol-selected path
- Scoring `S = 0.35L + 0.25P + 0.20H + 0.20C`
- Link disable/restore with events

### Phase C — Diagnostics + dashboard ✅
- Ping/traceroute labeled `software_simulation`
- `/api/dashboard/overview`

### Phase D — Frontend wiring ✅ (minimal)
- Dashboard consumes overview
- ControlPlane pages for Path/Optimize/Sim/Events

### Phase E — Verify ✅
- 28 backend tests passed
- Frontend production build passed

## Next phases (remaining)

1. Install ContainerLab in WSL and deploy `lab/routewise.clab.yml`
2. Bridge simulation actions to real FRR/vtysh where safe
3. React Flow topology designer (TS/Tailwind optional migration)
4. RIP/OSPF configuration write path
5. WebSocket live updates + reports export
