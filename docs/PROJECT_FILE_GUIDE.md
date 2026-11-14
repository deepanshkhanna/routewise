# RouteWise — Project File Guide

Guide to the **actual** repository layout and how pieces connect. Paths are relative to the project root `cn/`.

---

## Top-level map

| Path | Purpose |
|------|---------|
| `README.md` | Setup, stack, topology summary |
| `docs/` | Architecture, API, audits, and this viva pack |
| `frontend/` | React + Vite dashboard |
| `backend/` | FastAPI app + pytest |
| `lab/` | ContainerLab YAML + FRR configs (+ generated clab state if deployed) |
| `scripts/` | start/deploy/dev helpers |
| `.agents/skills/` | Local agent skills (not runtime app code) |

---

## Documentation you should study

| File | Why it matters |
|------|----------------|
| `docs/PROJECT_EXPLANATION.md` | Full teaching narrative + honesty labels |
| `docs/TECHNICAL_ARCHITECTURE_WALKTHROUGH.md` | Data-flow journeys |
| `docs/PRESENTATION_SCRIPT.md` | What to say |
| `docs/LIVE_DEMO_RUNBOOK.md` | What to click |
| `docs/VIVA_QUESTIONS_AND_ANSWERS.md` | Defense Q&A |
| `docs/PROJECT_FILE_GUIDE.md` | This file |
| `docs/NETWORK_INFRASTRUCTURE.md` | Docker/WSL/lab facts |
| `docs/FIREWALL_IMPLEMENTATION.md` | Firewall status truth |
| `docs/END_TO_END_TEST_REPORT.md` | What was verified live |
| `docs/FINAL_ENGINEERING_REPORT.md` | Feature completion matrix |
| `docs/BUILD_STATUS.md` | Snapshot of pass/fail areas |

Older docs (`architecture.md`, `project-plan.md`, etc.) may describe intent; prefer code + engineering/E2E reports when they conflict.

---

## Backend — important files

### Entry and config

| File | Implements | Connects to |
|------|------------|-------------|
| `backend/app/main.py` | App factory, CORS, router include, DB seed on startup | All API routers, `NetworkService` |
| `backend/app/core/config.py` | Settings, router inventory, topology links constants, vtysh allow-list | `DockerService`, `RoutingService` |

### Database

| File | Implements | Why important |
|------|------------|---------------|
| `backend/app/db/models.py` | ORM: Network, Router, Link, Event, StaticRoute, FirewallRule | Persistence schema |
| `backend/app/db/session.py` | Engine, SessionLocal, init_db, get_db | Every DB-backed route |

### Schemas

| File | Role |
|------|------|
| `backend/app/schemas/network.py` | Paths, optimize, simulation, dashboard DTOs |
| `backend/app/schemas/router.py` | Lab/router/OSPF DTOs + protocol readiness |
| `backend/app/schemas/firewall.py` | Firewall DTOs |

### Services (core logic)

| File | Implements | Used by |
|------|------------|---------|
| `services/network_service.py` | Seed triangle, networks, links, routers, static routes, events | networks/dashboard/simulation/firewall |
| `services/path_engine.py` | Graph adjacency, DFS paths, lowest-cost | analysis routes |
| `services/optimizer.py` | Normalize + score S=… | `/optimize` |
| `services/simulation_service.py` | Link/router fail, software ping/traceroute | analysis routes |
| `services/routing_service.py` | Lab status, routes, OSPF, protocol readiness | routers/lab |
| `services/docker_service.py` | Allow-listed docker/vtysh | routing_service, providers |
| `services/wsl_bridge.py` | Run docker/clab via Windows or WSL | docker + containerlab provider |
| `services/firewall_service.py` | Rules, test, apply to fw1 | firewall routes |
| `services/providers/base.py` | Provider interface / modes | factory |
| `services/providers/software.py` | Software provider status | factory |
| `services/providers/containerlab.py` | Deploy/destroy/status | lab routes |
| `services/providers/factory.py` | `probe_infrastructure`, active provider | Settings UI, lab, firewall mode |

### API routes

| File | Endpoints area |
|------|----------------|
| `api/routes/health.py` | `/api/health` |
| `api/routes/dashboard.py` | `/api/dashboard/overview` |
| `api/routes/networks.py` | networks, routers, links, events, static-routes, seed |
| `api/routes/analysis.py` | paths, optimize, simulate, diagnostics |
| `api/routes/routers.py` | list routers, routes, ospf-neighbors |
| `api/routes/topology.py` | configured lab topology JSON |
| `api/routes/lab.py` | infrastructure, protocols, deploy/destroy/restart |
| `api/routes/firewall.py` | firewall CRUD/test/apply |

### Tests

| File | Covers |
|------|--------|
| `tests/test_health.py` | health/root |
| `tests/test_topology.py` | topology triangle |
| `tests/test_networks_and_paths.py` | seed, paths, optimize, disable, ping, dashboard |
| `tests/test_firewall.py` | firewall CRUD/test validation |
| `tests/test_docker_service.py` | allow-list, errors, bridge |
| `tests/test_routing_service.py` | lab status / routes parsing helpers |
| `tests/test_routers.py` | HTTP router endpoints with mocks |
| `tests/test_lab_api.py` | infrastructure/deploy shape |

---

## Frontend — important files

| File | Purpose |
|------|---------|
| `frontend/package.json` | Dependencies/scripts |
| `frontend/vite.config.js` | Dev server + `/api` proxy |
| `frontend/src/main.jsx` | React bootstrap |
| `frontend/src/App.jsx` | Routes + shell layout |
| `frontend/src/services/api.js` | **All** backend calls |
| `frontend/src/hooks/useNetworkLab.js` | Shared overview/network/lab loading |
| `frontend/src/components/layout/*` | Header, Sidebar, Page |
| `frontend/src/components/topology/TopologyCanvas.jsx` | React Flow graph |
| `frontend/src/components/topology/RouterNode.jsx` | Custom node |
| `frontend/src/pages/Dashboard.jsx` | Overview |
| `frontend/src/pages/TopologyPage.jsx` | Topology designer |
| `frontend/src/pages/RoutingPage.jsx` | Static routes + protocol badges |
| `frontend/src/pages/PathOptimizePages.jsx` | Path Explorer + Optimization |
| `frontend/src/pages/SimulationPage.jsx` | Link disable/restore demo |
| `frontend/src/pages/FirewallPage.jsx` | Firewall UI |
| `frontend/src/pages/SecondaryPages.jsx` | Analytics, Events, Reports, Settings |

---

## Lab — important files

| File | Purpose |
|------|---------|
| `lab/routewise.clab.yml` | Topology: r1/r2/r3 + optional fw1, three links |
| `lab/configs/r1/daemons` | Which FRR daemons start (ospfd/ripd/staticd/…) |
| `lab/configs/r1/frr.conf` | Interfaces, OSPF, RIP config for R1 |
| `lab/configs/r2/*`, `lab/configs/r3/*` | Same for R2/R3 |
| `lab/.gitattributes` | Keep FRR configs LF |
| `lab/clab-routewise/` | Generated by ContainerLab when deployed (runtime artifact) |

---

## Scripts

| File | Purpose |
|------|---------|
| `scripts/dev.ps1` | status / backend / frontend / lab-deploy / lab-status helpers |
| `scripts/start_backend.sh` / `start_frontend.sh` | Unix-style starters |
| `scripts/deploy_lab.sh` / `destroy_lab.sh` | Lab lifecycle |
| `scripts/check_environment.sh` | Env probe |

---

## Main execution flows

### Creating / ensuring a network

1. Backend startup → `seed_default_triangle()`  
   **or** `POST /api/networks` / `POST /api/networks/seed-default`
2. Rows in `networks`, `routers`, `links`, seed `events`
3. Frontend `useNetworkLab` / `getNetwork` loads it for pages

**Key files:** `network_service.py`, `networks.py`, `useNetworkLab.js`

### Saving topology changes

- Add router: `POST /api/networks/{id}/routers`
- Add link: `POST /api/networks/{id}/links`
- Persisted via SQLAlchemy commit; Topology page refresh shows React Flow update

**Note:** Canvas editing UX is present; treat advanced designer features as incremental vs a full commercial editor.

### Exploring a route

1. UI Path Explorer → `api.getPaths`
2. `analysis.explore_paths` → `PathEngine`
3. Response drives highlight + table

**Key files:** `PathOptimizePages.jsx`, `analysis.py`, `path_engine.py`

### Optimization recommendation

1. UI Optimization → `api.optimizePath`
2. `PathEngine` candidates → `optimizer.recommend`
3. UI shows score breakdown + explanation

**Key files:** `optimizer.py`, `analysis.py`, `PathOptimizePages.jsx`

### Disabling / restoring a link

1. Simulation buttons → `api.disableLink` / `enableLink`
2. `SimulationService.set_link_state`
3. Event row written; frontend reloads network + paths

**Key files:** `SimulationPage.jsx`, `simulation_service.py`, `analysis.py`

### Deploying the actual network lab

1. Settings Deploy → `POST /api/lab/deploy`
2. `ContainerLabProvider.deploy` → `clab deploy -t lab/routewise.clab.yml` via `wsl_bridge`
3. Containers `clab-routewise-r1|r2|r3` running → `active_mode=REAL_LAB`
4. Optional: `RoutingService` vtysh reads; firewall apply → `fw1`

**Key files:** `lab.py`, `providers/containerlab.py`, `routewise.clab.yml`, `Settings` in `SecondaryPages.jsx`

---

## Suggested study order (files)

1. `README.md`  
2. `backend/app/main.py`  
3. `backend/app/db/models.py`  
4. `network_service.py` → `path_engine.py` → `optimizer.py` → `simulation_service.py`  
5. `api/routes/analysis.py` + `networks.py`  
6. `routing_service.py` + `docker_service.py` + `providers/factory.py`  
7. `lab/routewise.clab.yml` + `lab/configs/r1/frr.conf` + `daemons`  
8. `frontend/src/App.jsx` + `api.js` + Path/Simulation/Routing/Settings pages  
9. `firewall_service.py` + firewall docs  
10. `backend/tests/test_networks_and_paths.py` + E2E report  

---

## Quick “where is X?” index

| Question | Look here |
|----------|-----------|
| Score formula | `optimizer.py` |
| DFS paths | `path_engine.py` |
| Seed metrics | `network_service.py` (`seed_default_triangle`) |
| Link fail | `simulation_service.py` |
| OSPF parse | `routing_service.py` |
| Mode badge | `Sidebar.jsx` + `factory.probe_infrastructure` |
| FRR enable flags | `lab/configs/*/daemons` |
| Triangle wiring | `lab/routewise.clab.yml` |
| Firewall apply target | `firewall_service.py` (`FW_CONTAINER`) |
