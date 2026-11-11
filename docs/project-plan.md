# Project plan

## Milestone 0 — Initialization (current)

- [x] Project structure and documentation
- [x] FastAPI skeleton with health/lab/router endpoints
- [x] React dashboard shell with API integration
- [x] ContainerLab + FRR configs prepared (not deployed)
- [x] Scripts for env check and lifecycle
- [x] Git repository initialized

## Milestone 1 — Lab bring-up

- Install ContainerLab in WSL if missing
- Deploy triangular OSPF topology
- Verify adjacency: each router has two FULL neighbors
- Confirm loopbacks appear in remote routing tables

## Milestone 2 — Live inspection UX

- Wire dashboard cards to live route/OSPF data
- Topology panel highlights offline vs online nodes
- Clear empty states when lab is destroyed

## Milestone 3 — Path analysis

- Summarize best paths between loopbacks
- Optional cost annotations from OSPF metrics
- Still read-only; no config push from UI

## Milestone 4 — Hardening & demo

- Expand automated tests (mocked Docker)
- Demo script for course presentation
- Final README polish and screenshots

## Non-goals (v1)

- Writing FRR configuration through the API
- Arbitrary command execution
- Changing Windows host networking
- Production multi-tenant deployment
