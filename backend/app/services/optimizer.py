"""Deterministic explainable route recommendation engine."""

from __future__ import annotations

from app.schemas.network import CandidatePath, OptimizeResponse


def _normalize(values: list[float]) -> list[float]:
    """Higher raw value => higher (worse) normalized score 0..100."""
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.0 for _ in values]
    return [((v - lo) / (hi - lo)) * 100.0 for v in values]


def score_paths(paths: list[CandidatePath]) -> list[CandidatePath]:
    available = [p for p in paths if p.available]
    if not available:
        return paths

    lat = [p.total_latency_ms for p in available]
    loss = [p.avg_packet_loss_pct for p in available]
    hops = [float(p.hop_count) for p in available]
    cost = [p.total_cost for p in available]

    n_lat = _normalize(lat)
    n_loss = _normalize(loss)
    n_hops = _normalize(hops)
    n_cost = _normalize(cost)

    scored: list[CandidatePath] = []
    for i, path in enumerate(available):
        L, P, H, C = n_lat[i], n_loss[i], n_hops[i], n_cost[i]
        total = 0.35 * L + 0.25 * P + 0.20 * H + 0.20 * C
        scored.append(
            path.model_copy(
                update={
                    "score": round(total, 3),
                    "score_breakdown": {
                        "L_latency": round(L, 3),
                        "P_packet_loss": round(P, 3),
                        "H_hop_count": round(H, 3),
                        "C_routing_cost": round(C, 3),
                        "S_total": round(total, 3),
                    },
                }
            )
        )
    scored.sort(key=lambda p: (p.score is None, p.score if p.score is not None else 1e9))
    return scored


def recommend(
    network_id: int,
    source: str,
    destination: str,
    candidates: list[CandidatePath],
    protocol_selected: CandidatePath | None,
) -> OptimizeResponse:
    scored = score_paths(candidates)
    recommended = scored[0] if scored else None
    explanation_parts: list[str] = []
    if not recommended:
        explanation_parts.append(
            "No available path between the selected routers under current link/router state."
        )
    else:
        explanation_parts.append(
            f"Recommended path {' → '.join(recommended.hops)} with score "
            f"{recommended.score} (lower is better)."
        )
        bd = recommended.score_breakdown
        explanation_parts.append(
            "Breakdown — "
            f"latency L={bd.get('L_latency')}, "
            f"loss P={bd.get('P_packet_loss')}, "
            f"hops H={bd.get('H_hop_count')}, "
            f"cost C={bd.get('C_routing_cost')}."
        )
        if protocol_selected:
            proto = " → ".join(protocol_selected.hops)
            rec = " → ".join(recommended.hops)
            if proto == rec:
                explanation_parts.append(
                    "Recommended path matches the protocol-selected (lowest configured cost) path."
                )
            else:
                explanation_parts.append(
                    f"Protocol-selected path is {proto}; recommendation differs because "
                    "latency/loss/hops/cost trade-offs favor another available path."
                )
        explanation_parts.append(
            "data_source=software_simulation — not live FRR measurements."
        )

    return OptimizeResponse(
        network_id=network_id,
        source=source,
        destination=destination,
        recommended_path=recommended,
        protocol_selected_path=protocol_selected,
        candidates=scored,
        explanation=" ".join(explanation_parts),
    )
