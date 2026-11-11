# RouteWise Network Infrastructure

## Environment (verified 2026-11-11)

| Component | Status | Notes |
|-----------|--------|-------|
| Windows host | Win32 10.0.26300 | Backend/frontend run natively |
| Docker Desktop CLI | Present | Windows daemon pipe often unreachable |
| WSL2 Docker engine | **OK** — Server 29.1.3 | Owns lab containers |
| ContainerLab | **OK** — 0.83.0 | `/usr/bin/clab` in WSL |
| FRR image | quay.io/frrouting/frr:containerlab-10.7.1 | Alpine 3.22 based |

Backend bridges to WSL via `app/services/wsl_bridge.py` when the Windows Docker named pipe is down. No unauthenticated Docker TCP socket is exposed.

## Topology

File: `lab/routewise.clab.yml`

Matches the seeded SQLite R1–R2–R3 triangle:

- R1 eth1 ↔ R2 eth1 — `10.0.12.0/30`
- R2 eth2 ↔ R3 eth1 — `10.0.23.0/30`
- R1 eth2 ↔ R3 eth2 — `10.0.13.0/30`
- Loopbacks: `192.168.1.1`, `192.168.2.2`, `192.168.3.3`

Optional `fw1` Alpine node is defined for isolated nftables experiments (not in the OSPF data plane).

**Important:** FRR `daemons` / `frr.conf` must be Unix LF. CRLF breaks `watchfrr` parsing (`$'\r': command not found`). See `lab/.gitattributes`.

## Provider modes

| Mode | Meaning |
|------|---------|
| `SOFTWARE_SIMULATION` | SQLite graph path/optimize/failover |
| `REAL_LAB` | ContainerLab FRR containers running |
| `UNAVAILABLE` | Docker/ContainerLab missing or lab not deployed |

Factory: `app/services/providers/factory.py`

## Lifecycle

```powershell
# From Windows
.\scripts\dev.ps1 lab-deploy
.\scripts\dev.ps1 lab-status
.\scripts\dev.ps1 lab-destroy

# From WSL
cd /mnt/c/Users/deepa/cn/lab
clab deploy -t routewise.clab.yml
clab destroy -t routewise.clab.yml --cleanup
```

API: `POST /api/lab/deploy|destroy|restart`, `GET /api/lab/infrastructure`

## Safety

- Lab traffic stays inside Docker/`clab` network (`172.20.20.0/24` mgmt).
- Host Windows routing table and Windows Defender Firewall are never modified.
- Only allow-listed `docker` / `vtysh` commands are executed.
- Destroy targets only the RouteWise topology file — no global prune.
