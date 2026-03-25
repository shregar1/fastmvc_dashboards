"""Mock queues configuration - registered with dependency registry."""
from dataclasses import dataclass
from typing import Optional

# Register with registry on module load
try:
    from fast_dashboards.core.registry import registry
    _REGISTRY_AVAILABLE = True
except ImportError:
    _REGISTRY_AVAILABLE = False


@dataclass
class RabbitMQConfig:
    enabled: bool = False
    url: str = ""
    management_url: str = ""
    username: str = ""
    password: str = ""


@dataclass
class SQSConfig:
    enabled: bool = False
    queue_url: str = ""
    region: str = ""
    access_key_id: str = ""
    secret_access_key: str = ""


@dataclass
class NATSConfig:
    enabled: bool = False
    url: str = ""


@dataclass
class QueuesConfig:
    rabbitmq: Optional[RabbitMQConfig] = None
    sqs: Optional[SQSConfig] = None
    nats: Optional[NATSConfig] = None

    def __post_init__(self):
        if self.rabbitmq is None:
            self.rabbitmq = RabbitMQConfig()
        if self.sqs is None:
            self.sqs = SQSConfig()
        if self.nats is None:
            self.nats = NATSConfig()


class QueuesConfiguration:
    _instance: Optional["QueuesConfiguration"] = None

    @classmethod
    def instance(cls) -> "QueuesConfiguration":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_config(self) -> QueuesConfig:
        return QueuesConfig()


# Auto-register with dependency registry
if _REGISTRY_AVAILABLE:
    registry.register_config("queues", QueuesConfiguration)
