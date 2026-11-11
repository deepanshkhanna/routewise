"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the RouteWise API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="RouteWise", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )
    docker_timeout_seconds: int = Field(default=10, alias="DOCKER_TIMEOUT_SECONDS")
    lab_name: str = Field(default="routewise", alias="LAB_NAME")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


# Static inventory for the three-router lab (read-only metadata).
# Container names follow ContainerLab: clab-<lab_name>-<node>
ROUTER_INVENTORY: dict[str, dict[str, str]] = {
    "R1": {
        "loopback": "192.168.1.1/32",
        "protocol": "OSPF",
        "container_suffix": "r1",
    },
    "R2": {
        "loopback": "192.168.2.2/32",
        "protocol": "OSPF",
        "container_suffix": "r2",
    },
    "R3": {
        "loopback": "192.168.3.3/32",
        "protocol": "OSPF",
        "container_suffix": "r3",
    },
}

ALLOWED_ROUTER_IDS = frozenset(ROUTER_INVENTORY.keys())

# Predefined read-only vtysh commands only (never accept from API clients).
ALLOWED_VTYSH_COMMANDS = frozenset(
    {
        "show ip route",
        "show ip route json",
        "show ip ospf neighbor",
        "show ip ospf neighbor json",
        "show ip rip",
        "show ip rip status",
        "show interface",
        "show interface brief",
    }
)

# Static designed topology (separate from live Docker status).
TOPOLOGY_LINKS: list[dict[str, object]] = [
    {
        "id": "r1-r2",
        "source": "R1",
        "target": "R2",
        "subnet": "10.0.12.0/30",
        "endpoints": {"R1": "10.0.12.1/30", "R2": "10.0.12.2/30"},
    },
    {
        "id": "r2-r3",
        "source": "R2",
        "target": "R3",
        "subnet": "10.0.23.0/30",
        "endpoints": {"R2": "10.0.23.1/30", "R3": "10.0.23.2/30"},
    },
    {
        "id": "r1-r3",
        "source": "R1",
        "target": "R3",
        "subnet": "10.0.13.0/30",
        "endpoints": {"R1": "10.0.13.1/30", "R3": "10.0.13.2/30"},
    },
]
