"""RouteWise FastAPI entrypoint."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import analysis, dashboard, firewall, health, lab, networks, routers, topology
from app.core.config import get_settings
from app.db.session import SessionLocal, init_db
from app.services.network_service import NetworkService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("routewise")

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Intelligent Routing Management & Network Path Optimization System. "
        "Includes SQLite software-simulation control plane plus optional read-only "
        "ContainerLab/FRR inspection when the lab is running."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(lab.router)
app.include_router(routers.router)
app.include_router(topology.router)
app.include_router(networks.router)
app.include_router(analysis.router)
app.include_router(dashboard.router)
app.include_router(firewall.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    db = SessionLocal()
    try:
        NetworkService(db).seed_default_triangle()
    finally:
        db.close()
    logger.info("Database ready; default topology seeded if needed")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.info("Validation error on %s: %s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request", "error_code": "validation_error"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Hide unexpected internals from API clients. HTTPException uses FastAPI defaults."""
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "internal_error",
        },
    )


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "health": "/api/health",
        "dashboard": "/api/dashboard/overview",
    }
