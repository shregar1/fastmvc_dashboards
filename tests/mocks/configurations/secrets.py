"""Mock secrets configuration - registered with dependency registry."""
from dataclasses import dataclass, field
from typing import Optional

# Register with registry on module load
try:
    from fast_dashboards.core.registry import registry
    _REGISTRY_AVAILABLE = True
except ImportError:
    _REGISTRY_AVAILABLE = False


@dataclass
class VaultConfig:
    enabled: bool = False
    url: str = ""
    mount_point: str = ""


@dataclass
class AWSConfig:
    enabled: bool = False
    region: str = ""
    prefix: str = ""


@dataclass
class GCPConfig:
    enabled: bool = False
    project_id: str = ""


@dataclass
class AzureConfig:
    enabled: bool = False
    vault_url: str = ""


@dataclass
class SecretsConfig:
    vault: VaultConfig = field(default_factory=VaultConfig)
    aws: AWSConfig = field(default_factory=AWSConfig)
    gcp: GCPConfig = field(default_factory=GCPConfig)
    azure: AzureConfig = field(default_factory=AzureConfig)


class SecretsConfiguration:
    _instance: Optional["SecretsConfiguration"] = None

    @classmethod
    def instance(cls) -> "SecretsConfiguration":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_config(self) -> SecretsConfig:
        return SecretsConfig()


# Auto-register with dependency registry
if _REGISTRY_AVAILABLE:
    registry.register_config("secrets", SecretsConfiguration)
