# Getting started

Run RouteWise locally without ContainerLab first. Add the FRR lab only when Docker + WSL2 + ContainerLab are ready.

## 1. Clone

```bash
git clone https://github.com/deepanshkhanna/routewise.git
cd routewise
```

## 2. Environment

```bash
cp .env.example .env
```

Defaults:

- API: `http://127.0.0.1:8000`
- UI: `http://127.0.0.1:5173`

## 3. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Linux / macOS / WSL:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verify: http://127.0.0.1:8000/api/health

Interactive API: http://127.0.0.1:8000/docs

## 4. Frontend

New terminal:

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open: http://127.0.0.1:5173

You should see **API online**. **FRR down** is expected until the lab is deployed.

## 5. Optional — PowerShell helper

From repo root (Windows):

```powershell
.\scripts\dev.ps1 backend
.\scripts\dev.ps1 frontend
.\scripts\dev.ps1 status
```

## 6. Optional — ContainerLab FRR lab (REAL_LAB)

Prerequisites:

- Docker Desktop running (WSL2 engine recommended on Windows)
- ContainerLab installed inside WSL Ubuntu
- Topology file: `lab/routewise.clab.yml`

From WSL:

```bash
cd /mnt/c/path/to/routewise   # or your clone path under WSL
bash scripts/deploy_lab.sh
```

Or:

```bash
cd lab
containerlab deploy -t routewise.clab.yml
```

Confirm:

```bash
docker ps --filter name=clab-routewise
docker exec clab-routewise-r1 vtysh -c "show ip ospf neighbor"
```

Destroy:

```bash
bash scripts/destroy_lab.sh
```

**Important:** routers use `restart=no` after deploy. If Docker restarts a container alone, data-plane veths (`eth1`/`eth2`) can be missing — redeploy with ContainerLab instead of `docker start`.

## 7. Browse the UI

Follow [UI_BROWSING_GUIDE.md](UI_BROWSING_GUIDE.md).

## 8. Stop everything

1. Stop Vite / uvicorn terminals (`Ctrl+C`).
2. Destroy lab if deployed: `bash scripts/destroy_lab.sh`.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| UI shows API offline | Start backend on `:8000`; check CORS / `VITE_API_BASE_URL` |
| FRR down forever | Deploy lab; ensure Docker works inside WSL; check `/api/lab/infrastructure` |
| OSPF empty / no neighbors | Redeploy lab (do not only `docker start`) |
| Port in use | Free `:8000` / `:5173` or change ports in `.env` |
| Tests fail | Run `pytest -q` from `backend/` with venv active |

## Next reading

- [docs/README.md](README.md) — full documentation index
- [PROJECT_EXPLANATION.md](PROJECT_EXPLANATION.md) — real vs simulated behavior
- [api-documentation.md](api-documentation.md) — REST reference
