"""Mock jobs configuration - registered with dependency registry."""
from dataclasses import dataclass
from typing import Any, Optional

# Register with registry on module load
try:
    from fast_dashboards.core.registry import registry
    _REGISTRY_AVAILABLE = True
except ImportError:
    _REGISTRY_AVAILABLE = False


@dataclass
class CeleryConfig:
    enabled: bool = False
    namespace: str = "celery"
    broker_url: str = ""
    result_backend: str = ""


@dataclass
class RQConfig:
    enabled: bool = False
    redis_url: str = ""
    queue_name: str = "default"


@dataclass
class DramatiqConfig:
    enabled: bool = False


@dataclass
class JobsConfig:
    celery: Optional[CeleryConfig] = None
    rq: Optional[RQConfig] = None
    dramatiq: Optional[DramatiqConfig] = None

    def __post_init__(self):
        if self.celery is None:
            self.celery = CeleryConfig()
        if self.rq is None:
            self.rq = RQConfig()
        if self.dramatiq is None:
            self.dramatiq = DramatiqConfig()


class JobsConfiguration:
    _instance: Optional["JobsConfiguration"] = None

    @classmethod
    def instance(cls) -> "JobsConfiguration":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_config(self) -> JobsConfig:
        return JobsConfig()


# Auto-register with dependency registry
if _REGISTRY_AVAILABLE:
    registry.register_config("jobs", JobsConfiguration)
