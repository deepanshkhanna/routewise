# RouteWise

**Intelligent Routing Management & Network Path Optimization System**

Computer Networks course project: a React operations dashboard, a FastAPI control plane, and an optional Docker/ContainerLab FRRouting lab for a three-router OSPF triangle.

**Public repository:** https://github.com/deepanshkhanna/routewise

---

## What this is

| Layer | Role |
|-------|------|
| **Frontend** | Dark network-ops UI (React + Vite) — topology, routing, paths, simulation, firewall, settings |
| **Backend** | FastAPI + SQLite control plane — allow-listed Docker/`vtysh` only |
| **Lab (optional)** | ContainerLab FRR nodes R1–R2–R3 (+ fw1) for live OSPF/RIP inspection |

Two honest execution modes:

- **`SOFTWARE_SIMULATION`** — full UI + path/failover on the SQLite graph (no Docker required)
- **`REAL_LAB`** — ContainerLab FRR online; OSPF/RIP probed from live containers

---

## Quick start

```bash
git clone https://github.com/deepanshkhanna/routewise.git
cd routewise
cp .env.example .env
```

**Backend**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend** (new terminal)

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

| Surface | URL |
|---------|-----|
| Dashboard | http://127.0.0.1:5173 |
| Swagger API | http://127.0.0.1:8000/docs |
| Health | http://127.0.0.1:8000/api/health |

Full setup (lab included): **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)**  
UI tour: **[docs/UI_BROWSING_GUIDE.md](docs/UI_BROWSING_GUIDE.md)**  
All docs: **[docs/README.md](docs/README.md)**

---

## Browse the product (UI map)

| Route | Page | Purpose |
|-------|------|---------|
| `/` | Overview | Ops summary + lab awareness |
| `/topology` | Topology Designer | Interactive R1–R2–R3 canvas |
| `/routing` | Routing | Static routes + RIP/OSPF when lab is up |
| `/paths` | Path Explorer | Software path computation |
| `/optimize` | Optimization | Cost-aware path suggestions |
| `/simulation` | Simulation Lab | Guided failover demo |
| `/firewall` | Firewall | Policy CRUD (+ optional REAL_LAB apply) |
| `/analytics` | Analytics | Charts / presentation visuals |
| `/events` | Events | Event log |
| `/reports` | Reports | Summary surfaces |
| `/settings` | Settings | Lab deploy / destroy / infrastructure probe |

Step-by-step clicks: [docs/UI_BROWSING_GUIDE.md](docs/UI_BROWSING_GUIDE.md) · Demo script: [docs/LIVE_DEMO_RUNBOOK.md](docs/LIVE_DEMO_RUNBOOK.md)

---

## Architecture

```
Browser (React @ :5173)
        │  REST /api/*
        ▼
FastAPI backend (@ :8000)  +  SQLite
        │  fixed docker / vtysh commands only
        ▼
Docker → ContainerLab FRR (R1, R2, R3)   [optional REAL_LAB]
```

- Frontend never talks to Docker directly.
- Backend never accepts arbitrary shell from clients.
- Host routing table is never modified.

---

## Repository layout

```
routewise/
├── README.md              # You are here
├── CONTRIBUTING.md
├── LICENSE
├── .env.example
├── docs/                  # Full guides, audits, viva pack
├── frontend/              # React + Vite
├── backend/               # FastAPI + pytest
├── lab/                   # ContainerLab topology + FRR configs
└── scripts/               # env check, deploy/destroy, start helpers
```

---

## Lab topology (when deployed)

| Router | Loopback | Links |
|--------|----------|--------|
| R1 | 192.168.1.1/32 | 10.0.12.1/30 → R2, 10.0.13.1/30 → R3 |
| R2 | 192.168.2.2/32 | 10.0.12.2/30 → R1, 10.0.23.1/30 → R3 |
| R3 | 192.168.3.3/32 | 10.0.23.2/30 → R2, 10.0.13.2/30 → R1 |

```bash
# from WSL with ContainerLab installed
bash scripts/deploy_lab.sh
bash scripts/destroy_lab.sh
```

If containers lose `eth1`/`eth2` after a bare `docker start`, **redeploy** with ContainerLab — do not rely on Docker restart alone.

---

## Documentation index

| Guide | Use when |
|-------|----------|
| [docs/README.md](docs/README.md) | Finding any document |
| [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) | First run |
| [docs/UI_BROWSING_GUIDE.md](docs/UI_BROWSING_GUIDE.md) | Exploring the UI |
| [docs/PROJECT_EXPLANATION.md](docs/PROJECT_EXPLANATION.md) | Understanding real vs simulated |
| [docs/TECHNICAL_ARCHITECTURE_WALKTHROUGH.md](docs/TECHNICAL_ARCHITECTURE_WALKTHROUGH.md) | Data-flow deep dive |
| [docs/PROJECT_FILE_GUIDE.md](docs/PROJECT_FILE_GUIDE.md) | Navigating source files |
| [docs/api-documentation.md](docs/api-documentation.md) | REST reference |
| [docs/installation-guide.md](docs/installation-guide.md) | Prerequisites |
| [docs/NETWORK_INFRASTRUCTURE.md](docs/NETWORK_INFRASTRUCTURE.md) | Docker / WSL / FRR |
| [docs/LIVE_DEMO_RUNBOOK.md](docs/LIVE_DEMO_RUNBOOK.md) | Live demo clicks |
| [docs/PRESENTATION_SCRIPT.md](docs/PRESENTATION_SCRIPT.md) | Spoken demo |
| [docs/VIVA_QUESTIONS_AND_ANSWERS.md](docs/VIVA_QUESTIONS_AND_ANSWERS.md) | Defense Q&A |
| [docs/FINAL_ENGINEERING_REPORT.md](docs/FINAL_ENGINEERING_REPORT.md) | Feature matrix |
| [docs/END_TO_END_TEST_REPORT.md](docs/END_TO_END_TEST_REPORT.md) | Verification notes |

---

## Prerequisites

- Python 3.10+ (3.12+ recommended)
- Node.js 20+ and npm
- Docker Desktop + WSL2 Ubuntu + ContainerLab *(optional, for REAL_LAB)*
- Git

---

## Safety

- Inspection commands are allow-listed.
- No host network mutation from the app.
- Secrets: copy `.env.example` → `.env`; never commit `.env` or `backend/data/*.db`.

---

## License

MIT — see [LICENSE](LICENSE). Academic / course use welcome.
