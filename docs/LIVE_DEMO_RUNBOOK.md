# RouteWise — Live Demo Runbook

Use this during viva/demo. Prefer the software path if Docker/ContainerLab is unavailable. Never present software Simulation Lab clicks as live FRR `ip link` operations.

---

## 0. Pre-flight checklist

| Check | How | Pass criteria |
|-------|-----|---------------|
| Backend | Browser `http://127.0.0.1:8000/api/health` | JSON ok |
| Frontend | `http://127.0.0.1:5173` | UI loads |
| Mode | Sidebar “RouteWise Lab” or Settings | `SOFTWARE_SIMULATION` or `REAL_LAB` |
| Default network | Overview / Topology | R1 R2 R3 visible |

### Start services (Windows PowerShell)

Terminal 1 — backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2 — frontend:

```powershell
cd frontend
npm run dev
```

Or from repo root if available:

```powershell
.\scripts\dev.ps1 backend
.\scripts\dev.ps1 frontend
.\scripts\dev.ps1 status
```

### Optional lab

```powershell
.\scripts\dev.ps1 lab-deploy
.\scripts\dev.ps1 lab-status
```

WSL alternative:

```bash
cd /mnt/c/Users/deepa/cn/lab
clab deploy -t routewise.clab.yml
```

**Fallback if lab fails:** continue with sections 1–14 using software APIs only. Say: “REAL_LAB unavailable; demonstrating SOFTWARE_SIMULATION.”

---

## Demo sequence

### 1. Starting frontend and backend

- **Do:** Start uvicorn + Vite as above.  
- **Say:** “Backend on port 8000, frontend on 5173, Vite proxies `/api`.”  
- **Expect:** Health OK; no CORS errors in console.

### 2. Opening the application

- **Click:** open `http://127.0.0.1:5173`  
- **Show:** dark operations UI, sidebar modules.  
- **Say:** “This is the RouteWise control dashboard.”

### 3. Dashboard / Overview

- **Click:** Overview (`/`)  
- **Show:** router/link counts, recent events, lab running flag.  
- **API:** `GET /api/dashboard/overview`  
- **Say:** “Overview metrics come from the SQLite software topology. The message on the API explicitly says that.”  
- **Expect:** seeded network present; `data_source` software.

### 4–5. Topology — routers and links

- **Click:** Topology Designer  
- **Show:** React Flow triangle R1–R2–R3; subnets 10.0.12/30, 10.0.23/30, 10.0.13/30.  
- **API:** `GET /api/networks/{id}`  
- **Say:** “This mirrors our ContainerLab addressing so simulation and real lab stay aligned.”

### 6–7. Routing Manager and routing tables

- **Click:** Routing Manager  
- **Show:** static route form + table; protocol badges (Static / RIP / OSPF / BGP).  
- **API:** `GET /api/networks/{id}/static-routes`, `GET /api/lab/protocols`  
- **Say:**  
  - “Static routes here are persisted in SQLite for the software plane.”  
  - “OSPF badge reflects live FRR neighbors when the lab is deployed.”  
  - “BGP is marked future / disabled in daemons.”  
- **Optional if REAL_LAB:** open API docs or call `GET /api/routers/R1/routes` and `…/ospf-neighbors` to show live tables.  
- **Expect if lab down:** OSPF/RIP badges warn “Lab not deployed” or unreachable — still OK for demo.

### 8–9. Path Explorer — candidates

- **Click:** Path Explorer  
- **Select:** Source R1, Destination R3 → **Trace path**  
- **API:** `GET /api/networks/{id}/paths?source=R1&destination=R3`  
- **Show:** protocol-selected path (likely R1→R3), candidate table including R1→R2→R3.  
- **Say:** “Pathfinding is DFS over the undirected link graph. Protocol-selected means lowest total link cost in software — not a claim that we scraped OSPF SPF for this panel.”  
- **Expect:** two candidates when all links up; message mentions software_simulation.

### 10. Route optimization

- **Click:** Optimization  
- **Select:** R1 → R3 → run optimize  
- **API:** `GET /api/networks/{id}/optimize?source=R1&destination=R3`  
- **Show:** recommended path, score, breakdown L/P/H/C, explanation text.  
- **Say:** “S = 0.35L + 0.25P + 0.20H + 0.20C after min-max normalization. Lower is better. This is advisory software scoring.”  
- **Expect (default seed):** recommended R1→R3 with score 0 vs alternate 100; matches lowest-cost path.

### 11. Disable a network link

- **Click:** Simulation Lab  
- **Click:** **Disable R1-R3** (button label uses router names)  
- **API:** `POST /api/networks/{id}/simulate/links/{linkId}/disable`  
- **Show:** link state change on canvas; recovery path updates.  
- **Say:** “We mark the link down in SQLite and log a simulation event. The graph engine immediately stops using that edge.”  
- **Expect:** active link count decreases; path becomes R1→R2→R3.

### 12. Show the alternative route

- **Show:** “Recovery path R1 → R3” panel reading `R1 → R2 → R3`.  
- **Optional:** return to Path Explorer and Trace again — only one candidate.  
- **Say:** “This is how we teach failover without breaking the host network.”

### 13. Restore the link

- **Click:** **Restore R1-R3**  
- **API:** `POST …/simulate/links/{linkId}/enable`  
- **Expect:** direct path available again; event logged as restored.

### 14. Events and analytics

- **Click:** Events & Alerts  
- **Show:** disable/restore events with `data_source=software_simulation`.  
- **Click:** Analytics  
- **Say clearly:** “Analytics charts are illustrative for UI demonstration, not live telemetry.”  
- **Optional:** Reports page for export-style summary.

### 15. Real network infrastructure status

- **Click:** Settings & Lab  
- **Show:** infrastructure probe / mode.  
- **API:** `GET /api/lab/infrastructure`  

**If `active_mode=REAL_LAB`:**

- Say: “ContainerLab FRR nodes are running. Inspection uses allow-listed docker exec vtysh.”  
- Optional demo:  
  - `GET /api/routers/R1/ospf-neighbors` → Full neighbors  
  - `GET /api/routers/R1/routes` → OSPF routes to other loopbacks  
- Optional firewall apply story: rules on `fw1` only; host firewall untouched.  
- Do **not** run destructive destroy unless you can redeploy quickly.

**If software only:**

- Say: “Docker or ContainerLab is unavailable in this environment. Software simulation remains fully usable for path, optimize, and failover teaching. Real OSPF was verified in our lab report when the environment was available.”

---

## Recommended timing (≈8 minutes demo)

| Min | Step |
|-----|------|
| 0:00 | Start / Overview |
| 0:45 | Topology |
| 1:30 | Routing Manager + mode honesty |
| 2:30 | Path Explorer |
| 3:30 | Optimization + formula |
| 4:30 | Disable link → alternate |
| 5:30 | Restore + Events |
| 6:15 | Settings infrastructure |
| 7:00 | Firewall one-liner + limitations |
| 7:30 | Stop / ask for questions |

---

## Fallback scripts

### A. Backend up, frontend up, lab down

Run steps 1–14. Skip live vtysh. Point to `docs/END_TO_END_TEST_REPORT.md` for prior OSPF verification if asked.

### B. Backend down

```powershell
cd C:\Users\deepa\cn\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### C. Port busy

Change port or stop the old process; Vite proxy expects backend `:8000` unless configured otherwise.

### D. Empty topology

```http
POST /api/networks/seed-default
```

Or restart backend (startup seeds automatically).

### E. Want real failover proof without UI wiring

Only if lab is up and you have time — in WSL:

```bash
docker exec clab-routewise-r1 vtysh -c "show ip ospf neighbor"
docker exec -it clab-routewise-r1 sh -c "ip link set eth2 down"
# show neighbor / traceroute change
docker exec -it clab-routewise-r1 sh -c "ip link set eth2 up"
```

Label this **manual real-lab failover**, separate from Simulation Lab buttons.

---

## Phrases that keep you safe

- “This panel is software_simulation.”  
- “This reading comes from live FRR via allow-listed vtysh.”  
- “We do not modify the Windows routing table or Windows Firewall.”  
- “BGP is not enabled in this project.”  
- “Analytics here is illustrative.”
