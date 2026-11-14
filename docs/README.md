# RouteWise documentation

Start here if you are browsing the repository. Every major guide lives under `docs/`.

## Read in this order

| # | Document | Audience | What you get |
|---|----------|----------|--------------|
| 1 | [GETTING_STARTED.md](GETTING_STARTED.md) | Everyone | Clone → run UI + API in minutes |
| 2 | [UI_BROWSING_GUIDE.md](UI_BROWSING_GUIDE.md) | Demo / reviewers | Page-by-page tour of the dashboard |
| 3 | [PROJECT_EXPLANATION.md](PROJECT_EXPLANATION.md) | Professors / viva | What is real vs simulated (honest labels) |
| 4 | [TECHNICAL_ARCHITECTURE_WALKTHROUGH.md](TECHNICAL_ARCHITECTURE_WALKTHROUGH.md) | Engineers | Request journeys and control-plane design |
| 5 | [PROJECT_FILE_GUIDE.md](PROJECT_FILE_GUIDE.md) | Contributors | Map of important source files |
| 6 | [LIVE_DEMO_RUNBOOK.md](LIVE_DEMO_RUNBOOK.md) | Presenters | Click path for a live demo |
| 7 | [PRESENTATION_SCRIPT.md](PRESENTATION_SCRIPT.md) | Presenters | Spoken narrative |
| 8 | [VIVA_QUESTIONS_AND_ANSWERS.md](VIVA_QUESTIONS_AND_ANSWERS.md) | Defense | Expected Q&A |

## Setup and operations

| Document | Purpose |
|----------|---------|
| [installation-guide.md](installation-guide.md) | Tooling prerequisites and install steps |
| [NETWORK_INFRASTRUCTURE.md](NETWORK_INFRASTRUCTURE.md) | Docker / WSL2 / ContainerLab / FRR facts |
| [network-topology.md](network-topology.md) | R1–R2–R3 addressing and links |
| [api-documentation.md](api-documentation.md) | REST endpoints (also live at `/docs`) |

## Design and architecture

| Document | Purpose |
|----------|---------|
| [architecture.md](architecture.md) | High-level system architecture |
| [DESIGN.md](DESIGN.md) | Product / UI design notes |
| [FIREWALL_IMPLEMENTATION.md](FIREWALL_IMPLEMENTATION.md) | Firewall policy engine + REAL_LAB apply |

## Status, audits, and reports

| Document | Purpose |
|----------|---------|
| [BUILD_STATUS.md](BUILD_STATUS.md) | Build / test snapshot |
| [END_TO_END_TEST_REPORT.md](END_TO_END_TEST_REPORT.md) | Live verification notes |
| [FINAL_ENGINEERING_REPORT.md](FINAL_ENGINEERING_REPORT.md) | Feature completion matrix |
| [FINAL_IMPLEMENTATION_AUDIT.md](FINAL_IMPLEMENTATION_AUDIT.md) | Implementation audit |
| [UI_COMPLETION_REPORT.md](UI_COMPLETION_REPORT.md) | Frontend completion notes |
| [UI_IMPLEMENTATION_PLAN.md](UI_IMPLEMENTATION_PLAN.md) | Historical UI plan |
| [UI_SKILLS_AND_DESIGN_RESEARCH.md](UI_SKILLS_AND_DESIGN_RESEARCH.md) | Design research |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Historical build plan |
| [project-plan.md](project-plan.md) | Original project plan |

## Honesty labels (read before demos)

| Mode | Meaning |
|------|---------|
| `SOFTWARE_SIMULATION` | SQLite topology + software path/failover. Safe without Docker. |
| `REAL_LAB` | ContainerLab FRR containers online; OSPF/RIP probed via allow-listed `vtysh`. |
| Header badge **FRR up** | Lab containers running and reachable from the API. |
| Header badge **FRR down** | Lab not deployed / Docker unavailable / containers stopped. |

Never present Simulation Lab clicks as live `ip link` operations on FRR unless `REAL_LAB` is active and you are using lab lifecycle APIs intentionally.

## Quick links (when servers are running)

| Surface | URL |
|---------|-----|
| Dashboard | http://127.0.0.1:5173 |
| OpenAPI / Swagger | http://127.0.0.1:8000/docs |
| Health | http://127.0.0.1:8000/api/health |
| Lab infrastructure | http://127.0.0.1:8000/api/lab/infrastructure |
