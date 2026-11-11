"""Graph path finding over persisted topology links (software simulation)."""

from __future__ import annotations

from collections import defaultdict, deque

from app.db.models import Link, Router
from app.schemas.network import CandidatePath, PathHop


class PathEngine:
    """Compute candidate paths and a protocol-selected (lowest-cost) path."""

    def __init__(self, routers: list[Router], links: list[Link]) -> None:
        self.routers = {r.name: r for r in routers}
        self.links = links
        self.adj: dict[str, list[tuple[str, Link]]] = defaultdict(list)
        for link in links:
            if not link.enabled or link.status != "up":
                continue
            src_up = self.routers.get(link.source_router)
            dst_up = self.routers.get(link.target_router)
            if not src_up or not dst_up:
                continue
            if src_up.status != "up" or dst_up.status != "up":
                continue
            self.adj[link.source_router].append((link.target_router, link))
            self.adj[link.target_router].append((link.source_router, link))

    def all_simple_paths(self, source: str, destination: str, max_depth: int = 6) -> list[CandidatePath]:
        if source not in self.routers or destination not in self.routers:
            return []
        results: list[CandidatePath] = []

        def dfs(node: str, path: list[str], used_links: list[Link]) -> None:
            if len(path) > max_depth:
                return
            if node == destination and len(path) > 1:
                results.append(self._to_candidate(path, used_links, available=True))
                return
            for neighbor, link in self.adj.get(node, []):
                if neighbor in path:
                    continue
                dfs(neighbor, path + [neighbor], used_links + [link])

        dfs(source, [source], [])
        results.sort(key=lambda p: (p.total_cost, p.total_latency_ms, p.hop_count))
        return results

    def lowest_cost_path(self, source: str, destination: str) -> CandidatePath | None:
        paths = self.all_simple_paths(source, destination)
        return paths[0] if paths else None

    def reachable(self, source: str, destination: str) -> bool:
        if source not in self.adj and source != destination:
            return source == destination
        seen = {source}
        q: deque[str] = deque([source])
        while q:
            node = q.popleft()
            if node == destination:
                return True
            for neighbor, _link in self.adj.get(node, []):
                if neighbor not in seen:
                    seen.add(neighbor)
                    q.append(neighbor)
        return False

    @staticmethod
    def _to_candidate(path: list[str], links: list[Link], available: bool) -> CandidatePath:
        hops: list[PathHop] = []
        total_cost = 0.0
        total_latency = 0.0
        loss_values: list[float] = []
        for i, link in enumerate(links):
            a, b = path[i], path[i + 1]
            hops.append(
                PathHop(
                    from_router=a,
                    to_router=b,
                    link_id=link.id,
                    subnet=link.subnet,
                    cost=link.cost,
                    latency_ms=link.latency_ms,
                    packet_loss_pct=link.packet_loss_pct,
                )
            )
            total_cost += float(link.cost)
            total_latency += float(link.latency_ms)
            loss_values.append(float(link.packet_loss_pct))
        avg_loss = sum(loss_values) / len(loss_values) if loss_values else 0.0
        return CandidatePath(
            hops=path,
            hop_count=max(len(path) - 1, 0),
            total_cost=total_cost,
            total_latency_ms=total_latency,
            avg_packet_loss_pct=avg_loss,
            available=available,
            links=hops,
        )
