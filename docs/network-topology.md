# Network topology

## Overview

RouteWise uses a three-router triangular topology so every pair of routers has a direct link. OSPF area 0 forms adjacencies on all three links and advertises loopback and connected networks.

```
          R1
         /  \
   10.0.12   10.0.13
       /      \
     R2 ------ R3
        10.0.23
```

## Addressing

### Loopbacks

| Router | Loopback |
|--------|----------|
| R1 | 192.168.1.1/32 |
| R2 | 192.168.2.2/32 |
| R3 | 192.168.3.3/32 |

### Point-to-point links (`/30`)

| Link | Subnet | Endpoints |
|------|--------|-----------|
| R1 ↔ R2 | 10.0.12.0/30 | R1 `10.0.12.1`, R2 `10.0.12.2` |
| R2 ↔ R3 | 10.0.23.0/30 | R2 `10.0.23.1`, R3 `10.0.23.2` |
| R1 ↔ R3 | 10.0.13.0/30 | R1 `10.0.13.1`, R3 `10.0.13.2` |

## Routing

- Protocol: OSPF
- Area: 0 (backbone)
- Networks: connected link subnets and loopbacks advertised into OSPF
- Image: `quay.io/frrouting/frr:containerlab-10.7.1`

## ContainerLab artifacts

| Path | Role |
|------|------|
| `lab/routewise.clab.yml` | Topology definition |
| `lab/configs/r1/frr.conf` | R1 FRR configuration |
| `lab/configs/r2/frr.conf` | R2 FRR configuration |
| `lab/configs/r3/frr.conf` | R3 FRR configuration |
| `lab/configs/*/daemons` | Enabled FRR daemons |

Expected container names after deploy:

- `clab-routewise-r1`
- `clab-routewise-r2`
- `clab-routewise-r3`

## Isolation

All lab networking stays inside Docker/WSL. Scripts and the API must not modify Windows host routes or network adapters.
