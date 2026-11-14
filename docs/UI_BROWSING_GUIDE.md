# UI browsing guide

Tour of the RouteWise dashboard. Assumes backend (`:8000`) and frontend (`:5173`) are running. Lab is optional.

Base URL: http://127.0.0.1:5173

## Global chrome

| Element | Where | Meaning |
|---------|-------|---------|
| **API online / offline** | Header | FastAPI health probe |
| **FRR up / checking / down** | Header | ContainerLab FRR lab reachability |
| Sidebar | Left | Navigate all primary modules |

## Pages

### Overview — `/`

Operational summary for the default triangle network.

- Metric cards for routers, links, events, lab state
- Quick sense of `SOFTWARE_SIMULATION` vs live lab
- Entry point before deeper tools

**Look for:** lab badge consistency with header; seeded R1–R2–R3 network.

---

### Topology Designer — `/topology`

Interactive React Flow canvas of routers and links.

- Drag / pan / zoom the graph
- Select nodes; inspect status coloring when lab is online
- Edit topology through the control plane (SQLite-backed)

**Look for:** R1–R2–R3 triangle; link costs; no minimap overlay (removed by design).

---

### Routing — `/routing`

Static routes (SQLite) plus RIP v2 / OSPF status when `REAL_LAB` is active.

- Add/list static routes for demos without FRR
- Protocol panels read live FRR via allow-listed `vtysh` when lab is up
- Clear messaging when lab is unavailable

**Look for:** honesty — OSPF neighbor Full state only when containers are healthy.

---

### Path Explorer — `/paths`

Compute paths on the software topology graph.

- Choose source / destination
- Inspect hop sequence and costs
- Works fully in `SOFTWARE_SIMULATION`

---

### Optimization — `/optimize`

Suggests preferred paths / cost-aware choices on the SQLite graph.

- Compare candidate routes
- Useful for teaching Dijkstra-style intuition without touching FRR

---

### Simulation Lab — `/simulation`

Professor-friendly failover walkthrough.

- Guided steps: baseline → fail a link → recompute → compare
- Packet-style animation on the canvas
- Software plane by default — do **not** claim live FRR `ip link` unless you deliberately drive lab APIs

**Look for:** step checklist, before/after path comparison, clear simulation labeling.

---

### Firewall — `/firewall`

Isolated policy engine.

- CRUD rules in SQLite
- Optional apply into lab (`nftables`) only when `REAL_LAB` is active
- Mode badge: software vs real lab

---

### Analytics — `/analytics`

Charts and illustrative telemetry for the UI.

- Not live FRR counters unless explicitly documented otherwise
- Good for presentation visuals

---

### Events — `/events`

Operational event log tied to the selected network.

- Failover / topology / control-plane activity as recorded by the API

---

### Reports — `/reports`

Summaries suitable for screenshots and viva handouts.

- Network + overview derived report surfaces

---

### Settings — `/settings`

Lab lifecycle and infrastructure probe.

- Deploy / restart / destroy ContainerLab topology (when Docker/WSL bridge works)
- Shows `SOFTWARE_SIMULATION` vs `REAL_LAB`
- Refresh lab status after deploy

**Look for:** `/api/lab/infrastructure` fields (`docker_ok`, `containerlab_ok`, `lab_deployed`, per-router status).

## Suggested 10-minute browse path

1. Overview → confirm API online  
2. Topology → show triangle  
3. Paths → compute R1→R3  
4. Simulation → run guided failover  
5. Routing → show static routes; if lab up, OSPF neighbors  
6. Settings → show mode and infrastructure JSON  
7. Firewall → show policy list + mode badge  

## Demo with live FRR

1. Deploy lab (`scripts/deploy_lab.sh` or Settings deploy).  
2. Wait until header shows **FRR up**.  
3. Routing → OSPF neighbors should reach **Full**.  
4. Keep Simulation Lab language honest (software graph vs REAL_LAB probes).

## Related docs

- [LIVE_DEMO_RUNBOOK.md](LIVE_DEMO_RUNBOOK.md) — timed click script  
- [PRESENTATION_SCRIPT.md](PRESENTATION_SCRIPT.md) — what to say  
- [GETTING_STARTED.md](GETTING_STARTED.md) — setup  
