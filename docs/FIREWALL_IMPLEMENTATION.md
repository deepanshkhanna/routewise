# Firewall Implementation

## Architecture

RouteWise firewall policies are **lab-isolated**. They never modify Windows Defender Firewall or the host routing table.

| Layer | Implementation | Status |
|-------|----------------|--------|
| Policy store | SQLite `firewall_rules` | **IMPLEMENTED AND VERIFIED** |
| Evaluation engine | First-match software policy (`FirewallService.test`) | **IMPLEMENTED AND VERIFIED IN SOFTWARE SIMULATION** |
| UI | `/firewall` module | **IMPLEMENTED** |
| nftables on FRR routers | Not present in FRR image | **NOT IMPLEMENTED** (use fw1) |
| Dedicated `fw1` Alpine node | `alpine:3.20` + nftables in `lab/routewise.clab.yml` | **IMPLEMENTED AND VERIFIED IN REAL LAB** |
| `POST .../firewall/apply` | Pushes SQLite rules into `clab-routewise-fw1` | **IMPLEMENTED AND VERIFIED IN REAL LAB** |

Evidence: icmp drop rule on fw1 caused localhost ping 100% loss inside that container only; R1–R3 OSPF/ping unaffected; host Windows firewall untouched.

Software `.../firewall/test` remains the first-match evaluator for UI demos; apply pushes allowlisted nft fragments to fw1.

## API

- `GET /api/networks/{id}/firewall/status`
- `GET|POST /api/networks/{id}/firewall/rules`
- `DELETE /api/networks/{id}/firewall/rules/{rule_id}`
- `POST .../enable` / `.../disable`
- `POST /api/networks/{id}/firewall/test`

## Verified software behavior

1. Create deny ICMP `10.0.12.1 → 10.0.23.2`
2. Test → `allowed=false`, hit_count increments
3. Disable rule → default allow
4. Delete rule

Host firewall unchanged throughout.
