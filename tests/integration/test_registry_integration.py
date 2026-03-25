"""Integration tests for the dependency registry with various scenarios."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from typing import Any, Dict, Optional


class TestRegistryConfigVariations:
    """Tests for different configuration patterns."""

    def test_registry_with_simple_config(self):
        """Test registry with simple configuration object."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg = DependencyRegistry()
        
        class SimpleConfig:
            @classmethod
            def instance(cls):
                return cls()
            def get_config(self):
                return {"key": "value"}
        
        reg.register_config("simple", SimpleConfig)
        cfg_class = reg.get_config("simple")
        
        assert cfg_class is SimpleConfig
        assert cfg_class.instance().get_config() == {"key": "value"}

    def test_registry_with_nested_config(self):
        """Test registry with deeply nested configuration."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg = DependencyRegistry()
        
        class DatabaseConfig:
            host = "localhost"
            port = 5432
        
        class CacheConfig:
            host = "localhost"
            port = 6379
        
        class AppConfig:
            database = DatabaseConfig()
            cache = CacheConfig()
        
        class NestedConfig:
            @classmethod
            def instance(cls):
                return cls()
            def get_config(self):
                return AppConfig()
        
        reg.register_config("nested", NestedConfig)
        cfg = reg.get_config("nested").instance().get_config()
        
        assert cfg.database.host == "localhost"
        assert cfg.cache.port == 6379

    def test_registry_with_callable_config(self):
        """Test registry with callable-based configuration."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg = DependencyRegistry()
        
        config_data = {"dynamic": "value"}
        
        class DynamicConfig:
            @classmethod
            def instance(cls):
                return cls()
            def get_config(self):
                # Could load from file, env, etc.
                return config_data.copy()
        
        reg.register_config("dynamic", DynamicConfig)
        
        # Modify original data
        config_data["dynamic"] = "changed"
        
        # Config should return current data
        cfg = reg.get_config("dynamic").instance().get_config()
        assert cfg["dynamic"] == "changed"


class TestRegistryDatastoreVariations:
    """Tests for different datastore patterns."""

    def test_registry_with_async_datastore(self):
        """Test registry with async datastore class."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg = DependencyRegistry()
        
        class AsyncMongoStore:
            async def connect(self):
                return True
            async def disconnect(self):
                return True
            async def find(self, query: dict) -> list:
                return []
        
        reg.register_datastore("AsyncMongo", AsyncMongoStore)
        store_class = reg.get_datastore("AsyncMongo")
        
        assert store_class is AsyncMongoStore

    def test_registry_with_singleton_datastore(self):
        """Test registry with singleton datastore pattern."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg = DependencyRegistry()
        
        class SingletonStore:
            _instance = None
            
            def __new__(cls):
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.connected = False
                return cls._instance
            
            def connect(self):
                self.connected = True
        
        reg.register_datastore("Singleton", SingletonStore)
        
        # Get class and create instances
        StoreClass = reg.get_datastore("Singleton")
        instance1 = StoreClass()
        instance2 = StoreClass()
        
        assert instance1 is instance2  # Same instance

    def test_registry_with_factory_datastore(self):
        """Test registry with factory-based datastore."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg = DependencyRegistry()
        
        class ConnectionPool:
            def __init__(self, size: int = 10):
                self.size = size
                self.connections = []
        
        # Register a factory function
        def pool_factory():
            return ConnectionPool(size=20)
        
        reg.register_datastore("Pool", pool_factory)
        
        # When retrieved, it's the factory
        factory = reg.get_datastore("Pool")
        pool = factory()
        
        assert pool.size == 20


class TestRegistrySessionProviders:
    """Tests for session provider patterns."""

    @pytest.mark.asyncio
    async def test_registry_with_async_db_session(self):
        """Test registry with async database session provider."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg = DependencyRegistry()
        
        class AsyncSession:
            async def execute(self, query: str) -> Any:
                return {"result": "data"}
            async def commit(self):
                pass
            async def rollback(self):
                pass
        
        def session_provider():
            return AsyncSession()
        
        reg.register_db_session(session_provider)
        session = reg.get_db_session()
        
        result = await session.execute("SELECT 1")
        assert result == {"result": "data"}

    def test_registry_with_context_manager_session(self):
        """Test registry with context manager-based session."""
        from fast_dashboards.core.registry import DependencyRegistry
        from contextlib import contextmanager
        
        reg = DependencyRegistry()
        
        class ManagedSession:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def execute(self, query: str):
                return []
        
        @contextmanager
        def session_provider():
            yield ManagedSession()
        
        reg.register_db_session(session_provider)
        
        # Provider is callable that returns context manager
        provider = reg._session_providers.get("db")
        assert provider is not None

    def test_registry_with_sync_redis_session(self):
        """Test registry with sync Redis session provider."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg = DependencyRegistry()
        
        class SyncRedis:
            def ping(self) -> bool:
                return True
            def get(self, key: str) -> Optional[str]:
                return None
            def set(self, key: str, value: str):
                pass
        
        reg.register_redis_session(lambda: SyncRedis())
        redis = reg.get_redis_session()
        
        assert redis.ping() is True


class TestRegistryTenantStorePatterns:
    """Tests for tenant store patterns."""

    def test_registry_with_sync_tenant_store(self):
        """Test registry with synchronous tenant store."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg = DependencyRegistry()
        
        class SyncTenantStore:
            def list_all(self) -> list[dict]:
                return [{"id": "1", "name": "Tenant 1"}]
            def get_by_id(self, tenant_id: str) -> Optional[dict]:
                return {"id": tenant_id, "name": "Found"}
        
        reg.register_tenant_store(SyncTenantStore())
        store = reg.get_tenant_store()
        
        tenants = store.list_all()
        assert len(tenants) == 1
        assert tenants[0]["name"] == "Tenant 1"

    def test_registry_with_async_tenant_store(self):
        """Test registry with asynchronous tenant store."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg = DependencyRegistry()
        
        class AsyncTenantStore:
            async def list_all(self) -> list[dict]:
                return [{"id": "1", "name": "Async Tenant"}]
            async def get_by_id(self, tenant_id: str) -> Optional[dict]:
                return {"id": tenant_id, "name": "Async Found"}
        
        reg.register_tenant_store(AsyncTenantStore())
        store = reg.get_tenant_store()
        
        # Store is registered (async behavior tested elsewhere)
        assert store is not None

    def test_registry_with_caching_tenant_store(self):
        """Test registry with caching tenant store."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg = DependencyRegistry()
        
        class CachingTenantStore:
            def __init__(self):
                self._cache = {}
                self._cache_ttl = 300
            
            def list_all(self) -> list[dict]:
                if "tenants" not in self._cache:
                    self._cache["tenants"] = [{"id": "1", "name": "Cached"}]
                return self._cache["tenants"]
            
            def invalidate(self):
                self._cache.clear()
        
        reg.register_tenant_store(CachingTenantStore())
        store = reg.get_tenant_store()
        
        # First call caches
        tenants1 = store.list_all()
        # Second call returns cached
        tenants2 = store.list_all()
        
        assert tenants1 == tenants2


class TestRegistryWithFastAPIIntegration:
    """Tests for registry integration with FastAPI."""

    def test_registry_dependency_injection(self):
        """Test using registry with FastAPI dependency injection."""
        from fast_dashboards.core.registry import DependencyRegistry
        from fastapi import Depends
        
        reg = DependencyRegistry()
        
        class Config:
            @classmethod
            def instance(cls):
                return cls()
            def get_config(self):
                return {"setting": "value"}
        
        reg.register_config("app", Config)
        
        def get_config():
            return reg.get_config("app").instance().get_config()
        
        app = FastAPI()
        
        @app.get("/config")
        def read_config(cfg: dict = Depends(get_config)):
            return cfg
        
        client = TestClient(app)
        response = client.get("/config")
        
        assert response.status_code == 200
        assert response.json() == {"setting": "value"}

    def test_registry_with_app_lifecycle(self):
        """Test registry across app startup/shutdown."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg = DependencyRegistry()
        lifecycle_events = []
        
        class LifecycleConfig:
            @classmethod
            def instance(cls):
                if not hasattr(cls, '_initialized'):
                    cls._initialized = True
                    lifecycle_events.append('init')
                return cls()
            def get_config(self):
                return {"status": "active"}
        
        reg.register_config("lifecycle", LifecycleConfig)
        
        app = FastAPI()
        
        @app.on_event("startup")
        async def startup():
            cfg = reg.get_config("lifecycle")
            if cfg:
                cfg.instance().get_config()
        
        @app.on_event("shutdown")
        async def shutdown():
            lifecycle_events.append('shutdown')
        
        with TestClient(app):
            pass
        
        # Config was accessed during startup
        assert 'init' in lifecycle_events

    def test_registry_multiple_configs_same_app(self):
        """Test multiple configurations in same app."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg = DependencyRegistry()
        
        class DBConfig:
            @classmethod
            def instance(cls):
                return cls()
            def get_config(self):
                return {"host": "db.example.com"}
        
        class CacheConfig:
            @classmethod
            def instance(cls):
                return cls()
            def get_config(self):
                return {"host": "cache.example.com"}
        
        class QueueConfig:
            @classmethod
            def instance(cls):
                return cls()
            def get_config(self):
                return {"host": "queue.example.com"}
        
        reg.register_config("db", DBConfig)
        reg.register_config("cache", CacheConfig)
        reg.register_config("queue", QueueConfig)
        
        app = FastAPI()
        
        @app.get("/configs")
        def get_configs():
            return {
                "db": reg.get_config("db").instance().get_config()["host"],
                "cache": reg.get_config("cache").instance().get_config()["host"],
                "queue": reg.get_config("queue").instance().get_config()["host"],
            }
        
        client = TestClient(app)
        response = client.get("/configs")
        
        assert response.status_code == 200
        data = response.json()
        assert data["db"] == "db.example.com"
        assert data["cache"] == "cache.example.com"
        assert data["queue"] == "queue.example.com"


class TestRegistryEdgeCases:
    """Tests for registry edge cases."""

    def test_registry_with_none_values(self):
        """Test registry handles None values gracefully."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg = DependencyRegistry()
        
        # Registering None should not fail
        reg.register_config("none_config", None)
        result = reg.get_config("none_config")
        
        # Returns None as registered
        assert result is None

    def test_registry_overwrite_existing(self):
        """Test overwriting existing registration."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg = DependencyRegistry()
        
        class Config1:
            value = 1
        
        class Config2:
            value = 2
        
        reg.register_config("test", Config1)
        assert reg.get_config("test").value == 1
        
        # Overwrite
        reg.register_config("test", Config2)
        assert reg.get_config("test").value == 2

    def test_registry_thread_safety_simulation(self):
        """Test registry behavior under concurrent access simulation."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg = DependencyRegistry()
        
        class ThreadSafeConfig:
            _counter = 0
            
            @classmethod
            def instance(cls):
                cls._counter += 1
                return cls()
            
            def get_config(self):
                return {"access_count": self._counter}
        
        reg.register_config("threadsafe", ThreadSafeConfig)
        
        # Simulate multiple accesses
        for _ in range(10):
            cfg = reg.get_config("threadsafe")
            cfg.instance().get_config()
        
        # Counter should reflect all accesses
        assert ThreadSafeConfig._counter == 10

    def test_registry_with_exception_in_config(self):
        """Test registry handles exceptions in config methods."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg = DependencyRegistry()
        
        class BrokenConfig:
            @classmethod
            def instance(cls):
                return cls()
            def get_config(self):
                raise RuntimeError("Config error")
        
        reg.register_config("broken", BrokenConfig)
        
        # Getting config class should work
        cfg_class = reg.get_config("broken")
        assert cfg_class is BrokenConfig
        
        # But calling get_config raises
        with pytest.raises(RuntimeError, match="Config error"):
            cfg_class.instance().get_config()
