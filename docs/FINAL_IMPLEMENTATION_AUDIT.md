# Final Implementation Audit

## Process / ports (at audit close)

| Service | Port | State |
|---------|------|-------|
| Backend uvicorn | 127.0.0.1:8000 | Running (restarted with lab/firewall routes) |
| Frontend Vite | 127.0.0.1:5173 | Running (reuse; do not treat prior intentional Vite stop as crash) |

## Gaps found and actions

| Issue | Action |
|-------|--------|
| No NetworkProvider boundary | Added `providers/` (software, containerlab, factory) |
| Windows Docker pipe down | `wsl_bridge` falls back to WSL docker/clab |
| ContainerLab missing earlier | Present in WSL 0.83.0 |
| FRR daemons CRLF | Converted configs to LF; lab redeployed |
| No firewall API/UI | Added models, service, routes, Firewall page |
| Settings lacked lab lifecycle | Deploy/restart/destroy + infrastructure probe |
| ospfd not running (CRLF) | Fixed; OSPF Full mesh verified |
| nftables missing in FRR image | Documented BLOCKED; optional fw1 node added to YAML |

## Preserved

- Software simulation path/optimize/failover
- Existing 28+ backend tests (now 32)
- Vite `/api` proxy
- Seeded R1–R2–R3 SQLite topology
