# API documentation

## Base URL

Local development: `http://localhost:8000`

Interactive OpenAPI (Swagger UI): `http://localhost:8000/docs`

OpenAPI JSON: `http://localhost:8000/openapi.json`

## Conventions

- All inspection endpoints are **GET** and **read-only**.
- Router IDs are restricted to `R1`, `R2`, and `R3`.
- Clients cannot supply Docker or vtysh command strings.
- Configured topology (`/api/topology`) is separate from live Docker status.
- Error payloads avoid stack traces, secrets, and filesystem paths.

## Endpoints

### GET `/api/health`

Check whether the FastAPI process is running. Does **not** require Docker.

**Response 200**

```json
{
  "status": "ok",
  "app": "RouteWise",
  "version": "0.1.0"
}
```

---

### GET `/api/lab/status`

Determine Docker lab readiness for ContainerLab topology `routewise`.

Checks:

1. Docker CLI availability
2. Docker daemon reachability (`docker info`)
3. Per-router container state for `clab-routewise-r1|r2|r3`

Overall `status` values:

| status | meaning |
|--------|---------|
| `running` | All three router containers are running |
| `stopped` | One or more containers exist but are not fully running |
| `unavailable` | Docker missing/unreachable, or containers not found |
| `unknown` | Inspect could not determine state (e.g. timeout) |

**Response 200**

```json
{
  "lab_name": "routewise",
  "status": "unavailable",
  "running": false,
  "expected_routers": ["R1", "R2", "R3"],
  "containers_found": [],
  "routers": [
    {
      "router_id": "R1",
      "container_name": "clab-routewise-r1",
      "status": "unavailable"
    },
    {
      "router_id": "R2",
      "container_name": "clab-routewise-r2",
      "status": "unavailable"
    },
    {
      "router_id": "R3",
      "container_name": "clab-routewise-r3",
      "status": "unavailable"
    }
  ],
  "docker_ok": true,
  "message": "Docker lab containers were not found. Deploy the lab to continue."
}
```

`running` remains a boolean for clients that only need a simple flag (`true` only when overall status is `running`).

---

### GET `/api/routers`

Return configured routers with live availability from Docker inspect.

**Response 200**

```json
{
  "lab_running": false,
  "message": "Docker lab containers were not found. Deploy the lab to continue.",
  "routers": [
    {
      "id": "R1",
      "container_name": "clab-routewise-r1",
      "loopback": "192.168.1.1/32",
      "protocol": "OSPF",
      "available": false,
      "status": "unavailable"
    }
  ]
}
```

Loopback and protocol come from the documented lab design. `available` is true only when Docker reports the container as running.

---

### GET `/api/routers/{router_id}/routes`

Path parameter: `router_id` ∈ `{R1,R2,R3}` (case-insensitive).

Retrieves the FRR routing table via allow-listed commands:

1. `docker exec <container> vtysh -c "show ip route json"`
2. Fallback: `show ip route`

**Response 200** (lab running)

```json
{
  "router_id": "R1",
  "available": true,
  "status": "online",
  "routes": [
    {
      "destination": "192.168.2.2/32",
      "nexthop": "10.0.12.2",
      "protocol": "ospf",
      "metric": "20",
      "raw": "{...}"
    }
  ],
  "raw_output": "...",
  "message": "Routing table retrieved.",
  "error_code": null
}
```

**Error responses**

| HTTP | error_code | when |
|------|------------|------|
| 400 | `invalid_router_id` | Router id not R1/R2/R3 |
| 404 | `router_not_found` | Container missing |
| 409 | `router_stopped` | Container exists but stopped |
| 502 | `frr_command_failed` | vtysh failed |
| 503 | `docker_cli_missing` / `docker_daemon_unavailable` / `router_unknown` | Docker unavailable |
| 504 | `docker_timeout` | Subprocess timeout |

Example 404 body:

```json
{
  "router_id": "R1",
  "available": false,
  "status": "unavailable",
  "routes": [],
  "raw_output": "",
  "message": "Router container was not found; deploy the lab to read routing table.",
  "error_code": "router_not_found"
}
```

---

### GET `/api/routers/{router_id}/ospf-neighbors`

Path parameter: `router_id` ∈ `{R1,R2,R3}`.

Retrieves OSPF neighbors via:

1. `show ip ospf neighbor json`
2. Fallback: `show ip ospf neighbor`

**Response 200**

```json
{
  "router_id": "R1",
  "available": true,
  "status": "online",
  "neighbors": [
    {
      "local_router": "R1",
      "neighbor_id": "2.2.2.2",
      "priority": "1",
      "state": "Full/DR",
      "address": "10.0.12.2",
      "interface": "eth1:10.0.12.1",
      "raw": "..."
    }
  ],
  "raw_output": "...",
  "message": "OSPF neighbor table retrieved.",
  "error_code": null
}
```

HTTP error mapping matches `/routes`.

---

### GET `/api/topology`

Return the **configured** triangular topology. This does not inspect Docker.

**Response 200**

```json
{
  "name": "routewise-triangle",
  "protocol": "OSPF",
  "area": "0",
  "nodes": [
    {"id": "R1", "label": "R1", "loopback": "192.168.1.1/32"},
    {"id": "R2", "label": "R2", "loopback": "192.168.2.2/32"},
    {"id": "R3", "label": "R3", "loopback": "192.168.3.3/32"}
  ],
  "links": [
    {
      "id": "r1-r2",
      "source": "R1",
      "target": "R2",
      "subnet": "10.0.12.0/30",
      "endpoints": {"R1": "10.0.12.1/30", "R2": "10.0.12.2/30"}
    },
    {
      "id": "r2-r3",
      "source": "R2",
      "target": "R3",
      "subnet": "10.0.23.0/30",
      "endpoints": {"R2": "10.0.23.1/30", "R3": "10.0.23.2/30"}
    },
    {
      "id": "r1-r3",
      "source": "R1",
      "target": "R3",
      "subnet": "10.0.13.0/30",
      "endpoints": {"R1": "10.0.13.1/30", "R3": "10.0.13.2/30"}
    }
  ]
}
```

## Docker integration

| Operation | Command template |
|-----------|------------------|
| Daemon check | `docker info --format {{.ServerVersion}}` |
| Container state | `docker inspect -f {{.State.Status}} <allowlisted-name>` |
| FRR show | `docker exec <allowlisted-name> vtysh -c <allowlisted-show>` |

Expected container names:

- `clab-routewise-r1`
- `clab-routewise-r2`
- `clab-routewise-r3`

Allow-listed vtysh commands:

- `show ip route`
- `show ip route json`
- `show ip ospf neighbor`
- `show ip ospf neighbor json`
- `show interface`

## Security restrictions

- `subprocess` always uses `shell=False` and argv lists.
- No generic command-execution endpoint.
- Router IDs and container names are allow-listed.
- vtysh commands are allow-listed inside `DockerService` (not only at the route layer).
- API never modifies host routes, interfaces, container lifecycle, or FRR configuration.
- Lab deploy/destroy is script-only, not exposed via the API.
- CORS allows `http://localhost:5173` and `http://127.0.0.1:5173` by default.

## CORS

Default origins (configurable via `CORS_ORIGINS`):

- `http://localhost:5173`
- `http://127.0.0.1:5173`
