# RouteWise — Presentation Script

Speak naturally. Short sentences. Show the UI when the script says **[SHOW:]**.  
Do not claim software path scoring is live OSPF. If the lab is down, use the software demo and say so honestly.

---

## A. One-minute introduction

Good morning. Our project is **RouteWise** — an intelligent routing management and path optimization system for computer networks.

We built a React dashboard and a FastAPI backend that manage a three-router triangular topology — R1, R2, and R3. The same addressing is used in a Docker ContainerLab with FRRouting, so we can study both **software path analysis** and **real OSPF behavior**.

The problem we address is simple: routing decisions are hard to see. When a link fails, students need a safe way to observe alternate paths and understand the difference between lowest protocol cost and a multi-metric recommendation.

In one minute: RouteWise helps you **visualize topology, explore paths, score alternatives, simulate failures, and optionally inspect live FRR routes** — without touching the Windows host routing table.

---

## B. Three-minute project explanation

**[SHOW: Overview `/`]**

RouteWise has two layers that work together.

First, a **software control plane**. Topology, link metrics, events, static routes, and firewall policies live in SQLite. From that graph we compute all simple paths between two routers, pick the lowest-cost path as a teaching stand-in for protocol selection, and run an optimization score:

S = 0.35×latency + 0.25×packet loss + 0.20×hop count + 0.20×routing cost, after normalization. Lower score is better.

**[SHOW: Path Explorer `/paths` — Trace R1 to R3]**

Here you see the direct path and the path via R2, with cost and latency.

**[SHOW: Simulation Lab `/simulation` — disable R1–R3, then restore]**

When we disable the direct link, traffic logically moves to R1 → R2 → R3. That failure demo is safe because it updates the database graph used by the app.

Second, an optional **real lab**. Using ContainerLab we run three FRR containers. When they are up, the API can read real routing tables and OSPF neighbors through allow-listed Docker commands. Our verified demo focuses on **OSPF area 0**. RIP is configured in the lab files; BGP is not enabled.

**[SHOW: Settings — infrastructure mode badge REAL_LAB or SOFTWARE_SIMULATION]**

If Docker is unavailable, the software features still work. We designed graceful degradation on purpose.

That is RouteWise: a teaching-grade routing lab with a clear boundary between simulation and real FRR.

---

## C. Full 8–10 minute presentation

### 0:00–0:45 — Opening

Faculty, our project title is RouteWise: Intelligent Routing Management and Network Path Optimization.

I will cover the problem, what we built, the architecture, a live walkthrough, and honest limitations.

### 0:45–1:30 — Problem and motivation

In networks, routers forward packets using routing tables filled by static configuration or dynamic protocols such as RIP and OSPF. When a link fails, protocols reconverge and pick another path. That process is powerful — but difficult to demonstrate clearly in a short viva if you only have CLI snippets.

We wanted one system that can:

1. Show the topology visually.  
2. Compare candidate paths.  
3. Explain a recommendation with weights.  
4. Simulate failure safely.  
5. Optionally prove the same triangle works with real FRR OSPF.

### 1:30–2:30 — Existing vs proposed

Existing approach: manual CLI, disconnected simulators, risky unrestricted shell access to Docker.

Proposed system: React UI → FastAPI → SQLite software plane, plus optional ContainerLab FRR lab. The frontend never talks to Docker. The backend only runs fixed inspection commands.

### 2:30–3:30 — Objectives and stack

**[SHOW: Overview metrics]**

Objectives: topology management, path exploration, optimization, failure simulation, FRR inspection, lab-isolated firewall policies, and tests.

Stack: React + Vite, FastAPI, SQLAlchemy/SQLite, Docker/WSL, ContainerLab, FRRouting.

### 3:30–5:00 — Architecture

**[SHOW: Settings / lab mode]**

Architecture has clear layers:

- UI pages for each workflow.  
- `api.js` as the only frontend network client.  
- FastAPI routers calling services.  
- `PathEngine` and `optimizer` for software analysis.  
- `RoutingService` + `DockerService` for FRR.  
- Provider factory choosing SOFTWARE_SIMULATION vs REAL_LAB.

Database tables: networks, routers, links, events, static_routes, firewall_rules.

Default seed matches lab subnets: 10.0.12.0/30, 10.0.23.0/30, 10.0.13.0/30, with loopbacks 192.168.1.1, .2.2, .3.3.

### 5:00–7:00 — Live walkthrough (core)

**[SHOW: Topology Designer]**  
Three routers, three links — a classic triangle with redundant paths.

**[SHOW: Routing Manager]**  
Static routes are stored in SQLite for the software plane. Protocol badges show Static, RIP, OSPF, BGP readiness. OSPF becomes operational when the lab reports Full neighbors.

**[SHOW: Path Explorer — Trace path]**  
Say: “These candidates come from our graph engine. The protocol-selected path is the lowest total configured cost. This is software_simulation, not a live FIB dump.”

**[SHOW: Optimization]**  
Explain S = 0.35L + 0.25P + 0.20H + 0.20C. Normalization makes metrics comparable. Lowest score wins. Mention that under the default seed, recommendation and lowest-cost path both prefer R1→R3, but the engines are still different.

**[SHOW: Simulation — disable R1–R3]**  
“Direct path disappears; alternate path appears; an event is logged.”

**[SHOW: restore link]**  
“Path returns.”

**[SHOW: Events]**  
Point to severity and `data_source=software_simulation`.

### 7:00–8:30 — Real lab and firewall (honest)

**[SHOW: Settings infrastructure]**  
If REAL_LAB: “Containers R1 R2 R3 are running. We can query `show ip route` and OSPF neighbors through the API.”

If not: “Lab is not deployed right now, so we demonstrate software mode. That is an intentional fallback.”

**[SHOW: Firewall]**  
“Rules live in SQLite. Test uses a first-match software policy engine and never changes Windows Firewall. Apply targets an isolated Alpine fw1 node when the lab is up — not the FRR image, which has no nftables.”

### 8:30–9:30 — Testing and security

We have about 32 backend pytest cases covering health, topology, paths, optimize, link disable, firewall, and Docker allow-listing with mocks. Real OSPF Full adjacency and failover were verified in the lab report when ContainerLab was deployed.

Security highlights: allow-listed vtysh, no arbitrary shell from clients, host routing untouched.

### 9:30–10:00 — Limitations and close

Limitations: Analytics charts are illustrative; path optimize is software; BGP not implemented; static routes in UI are not auto-pushed to FRR; Windows Docker may require WSL bridge.

Future work: push controlled configs to FRR, richer RIP/BGP scenarios, optional real interface-down from the Simulation UI, live telemetry.

Thank you. We are ready for questions.

---

## D. Closing statement (15–20 seconds)

RouteWise brings routing concepts into one place: a visual topology, explainable path scoring, safe failure simulation, and an optional real FRR OSPF lab — with a clear line between what is simulated and what is executed on the network. Thank you.

---

## Memorization cues (cheat sheet)

| Minute | Topic | Page |
|--------|-------|------|
| 0 | Intro | Overview |
| 2 | Problem | Overview |
| 3 | Architecture | Settings mode |
| 5 | Topology | Topology |
| 6 | Paths + score | Paths / Optimize |
| 7 | Failover | Simulation |
| 8 | Real lab / FW | Settings / Firewall |
| 9 | Tests + limits | — |

**Sentence to memorize:**  
“Software graph for teaching paths and scores; ContainerLab FRR for real OSPF inspection; host network never modified.”
