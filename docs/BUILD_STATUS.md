# Build Status

Updated: 2026-11-11

## Passing

- Backend pytest: **32 passed**
- Frontend: Vite app with Firewall + Settings lab controls
- ContainerLab deploy: **R1/R2/R3 running**
- OSPF neighbors Full + ping + failover alternate path: **verified**
- API `/api/lab/infrastructure` reports `REAL_LAB` when lab up

## Partial / blocked

- RIP real lab: not enabled in `daemons` (ospf-focused demo)
- BGP: not enabled
- nftables apply on FRR nodes: blocked (no binaries / apk CDN)
- Playwright screenshot matrix: not run this session
- Topology Designer full interactive editor: existing canvas + inspector; advanced add/delete UX incremental

## Commands

```powershell
cd C:\Users\deepa\cn\backend
.\.venv\Scripts\python.exe -m pytest -q

cd C:\Users\deepa\cn\frontend
npm run build

.\scripts\dev.ps1 status
.\scripts\dev.ps1 lab-status
```
