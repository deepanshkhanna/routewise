# End-to-End Test Report

Date: 2026-11-11

## Backend unit/API tests

```
32 passed
```

Includes prior suite plus firewall CRUD/test and lab infrastructure mocks.

## Real lab — deploy

```
clab deploy -t routewise.clab.yml
→ clab-routewise-r1|r2|r3 running (FRR containerlab-10.7.1)
```

**Status: IMPLEMENTED AND VERIFIED IN REAL LAB**

## Real lab — OSPF

After LF-normalized `daemons`/`frr.conf`:

- `watchfrr` runs `zebra ospfd staticd` only (as configured)
- R1 neighbors: `2.2.2.2` Full (eth1), `3.3.3.3` Full (eth2)
- OSPF routes to `192.168.2.2/32` and `192.168.3.3/32` installed
- Ping R1→R2 and R1→R3: 0% loss

**Status: IMPLEMENTED AND VERIFIED IN REAL LAB**

## Real lab — failover demo

1. Baseline traceroute R1→`192.168.3.3`: direct 1 hop
2. `ip link set eth2 down` on R1 (real interface)
3. OSPF neighbor 3.3.3.3 withdrawn; only 2.2.2.2 Full
4. Route to `192.168.3.3` via `10.0.12.2` eth1 (metric 20)
5. Traceroute: `10.0.12.2` → `192.168.3.3`
6. Ping still 0% loss via alternate path
7. `ip link set eth2 up` — neighbor returns toward Full

**Status: IMPLEMENTED AND VERIFIED IN REAL LAB**

## Firewall

Software policy engine: verified via pytest + API.

`fw1` Alpine + nftables: installed; ICMP drop rule verified (100% loss to lo inside fw1 only).

`POST /api/networks/1/firewall/apply` → applied SQLite deny rule into `inet routewise` on `clab-routewise-fw1` (ruleset listed in API response).

nftables inside FRR router images: not used (no binaries); fw1 is the real-lab firewall target.

## Frontend

- Modules wired: Overview, Topology, Routing, Paths, Optimization, Simulation, **Firewall**, Analytics, Events, Reports, Settings
- Mode badge reads `/api/lab/infrastructure`
- Vite proxy `/api` preserved

## API smoke (post-restart)

- `GET /api/health` → ok
- `GET /api/lab/infrastructure` → `active_mode=REAL_LAB`, three routers running
- `GET /api/networks/1/firewall/status` → mode REAL_LAB
