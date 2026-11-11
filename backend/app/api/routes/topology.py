"""Static topology metadata for the dashboard."""

from fastapi import APIRouter

from app.schemas.router import TopologyResponse
from app.services.routing_service import RoutingService

router = APIRouter(tags=["topology"])


@router.get(
    "/api/topology",
    response_model=TopologyResponse,
    summary="Configured network topology",
)
async def get_topology() -> TopologyResponse:
    """Return designed triangular topology (not live router status)."""
    return RoutingService().get_topology()
