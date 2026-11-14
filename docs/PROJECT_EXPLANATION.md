# RouteWise — Complete Project Explanation

> Source of truth: repository code and verified lab reports as of the current tree.  
> Do **not** treat the original proposal as a completion checklist.  
> Status labels used below: **Fully implemented** · **Software-simulated** · **Real network (FRR/ContainerLab)** · **Partial** · **Planned** · **Environment-blocked**.

---

## 1. Project introduction

**RouteWise** is an intelligent routing management and network path optimization system built as a Computer Networks course project.

It combines:

1. A **React + Vite** operations dashboard.
2. A **FastAPI** control-plane API.
3. A **SQLite** persisted topology used for software pathfinding, optimization, failure simulation, events, static routes, and firewall policy.
4. An optional **Docker / WSL2 / ContainerLab / FRRouting** lab that runs a real three-router OSPF triangle (R1–R2–R3), with RIPv2 also configured in FRR files and BGP disabled.

Students and evaluators can:

- Inspect a triangle topology visually.
- Explore candidate paths and a “protocol-selected” (lowest-cost) path in software.
- Run a weighted recommendation score `S = 0.35L + 0.25P + 0.20H + 0.20C`.
- Disable/restore links in the software topology and watch alternate paths appear.
- When the lab is deployed, read real FRR routing tables and OSPF neighbors via allow-listed `docker exec … vtysh` commands.
- Manage lab-isolated firewall rules (SQLite + software test; optional nftables apply on `fw1`).

**What RouteWise is not**

- Not a production SDN controller.
- Not a replacement for Cisco/Juniper management suites.
- Not a system that modifies the Windows host routing table or Windows Defender Firewall.
- Not a claim that every UI chart is live telemetry (Analytics uses illustrative/synthetic demo data).

---

## 2. Problem statement

Enterprise and campus networks depend on routing protocols (static, RIP, OSPF, BGP) to forward traffic. Students and operators often struggle to:

- See how topology, link metrics, and failures affect path choice.
- Distinguish “shortest by protocol cost” from “better under latency/loss/hops trade-offs.”
- Practice failure recovery safely without breaking a physical network.
- Inspect real FRR/OSPF behavior without issuing arbitrary shell commands on the host.

---

## 3. Existing system (traditional approaches)

Without RouteWise, a course lab typically uses:

- Manual CLI on physical routers or VMs.
- Packet tracers / simulators disconnected from a modern UI.
- Ad-hoc scripts with no clear safety boundary around Docker/`vtysh`.
- Separate tools for topology drawing, route inspection, and failure demos.

---

## 4. Limitations of existing approaches

- Hard to visualize path candidates and scoring side-by-side.
- Easy to accidentally change host networking if Docker commands are unconstrained.
- Difficulty explaining *why* a path was recommended vs what OSPF/cost would prefer.
- Failover demos require careful CLI work and are hard to replay for viva.

---

## 5. Proposed / built system

RouteWise provides a **dual-mode** architecture:

| Mode | Meaning | When active |
|------|---------|-------------|
| `SOFTWARE_SIMULATION` | Paths, optimize, link fail/restore, ping/traceroute, events, static routes, firewall test — all over SQLite topology | Always available when backend is up |
| `REAL_LAB` | ContainerLab FRR containers running; routes/OSPF (and RIP probe) via Docker/`vtysh` | When R1/R2/R3 containers are all `running` |
| `UNAVAILABLE` (lab side) | Docker/ContainerLab missing or lab not deployed | App still works in software mode |

Provider selection: `backend/app/services/providers/factory.py` (`probe_infrastructure`, `get_active_provider`).

---

## 6. Project objectives

1. Model a three-router triangular topology matching the ContainerLab design.
2. Persist topology and events in SQLite for reproducible demos.
3. Compute all simple paths and a lowest-cost “protocol-selected” path.
4. Score candidates with an explainable weighted formula.
5. Simulate link/router failures and log events.
6. Optionally deploy/inspect a real FRR OSPF lab without touching host routing.
7. Keep Docker/`vtysh` commands allow-listed and safe.
8. Provide a dashboard suitable for presentation and viva.

---

## 7. Main features (what we actually built)

### 7.1 Dashboard / Overview — **Fully implemented** (metrics from SQLite)

- Route: `/`
- API: `GET /api/dashboard/overview`
- Shows router/link counts, failed links, recent events, lab running flag.
- Explicitly labeled `data_source=software_simulation`.

### 7.2 Topology Designer — **Fully implemented** (canvas + persisted network)

- Route: `/topology`
- React Flow canvas (`TopologyCanvas`, `RouterNode`).
- Data from `GET /api/networks/{id}` (seeded triangle on startup).
- Advanced interactive add/delete UX is incremental (existing canvas + inspector style), not a full commercial designer.

### 7.3 Routing Manager — **Partial / dual source**

- Route: `/routing`
- **Static routes**: CRUD-style add/list in SQLite — **software-simulated** (`/api/networks/{id}/static-routes`). Saving a static route does **not** push into FRR automatically.
- **Protocol readiness**: `GET /api/lab/protocols` probes Static (DB), RIP, OSPF, BGP status badges.
- **Live FRR routes/neighbors**: available via `GET /api/routers/{R1|R2|R3}/routes` and `…/ospf-neighbors` when containers run.

### 7.4 Path Explorer — **Software-simulated** (fully implemented)

- Route: `/paths`
- API: `GET /api/networks/{id}/paths?source=&destination=`
- DFS enumeration of simple paths; protocol-selected = lowest total link cost.
- Message in API states: not FRR FIB data.

### 7.5 Optimization — **Software-simulated** (fully implemented)

- Route: `/optimize`
- API: `GET /api/networks/{id}/optimize?source=&destination=`
- Formula implemented in `backend/app/services/optimizer.py`.

### 7.6 Simulation Lab — **Software-simulated** (fully implemented)

- Route: `/simulation`
- Disable/enable links via `POST …/simulate/links/{link_id}/disable|enable`.
- Updates SQLite `links.enabled` / `status`, writes `events`, recomputes R1→R3 path in UI.
- Separate from real FRR interface shutdown demos (those were verified manually with `ip link set eth2 down` inside containers — see `docs/END_TO_END_TEST_REPORT.md`).

### 7.7 Firewall & Security — **Software + optional real fw1**

- Route: `/firewall`
- SQLite rules + first-match software test — **verified in software**.
- `POST …/firewall/apply` pushes allow-listed nftables fragments into `clab-routewise-fw1` when REAL_LAB — **verified in real lab** for fw1.
- nftables on FRR router images — **not implemented** (no nft binaries in FRR image).
- Host Windows firewall — **never modified**.

### 7.8 Analytics — **Illustrative / synthetic UI**

- Route: `/analytics`
- Charts and availability numbers are demo visuals, not live Prometheus metrics.

### 7.9 Events & Alerts — **Fully implemented** (SQLite events)

- Route: `/events`
- API: `GET /api/networks/{id}/events`

### 7.10 Reports — **Fully implemented** (export-style UI over current overview/network)

- Route: `/reports`

### 7.11 Settings & Lab — **Fully implemented** (lifecycle + infra probe)

- Route: `/settings`
- `GET /api/lab/infrastructure`, `POST /api/lab/deploy|destroy|restart`
- Sidebar shows live `active_mode`.

### 7.12 Real network infrastructure — **Implemented; OSPF verified**

- Topology: `lab/routewise.clab.yml`
- FRR configs under `lab/configs/r{1,2,3}/`
- Daemons currently: `zebra=yes`, `ospfd=yes`, `ripd=yes`, `staticd=yes`, `bgpd=no`
- OSPF Full mesh + ping + failover: **verified** (engineering / E2E docs).
- RIP: **configured in lab files** and probeable via Routing Manager / `RoutingService._probe_rip_status`; treat as configured and probeable, with OSPF as the primary verified protocol demo.
- BGP: **planned / not enabled**.

---

## 8. Technology stack

| Layer | Technology |
|-------|------------|
| Frontend | React, Vite, JavaScript, React Router, React Flow, Lucide icons, CSS |
| Backend | Python, FastAPI, Pydantic v2, SQLAlchemy, uvicorn |
| Database | SQLite (created via SQLAlchemy `create_all`) |
| Lab | Docker (preferably WSL2 engine), ContainerLab, FRRouting `quay.io/frrouting/frr:containerlab-10.7.1` |
| Firewall helper | Alpine `fw1` + nftables (optional node) |
| Tests | pytest (mocked Docker; no real LLM; lab optional) |

---

## 9. System architecture (summary)

```
Browser React (:5173)
    │  fetch /api/*  (Vite proxy → :8000)
    ▼
FastAPI (app.main)
    ├── SQLite services: NetworkService, PathEngine, optimizer, SimulationService, FirewallService
    ├── RoutingService + DockerService (allow-listed docker/vtysh)
    └── providers: SoftwareSimulationProvider | ContainerLabProvider
            │
            ▼ (when deployed)
     WSL Docker → clab-routewise-r1/r2/r3 (+ optional fw1)
```

---

## 10. Database design

Models in `backend/app/db/models.py`:

| Table | Purpose |
|-------|---------|
| `networks` | Named topology containers |
| `routers` | Name, loopback, router_id, status, protocol |
| `links` | Endpoints, subnet, IPs, cost, bandwidth, latency, loss, enabled/status |
| `events` | Severity, category, description, `data_source` |
| `static_routes` | Per-router destination / next_hop / metric (DB only unless manually applied to FRR) |
| `firewall_rules` | allow/deny, protocol, endpoints, port, priority, hit_count |

Default seed (`NetworkService.seed_default_triangle`): network **"RouteWise Triangle Lab"** with R1/R2/R3 and three links matching lab subnets, with asymmetric metrics:

| Link | Subnet | Cost | Latency | Loss |
|------|--------|------|---------|------|
| R1–R2 | 10.0.12.0/30 | 10 | 8 ms | 0.5% |
| R2–R3 | 10.0.23.0/30 | 10 | 9 ms | 1.0% |
| R1–R3 | 10.0.13.0/30 | 15 | 4 ms | 0.0% |

---

## 11. Frontend architecture

- Entry: `frontend/src/main.jsx` → `App.jsx`
- Shared lab/network state: `hooks/useNetworkLab.js`
- API client: `services/api.js` (same-origin `/api`, timeout, JSON)
- Layout: `Header`, `Sidebar` (mode badge), `Page`
- Pages map 1:1 to product modules listed in §7
- Topology: React Flow in `components/topology/*`

---

## 12. Backend architecture

- Entry: `backend/app/main.py` — CORS, routers, startup seed
- Config: `app/core/config.py` — inventory, allow-listed vtysh commands, CORS
- DB session: `app/db/session.py`
- API packages: `health`, `lab`, `routers`, `topology`, `networks`, `analysis`, `dashboard`, `firewall`
- Services: network, path_engine, optimizer, simulation, routing, docker, firewall, wsl_bridge, providers

---

## 13. Routing implementation

### Software control plane

- Graph adjacency from enabled/`up` links and `up` routers (`PathEngine`).
- “Protocol-selected path” in the UI/API means **lowest summed link `cost`** among simple paths — a teaching proxy for cost-based selection, **not** a live OSPF SPF dump unless you separately call FRR route APIs.

### Real FRR lab

- OSPF area 0 on loopbacks and point-to-point links (`lab/configs/*/frr.conf`).
- Live inspection: `show ip route [json]`, `show ip ospf neighbor [json]`.
- Static daemon enabled (`staticd=yes`); app static routes live in SQLite by default.
- RIP v2 configured (`router rip` / `ripd=yes`); BGP off.

---

## 14. Optimization algorithm

File: `backend/app/services/optimizer.py`

1. Take available candidate paths from `PathEngine`.
2. Collect raw metrics: total latency, average packet loss, hop count, total cost.
3. Min–max normalize each metric to 0..100 (higher raw → higher/worse).
4. Score: **S = 0.35L + 0.25P + 0.20H + 0.20C**
5. Lowest S wins.
6. Explanation compares recommendation vs protocol-selected path and states `data_source=software_simulation`.

### Worked example (default seed, R1 → R3)

**Candidates**

| Path | Latency | Avg loss | Hops | Cost |
|------|---------|----------|------|------|
| A: R1 → R3 | 4 | 0.0 | 1 | 15 |
| B: R1 → R2 → R3 | 17 | 0.75 | 2 | 20 |

**Normalization** (for each metric: `((v - min) / (max - min)) * 100`)

| | L | P | H | C |
|--|---|---|---|---|
| A | 0 | 0 | 0 | 0 |
| B | 100 | 100 | 100 | 100 |

**Scores**

- S_A = 0  
- S_B = 100  

**Recommended:** R1 → R3 (score 0)  
**Protocol-selected (lowest cost):** also R1 → R3 (cost 15 < 20)

Under the default seed they **agree**. They would **differ** if cost favored the longer path while latency/loss/hops favored the direct path strongly enough that weighted S preferred the direct path — the API explanation text covers that case.

Unavailable links are excluded from the adjacency list (`enabled` false or `status != "up"`, or endpoint router down), so failed links never appear in candidates.

---

## 15. Network failure simulation

**Software (UI Simulation Lab)**

1. `POST /api/networks/{id}/simulate/links/{link_id}/disable`
2. Link marked `enabled=false`, `status=down`
3. Event logged (`data_source=software_simulation`)
4. Path Explorer / Simulation recomputes; e.g. disable R1–R3 → path becomes R1 → R2 → R3

**Real lab (verified separately)**

- `ip link set eth2 down` on R1 inside container
- OSPF withdraws direct neighbor; traffic via R2
- Restore interface → adjacency returns

Do **not** claim the Simulation Lab button runs `ip link` inside FRR unless you wire that provider path and show it; current Simulation page uses the software APIs.

---

## 16. Real network infrastructure

| Component | Role |
|-----------|------|
| Docker / WSL bridge | Execute docker/clab without exposing unauthenticated Docker TCP |
| ContainerLab | Orchestrate topology from `routewise.clab.yml` |
| FRR R1/R2/R3 | Real OSPF (+ configured RIP) routing |
| fw1 Alpine | Isolated nftables apply target |
| Management net | Lab-internal (e.g. `172.20.20.0/24`); host OS routes untouched |

---

## 17. Firewall implementation

| Capability | Status |
|------------|--------|
| Rule CRUD in SQLite | Fully implemented |
| First-match software test + hit_count | Fully implemented / verified in software |
| Apply to `clab-routewise-fw1` | Implemented / verified in real lab when lab up |
| nftables on FRR nodes | Not implemented |
| Stateful inspection like a commercial NGFW | Not claimed — simple filter rules + counters |
| Host firewall changes | Forbidden by design |

---

## 18. Security considerations

- Frontend never talks to Docker.
- Backend rejects non-allow-listed `vtysh` commands and non-docker argv.
- Only known router containers (`clab-routewise-r1/r2/r3`) are inspected.
- Validation errors return generic 422; unexpected errors return generic 500 (details logged server-side).
- Firewall apply uses argv fragments, not shell string interpolation.
- CORS limited to configured origins; methods GET/POST/DELETE/OPTIONS.

---

## 19. Testing and results

| Suite | Result (as documented in repo) |
|-------|--------------------------------|
| Backend pytest | **32 passed** (`docs/BUILD_STATUS.md`, `END_TO_END_TEST_REPORT.md`) |
| Path/optimize/disable/ping | Covered in `test_networks_and_paths.py` |
| Docker allow-list / errors | `test_docker_service.py`, `test_routing_service.py`, `test_routers.py` |
| Firewall CRUD/test | `test_firewall.py` |
| Lab API mocks | `test_lab_api.py` |
| Real OSPF + failover | Verified in E2E report when lab deployed |
| Playwright UI matrix | Not run / outstanding |

---

## 20. Limitations and future scope

**Limitations (honest)**

- Path Explorer / Optimize / Simulation ping & traceroute are **software graph** operations.
- Analytics numbers are illustrative.
- Static routes in UI are DB records unless separately applied to FRR.
- BGP not implemented (`bgpd=no`).
- Windows Docker Desktop pipe may be down; WSL Docker path is required in practice.
- Topology designer is not a full commercial editor.
- FRR image lacks nftables; firewall real apply uses `fw1` only.

**Future scope**

- Push static routes into FRR via controlled API.
- Deeper RIP/BGP lab scenarios and verification packs.
- Wire Simulation Lab optional “real interface down” actions through provider.
- Live metrics instead of illustrative analytics.
- Broader Playwright E2E matrix.

---

## Feature deep-dives (quick reference)

For each major feature: what / why / how / tech / files / APIs / UI / tests.

### Path exploration

- **What:** Lists candidate paths and lowest-cost path.
- **Why:** Teach multipath awareness and cost selection.
- **How:** Undirected adjacency + DFS simple paths (`max_depth=6`).
- **Tech:** Python `PathEngine`, Pydantic `CandidatePath`.
- **Files:** `path_engine.py`, `analysis.py`, `PathOptimizePages.jsx`.
- **API:** `GET /api/networks/{id}/paths`
- **UI:** Path Explorer — canvas highlight + candidate table.
- **Tests:** `test_paths_and_optimize`

### Optimization

- **What:** Weighted score recommendation with breakdown.
- **Why:** Separate multi-metric quality from pure cost.
- **How:** Normalize + weighted sum; lower better.
- **Files:** `optimizer.py`, `analysis.py`, Optimization page.
- **API:** `GET /api/networks/{id}/optimize`
- **Tests:** same as paths.

### Link failure simulation

- **What:** Disable/restore link in DB; recompute paths.
- **Why:** Safe failover teaching without host risk.
- **Files:** `simulation_service.py`, `SimulationPage.jsx`
- **API:** `…/simulate/links/{id}/disable|enable`
- **Tests:** `test_disable_link_changes_availability`

### FRR inspection

- **What:** Read routes and OSPF neighbors from containers.
- **Why:** Show real protocol state beside simulation.
- **Files:** `routing_service.py`, `docker_service.py`, `wsl_bridge.py`
- **API:** `/api/routers/{id}/routes`, `/ospf-neighbors`, `/api/lab/status`
- **Tests:** mocked in `test_routers.py` / `test_routing_service.py`

### Lab lifecycle

- **What:** Deploy/destroy/restart ContainerLab topology.
- **Files:** `providers/containerlab.py`, `api/routes/lab.py`, Settings page
- **API:** `/api/lab/deploy|destroy|restart|infrastructure`

### Firewall

- **What:** Policy store, software evaluate, optional fw1 apply.
- **Files:** `firewall_service.py`, `FirewallPage.jsx`, `lab/routewise.clab.yml` (`fw1`)
- **API:** `/api/networks/{id}/firewall/*`
- **Tests:** `test_firewall.py` + real-lab notes in firewall docs
