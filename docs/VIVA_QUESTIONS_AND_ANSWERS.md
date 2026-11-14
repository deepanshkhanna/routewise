# RouteWise — Viva Questions and Answers

Answers are short, technically correct, and aligned with **what the repo actually implements**.

---

## A. Project fundamentals

**1. What is RouteWise?**  
An intelligent routing management and path optimization system: React dashboard + FastAPI control plane + SQLite software topology, with an optional ContainerLab FRRouting lab for real OSPF inspection.

**2. What problem does it solve?**  
It makes path selection, multi-metric recommendation, and link-failure recovery visible and safe to demonstrate for learning, without changing the host OS routing table.

**3. Why did you build it?**  
As a Computer Networks project to connect theory (graphs, OSPF, failover) with a working UI and an optional real FRR lab.

**4. What makes it different from a plain packet tracer?**  
It has a real FastAPI backend, persisted topology/events, an explainable optimization formula, allow-listed Docker/FRR inspection, and explicit SOFTWARE_SIMULATION vs REAL_LAB modes.

**5. What did you fully implement vs simulate?**  
Fully implemented software: topology CRUD-ish seed, paths, optimize, link/router fail flags, events, static routes DB, firewall policy test, UI modules, pytest. Real lab: ContainerLab deploy + FRR OSPF verified when environment allows. Simulated: path “ping/traceroute”, optimization scoring, UI Analytics charts.

**6. What is the default topology?**  
Three routers R1–R2–R3 in a triangle with subnets 10.0.12.0/30, 10.0.23.0/30, 10.0.13.0/30 and loopbacks 192.168.1.1/32, 192.168.2.2/32, 192.168.3.3/32.

**7. Does RouteWise change Windows networking?**  
No. Lab traffic stays inside Docker/ContainerLab. Host routing and Windows Firewall are not modified by design.

---

## B. Computer networking

**8. What is routing?**  
Selecting the next hop / path to deliver IP packets toward a destination prefix.

**9. Routing vs switching?**  
Switching forwards frames in L2 domains using MAC tables. Routing forwards packets between L3 networks using routing tables.

**10. What is a routing table?**  
A list of destinations (prefixes) with next hop, outgoing interface, protocol/source, and metric/cost.

**11. What is a next hop?**  
The adjacent router IP (or interface) where a packet should be sent for a given destination.

**12. What is packet loss?**  
Fraction of packets that fail to reach the destination; in our software model it is a configured link attribute averaged along a path.

**13. What is latency?**  
Delay to traverse a path; we sum per-link `latency_ms` in the software engine.

**14. What is hop count?**  
Number of links (edges) in the path; `len(routers)-1` in our candidates.

**15. What is traceroute conceptually?**  
Listing intermediate hops toward a destination. Our API traceroute follows the software lowest-cost path and labels itself `software_simulation`.

---

## C. Routing protocols

**16. What routing protocols appear in RouteWise?**  
Static (DB + FRR staticd enabled), OSPF (primary verified), RIP v2 (configured in lab `daemons`/`frr.conf` and probeable), BGP (not enabled — `bgpd=no`).

**17. What is routing convergence?**  
The process after a topology change until routers agree on consistent forwarding paths again.

**18. Why use protocols instead of only static routes?**  
Static does not adapt to failures automatically; dynamic protocols reconverge when links/routers change.

---

## D. Static routing, RIP, and OSPF

**19. How do static routes work in your app?**  
UI/API stores them in SQLite (`static_routes`). That does not automatically install them into FRR. FRR has `staticd=yes` for lab capability, but the demo’s static manager is software DB.

**20. What is RIP v2?**  
A distance-vector IGP using hop count (max 15), multicast updates, classless prefixes. We configure `router rip` / `ripd=yes` in lab files and probe with `show ip rip`.

**21. How does OSPF determine a route?**  
Link-state: routers flood LSAs, each builds the same topology database, runs Dijkstra SPF, installs lowest-cost routes into the RIB/FIB.

**22. What OSPF area do you use?**  
Area 0 (backbone) on the triangle.

**23. Why FRR instead of coding OSPF yourself?**  
Correct OSPF is complex; FRR gives real protocol behavior. Our contribution is management, visualization, simulation, and safe inspection — not reimplementing OSPF.

**24. Is BGP implemented?**  
No. Daemon disabled; UI marks it as future extension.

---

## E. Network topology

**25. Why a triangle?**  
Minimum topology with redundancy: two disjoint paths between any pair (direct vs via third router), ideal for failover demos.

**26. What are point-to-point OSPF links here?**  
`ip ospf network point-to-point` on eth interfaces — no DR/BDR election needed on those links.

**27. How does SQLite topology relate to ContainerLab?**  
Same router names and IPv4 addressing so software demos and real lab tell one story.

---

## F. Graph algorithms

**28. How is the network a graph?**  
Routers = nodes; links = undirected edges when enabled and up.

**29. How do you find paths?**  
DFS enumeration of simple paths (`PathEngine.all_simple_paths`, max depth 6).

**30. What is the “protocol-selected” path in software?**  
Among candidates, the one with lowest total `cost` (tie-break latency, then hops).

**31. How are alternate paths found after failure?**  
Failed links are removed from adjacency; DFS only returns remaining paths.

**32. Shortest vs optimal path in your project?**  
“Shortest” here ≈ lowest configured cost (and/or fewest hops). “Optimal/recommended” ≈ lowest weighted multi-metric score S.

---

## G. Route optimization

**33. What is the recommendation formula?**  
`S = 0.35L + 0.25P + 0.20H + 0.20C` where L,P,H,C are normalized 0–100 scores for latency, packet loss, hop count, and routing cost.

**34. Why normalize?**  
Raw units differ (ms vs % vs hops vs cost). Min–max normalization puts them on one scale among current candidates.

**35. Why weighted scoring?**  
To express preference: latency weighted highest (0.35), then loss (0.25), then hops and cost (0.20 each).

**36. Why is lowest score preferred?**  
Each normalized component is “worse when higher,” so smaller S means better path.

**37. How are unavailable links handled?**  
Excluded from adjacency (`enabled` false / `status != up` / router down), so they never enter candidates.

**38. Does recommendation change FRR?**  
No. Advisory only; explanation sets `data_source=software_simulation`.

**39. Worked example (default seed R1→R3)?**  
Direct: lat 4, loss 0, hops 1, cost 15 → all normalized 0 → S=0.  
Via R2: lat 17, loss 0.75, hops 2, cost 20 → all normalized 100 → S=100.  
Recommend direct; lowest-cost also direct.

---

## H. Backend and FastAPI

**40. Why FastAPI?**  
Fast to build typed REST APIs, automatic OpenAPI docs, Pydantic validation, good async story (we use sync SQLAlchemy services under typical course load).

**41. What does Pydantic do here?**  
Validates request/response schemas so clients get predictable JSON.

**42. Main backend entrypoint?**  
`backend/app/main.py` — registers routers, CORS, seeds DB on startup.

**43. How is lab mode chosen?**  
`probe_infrastructure()`: if R1/R2/R3 containers all running → `REAL_LAB`, else software mode for app features.

**44. How do you keep Docker safe?**  
Allow-listed containers and vtysh show commands; reject arbitrary argv; timeouts; WSL bridge without opening unauthenticated Docker TCP.

---

## I. Frontend and React

**45. Why React + Vite?**  
Fast SPA development and hot reload; Vite proxies `/api` to the backend.

**46. What is React Flow used for?**  
Interactive topology canvas (nodes/edges, path highlight).

**47. How does the UI call the backend?**  
Only through `frontend/src/services/api.js` fetch helpers.

**48. Name the main pages.**  
Overview, Topology, Routing, Paths, Optimize, Simulation, Firewall, Analytics, Events, Reports, Settings.

---

## J. Database

**49. Why SQLite?**  
Zero-ops local DB for a course project; enough for one topology lab and events; easy to reset.

**50. Important tables?**  
`networks`, `routers`, `links`, `events`, `static_routes`, `firewall_rules`.

**51. Where is the DB created?**  
SQLAlchemy `init_db()` / `create_all` on startup (`app/db/session.py`).

---

## K. Docker and ContainerLab

**52. What is ContainerLab?**  
A tool to deploy network lab topologies as containers from a YAML file (`lab/routewise.clab.yml`).

**53. Why Docker/WSL?**  
FRR nodes need Linux networking namespaces; on Windows we typically use Docker Desktop’s WSL2 engine; our `wsl_bridge` helps when the Windows named pipe is down.

**54. What if Docker is unavailable?**  
Software simulation continues; lab APIs report unavailable; UI mode stays SOFTWARE_SIMULATION.

**55. Does destroy wipe your PC Docker?**  
No — destroy targets the RouteWise topology file/lab, not a global prune of all containers (provider uses clab destroy on this topology).

---

## L. FRRouting

**56. What is FRRouting?**  
Open-source routing suite (zebra + protocol daemons) widely used in labs and soft routers.

**57. How do you read routes?**  
`docker exec clab-routewise-rX vtysh -c "show ip route json"` (or text) via `DockerService`/`RoutingService`.

**58. What was a real bug you hit?**  
CRLF line endings in FRR configs broke `watchfrr`/`daemons` parsing; fixed by forcing LF (see engineering docs).

**59. Which protocol was verified end-to-end in lab?**  
OSPF: Full neighbors, ping, and failover via interface down — documented in `END_TO_END_TEST_REPORT.md`.

---

## M. Firewall

**60. How does your firewall work?**  
Rules in SQLite; `test` does first-match allow/deny in software; `apply` can push nftables rules into isolated `fw1` when REAL_LAB.

**61. Is it stateful like iptables conntrack NGFW?**  
We implement simple filter rules with counters — do not claim full commercial stateful firewall features.

**62. Why not nftables on FRR nodes?**  
FRR container image lacks nftables binaries; `fw1` Alpine node is the real-lab apply target.

**63. Does firewall test touch Windows Defender?**  
No.

---

## N. Testing and security

**64. How do you test?**  
pytest with mocked Docker responses; ~32 tests covering health, networks/paths/optimize/failover, firewall, lab API, allow-list rejection.

**65. Are real API calls required for unit tests?**  
No — Docker/FRR are mocked.

**66. Security highlights?**  
Allow-list commands, no frontend Docker access, generic 500s, validated firewall endpoints, lab isolation from host firewall/routes.

---

## O. Limitations and future improvements

**67. What requires Docker?**  
Live container inspect, vtysh reads, lab deploy/destroy, fw1 apply.

**68. What requires ContainerLab?**  
Orchestrated deploy of the YAML topology (you could run equivalent containers manually, but the project uses clab).

**69. What happens without the network lab?**  
Full software teaching path: topology, paths, optimize, simulation, events, firewall test.

**70. What would you implement next?**  
Optional real interface-down from Simulation via provider; push static routes to FRR safely; deeper RIP/BGP labs; replace illustrative Analytics with real metrics; Playwright E2E.

---

## Difficult cross-questions

**71. Is your Path Explorer showing OSPF’s real choice?**  
Not by itself. It shows software lowest-cost over configured link costs. Live OSPF choice is inspected via FRR route/neighbor APIs when the lab runs. Costs in SQLite are teaching metrics and may not equal FRR OSPF interface costs unless you keep them aligned.

**72. If recommendation ≠ protocol-selected, who is “correct”?**  
Different objectives. Protocol-selected minimizes configured cost. Recommendation minimizes weighted latency/loss/hops/cost. Neither silently rewrites the other.

**73. What happens if a router fails in software?**  
`status=down` removes it from usable adjacency; paths needing that router disappear; critical event logged.

**74. What happens if a router fails in real OSPF?**  
Neighbors time out, LSAs update, SPF recomputes, routes via remaining paths if redundancy exists.

**75. Why weighted 0.35/0.25/0.20/0.20 specifically?**  
A deliberate explainable preference order emphasizing delay, then reliability, then path length and administrative cost — simple enough to defend in viva without claiming ML optimality.

**76. Could you use Dijkstra instead of DFS?**  
Yes for single best weighted path. We DFS all simple paths because the UI must list **candidates** for comparison on a tiny triangle (depth capped).

**77. How do you prevent command injection via router id?**  
Router ids validated against allow-list `{R1,R2,R3}`; container names derived from inventory; vtysh commands must be in `ALLOWED_VTYSH_COMMANDS`.

**78. What is `data_source` on events?**  
Provenance label (`software_simulation`, `real_lab`, etc.) so demos stay honest about origin.

**79. Why is Analytics “fake”?**  
UI placeholder trends for presentation polish; subtitle/code label them illustrative/synthetic. Real metrics would need exporters/telemetry not in scope.

**80. If faculty asks “is RIP working?”**  
Answer: “RIP daemon and `router rip` are configured in lab files and the API can probe `show ip rip`. Our fully documented verified failover demo is OSPF. I will not over-claim RIP verification beyond probe/config status.”
