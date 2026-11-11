# Architecture

## Purpose

RouteWise separates the operator UI, control plane, and routing lab so students can explore OSPF behavior without touching the host OS routing table.

## Layers

### 1. Presentation (frontend)

- React SPA built with Vite
- Communicates only with FastAPI over REST
- Shows health, lab status, topology, and router tables
- Displays loading / error states when the lab is offline

### 2. Control plane (backend)

- FastAPI application under `backend/app`
- CORS limited to the local Vite origin (`http://localhost:5173`)
- Services wrap Docker CLI and fixed `vtysh` show commands
- Router IDs are allow-listed: `R1`, `R2`, `R3`
- Timeouts and structured errors prevent hanging or crashing the API

### 3. Data plane lab (simulation)

- ContainerLab topology `routewise`
- Three FRR containers in a triangle
- OSPF area 0 advertises loopbacks and link subnets
- Image: `quay.io/frrouting/frr:containerlab-10.7.1`

## Trust and safety boundaries

| Boundary | Rule |
|----------|------|
| Browser → API | JSON REST only |
| API → Docker | Predefined command templates only |
| Lab → Host | No host route injection; Docker/WSL isolation |
| User input | Path params validated against allow-list |

## Request flow

1. Dashboard loads and calls `/api/health` and `/api/lab/status`.
2. If the lab is up, it calls `/api/routers` and related detail endpoints.
3. Backend maps `R1` → container `clab-routewise-r1` (and similarly for R2/R3).
4. Backend runs `docker inspect` / `docker exec ... vtysh -c "show ..."`.
5. Output is parsed into Pydantic response models for the UI.

## Failure modes

- Docker daemon unavailable → lab status reports offline with a clear message
- Container missing → router marked unavailable; endpoints return useful status payloads
- Command timeout → timed-out error, no process hang
- Invalid router id → HTTP 400

## Extensibility (later milestones)

- Path-cost visualization from OSPF LSDB
- Historical snapshots of route tables
- Read-only policy annotations (no write APIs in v1)
