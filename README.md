# RouteWise

Intelligent Routing Management & Network Path Optimization System

Computer Networks course project that combines a React dashboard, a FastAPI control plane, and a Docker/ContainerLab FRRouting lab for inspecting OSPF-based path behavior in a three-router triangular topology.

## Objective

Provide a safe, read-only management view over a simulated routing lab so students can observe router availability, routing tables, and OSPF neighbor state without modifying the host network or issuing arbitrary shell commands.

## Main features

- Dark network-management dashboard (React + Vite)
- FastAPI REST API with strict, allow-listed Docker/vtysh inspection
- ContainerLab topology: R1–R2–R3 triangle with OSPF area 0
- Lab status and health endpoints that degrade gracefully when the lab is stopped
- Scripts for environment checks and lab lifecycle (deploy later; not during init)

## Technology stack

| Layer | Stack |
|-------|--------|
| Frontend | React, Vite, JavaScript, CSS |
| Backend | Python, FastAPI, Pydantic, uvicorn |
| Lab | Docker Desktop, WSL2 Ubuntu, ContainerLab, FRRouting |
| Protocol | OSPF area 0 |

## Architecture overview

```
Browser (React @ :5173)
        │  REST /api/*
        ▼
FastAPI backend (@ :8000)
        │  fixed docker/vtysh commands only
        ▼
Docker Desktop → ContainerLab FRR nodes (R1, R2, R3)
```

- Frontend never talks to Docker directly.
- Backend never accepts arbitrary shell from API clients.
- Lab remains isolated inside Docker/WSL; host routing table is untouched.

## Folder structure

```
cn/
├── README.md
├── docs/                 # Architecture, API, topology, install, plan
├── frontend/             # React + Vite dashboard
├── backend/              # FastAPI application + tests
├── lab/                  # ContainerLab topology + FRR configs
└── scripts/              # Env check and lifecycle helpers
```

## Prerequisites

- Python 3.10+ (3.12 recommended)
- Node.js 20+ and npm
- Docker Desktop with WSL2 backend
- WSL2 Ubuntu
- ContainerLab (install inside WSL; not required for local UI/API init)
- Git

## Frontend setup

```powershell
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173

## Backend setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs  
Health: http://localhost:8000/api/health

## Start development servers

From the project root (Git Bash / WSL):

```bash
./scripts/start_backend.sh
./scripts/start_frontend.sh
```

Or use the PowerShell/npm/uvicorn commands above in two terminals.

## Deploy the ContainerLab topology (later)

Do **not** deploy during first-time initialization. When ready, from WSL with ContainerLab installed:

```bash
./scripts/deploy_lab.sh
```

Topology file: `lab/routewise.clab.yml`

## Inspect routes and OSPF neighbors

Once the lab is running:

- API: `GET /api/routers/{R1|R2|R3}/routes`
- API: `GET /api/routers/{R1|R2|R3}/ospf-neighbors`
- Or via vtysh inside a container (read-only example):

```bash
docker exec -it clab-routewise-r1 vtysh -c "show ip route"
docker exec -it clab-routewise-r1 vtysh -c "show ip ospf neighbor"
```

## Stop and destroy the lab

```bash
./scripts/destroy_lab.sh
```

## Network summary

| Router | Loopback | Links |
|--------|----------|--------|
| R1 | 192.168.1.1/32 | 10.0.12.1/30 (to R2), 10.0.13.1/30 (to R3) |
| R2 | 192.168.2.2/32 | 10.0.12.2/30 (to R1), 10.0.23.1/30 (to R3) |
| R3 | 192.168.3.3/32 | 10.0.23.2/30 (to R2), 10.0.13.2/30 (to R1) |

## Documentation

- [Architecture](docs/architecture.md)
- [API documentation](docs/api-documentation.md)
- [Network topology](docs/network-topology.md)
- [Installation guide](docs/installation-guide.md)
- [Project plan](docs/project-plan.md)

## License

Academic / course use.
