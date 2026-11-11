# RouteWise — Final Engineering Report

## A. Initial state

Working FastAPI + React app with SQLite simulation (paths, optimize, link failure, events). Docker Desktop Windows engine often down; ContainerLab/FRR not previously verified. UI modules present but Firewall incomplete; no provider abstraction.

## B. Bugs discovered and fixed

1. **CRLF in FRR configs** → ospfd failed to start; converted to LF.
2. **Windows Docker pipe** mis-used as sole engine → WSL bridge for docker/clab.
3. **Lab API returned wrong shape** → deploy/destroy map `LabStatus`.
4. **Firewall table missing** on first pytest run → `create_all` after model add.
5. **WSL subprocess UTF-8 / None stdout** → encoding=`utf-8`, errors=`replace`.

## C. UI modules

| Module | Status |
|--------|--------|
| Overview | Live |
| Topology Designer | Live (React Flow + network API) |
| Routing Manager | Live |
| Path Explorer | Live |
| Optimization | Live |
| Simulation Lab | Live (software; real link ops via provider) |
| Firewall & Security | **Added** — rules, test, mode badge |
| Analytics | Present (charts labeled illustrative where synthetic) |
| Events & Alerts | Live |
| Reports | Live export |
| Settings & Lab | **Extended** — infra probe, deploy/destroy |

## D. Browser / FE

Frontend remains on `:5173`. Sidebar shows live `active_mode`. Playwright multi-viewport capture not executed this pass.

## E. Backend changes

- `services/providers/*`, `wsl_bridge.py`
- `firewall_service.py`, schemas, routes
- `api/routes/lab.py`, `firewall.py` registered in `main.py`
- `FirewallRule` model

## F. Database

New table: `firewall_rules`.

## G–H. Docker / ContainerLab / FRR

**IMPLEMENTED AND VERIFIED IN REAL LAB** — clab 0.83.0, three FRR nodes, OSPF Full.

## I. Static routing

**IMPLEMENTED BUT NOT VERIFIED** as a primary demo — `staticd=yes`; demo used OSPF.

## J. RIP

**NOT IMPLEMENTED** in real lab (`ripd=no`). Software path protocol selection remains.

## K. OSPF

**IMPLEMENTED AND VERIFIED IN REAL LAB** — neighbors, routes, ping, failover.

## L. BGP

**NOT IMPLEMENTED** (`bgpd=no`).

## M. Firewall

| Aspect | Classification |
|--------|----------------|
| Policy CRUD + test | IMPLEMENTED AND VERIFIED IN SOFTWARE SIMULATION |
| Host isolation | VERIFIED (no host firewall changes) |
| nftables on `fw1` + apply API | IMPLEMENTED AND VERIFIED IN REAL LAB |
| nftables on FRR router images | NOT IMPLEMENTED (use fw1) |

## N. Failover demonstration

**IMPLEMENTED AND VERIFIED IN REAL LAB** — eth2 down → path R1→R2→R3; restore brings adjacency back.

## O. Remaining limitations

- nftables package install inside lab intermittently fails (Alpine CDN).
- Docker Desktop Windows engine may still be down; WSL path required.
- BGP/RIP real configs not shipped.
- Full Playwright E2E matrix outstanding.

## P. Startup

```powershell
.\scripts\dev.ps1 status
.\scripts\dev.ps1 backend    # no-op if :8000 up
.\scripts\dev.ps1 frontend   # no-op if :5173 up
.\scripts\dev.ps1 lab-deploy # WSL ContainerLab
```

Backend: `http://127.0.0.1:8000`  
Frontend: `http://127.0.0.1:5173`

## Q. Tests

- Backend: **32 passed**
- Real lab OSPF + failover: **passed** (command evidence in `END_TO_E2E` / `END_TO_END_TEST_REPORT.md`)
- Frontend production build: run `npm run build` in `frontend/`
