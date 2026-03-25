"""Mock feature flags configuration - registered with dependency registry."""
from dataclasses import dataclass, field
from typing import Optional

# Register with registry on module load
try:
    from fast_dashboards.core.registry import registry
    _REGISTRY_AVAILABLE = True
except ImportError:
    _REGISTRY_AVAILABLE = False


@dataclass
class LaunchDarklyConfig:
    enabled: bool = False
    sdk_key: str = ""
    default_user_key: str = ""


@dataclass
class UnleashConfig:
    enabled: bool = False
    url: str = ""
    app_name: str = ""
    instance_id: str = ""
    api_key: str = ""


@dataclass
class FeatureFlagsConfig:
    launchdarkly: LaunchDarklyConfig = field(default_factory=LaunchDarklyConfig)
    unleash: UnleashConfig = field(default_factory=UnleashConfig)


class FeatureFlagsConfiguration:
    _instance: Optional["FeatureFlagsConfiguration"] = None

    @classmethod
    def instance(cls) -> "FeatureFlagsConfiguration":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_config(self) -> FeatureFlagsConfig:
        return FeatureFlagsConfig()


# Auto-register with dependency registry
if _REGISTRY_AVAILABLE:
    registry.register_config("feature_flags", FeatureFlagsConfiguration)
