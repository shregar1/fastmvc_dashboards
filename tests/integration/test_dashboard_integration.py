"""Integration tests for dashboards with full FastAPI applications."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from typing import Any


class TestHealthDashboardIntegration:
    """Integration tests for health dashboard with real app."""

    def test_health_dashboard_services_structure(self):
        """Test that health dashboard returns proper service structure."""
        from fast_dashboards.operations.health.dashboard import _gather_services
        
        services = _gather_services()
        
        # Should have all expected services
        service_keys = {s["key"] for s in services}
        expected = {"postgres", "redis", "mongo", "cassandra", "scylla", "dynamo", "cosmos", "elasticsearch"}
        assert expected.issubset(service_keys)
        
        # Each service should have required fields
        for svc in services:
            assert "name" in svc
            assert "key" in svc
            assert "enabled" in svc
            assert "status" in svc
            assert "message" in svc
            assert svc["status"] in ["healthy", "unhealthy", "skipped"]


class TestQueuesDashboardIntegration:
    """Integration tests for queues dashboard."""

    def test_queues_dashboard_with_mock_config(self):
        """Test queues dashboard with properly configured mock."""
        from fast_dashboards.core.registry import registry
        from fast_dashboards.operations.queues_dashboard.router import router as queues_router
        
        # Create and register a proper queues config
        class MockRabbitMQConfig:
            enabled = True
            url = "amqp://localhost"
            management_url = "http://localhost:15672"
            username = "guest"
            password = "guest"
        
        class MockSQSConfig:
            enabled = False
            queue_url = ""
            region = ""
            access_key_id = ""
            secret_access_key = ""
        
        class MockQueuesConfig:
            rabbitmq = MockRabbitMQConfig()
            sqs = MockSQSConfig()
        
        class MockQueuesConfiguration:
            _instance = None
            @classmethod
            def instance(cls):
                if cls._instance is None:
                    cls._instance = cls()
                return cls._instance
            def get_config(self):
                return MockQueuesConfig()
        
        registry.register_config("queues", MockQueuesConfiguration)
        
        app = FastAPI()
        app.include_router(queues_router)
        client = TestClient(app)
        
        response = client.get("/dashboard/queues")
        assert response.status_code == 200
        assert "Queues & Jobs" in response.text
        
        # Test state endpoint
        response = client.get("/dashboard/queues/state")
        assert response.status_code == 200
        data = response.json()
        assert "queues" in data
        assert "jobs" in data

    def test_queues_inspection_functions(self):
        """Test queue inspection functions directly."""
        from fast_dashboards.operations.queues_dashboard.router import _inspect_sqs
        
        # Create mock config objects
        class MockSQSConfig:
            enabled = False
            queue_url = ""
            region = ""
        
        # Test disabled SQS returns None
        result = _inspect_sqs(MockSQSConfig())
        assert result is None


class TestTenantsDashboardIntegration:
    """Integration tests for tenants dashboard."""

    def test_tenants_dashboard_with_custom_store(self):
        """Test tenants dashboard with custom tenant store."""
        from fast_dashboards.core.registry import registry
        from fast_dashboards.operations.tenants_dashboard.router import router as tenants_router
        
        # Create custom tenant store
        class MockTenant:
            def __init__(self, id: str, name: str, slug: str, is_active: bool = True):
                self.id = id
                self.name = name
                self.slug = slug
                self.is_active = is_active
                self.config = {"features": ["feature1", "feature2"]}
            
            def to_dict(self):
                return {
                    "id": self.id,
                    "name": self.name,
                    "slug": self.slug,
                    "is_active": self.is_active,
                    "config": self.config
                }
        
        class CustomTenantStore:
            async def list_all(self, active_only: bool = False):
                return [
                    MockTenant("1", "Tenant One", "tenant-one"),
                    MockTenant("2", "Tenant Two", "tenant-two", False),
                ]
            
            def list_all_sync(self):
                return [
                    MockTenant("1", "Tenant One", "tenant-one"),
                ]
        
        registry.register_tenant_store(CustomTenantStore())
        
        app = FastAPI()
        app.include_router(tenants_router)
        client = TestClient(app)
        
        response = client.get("/dashboard/tenants")
        assert response.status_code == 200
        assert "Tenants & Auth" in response.text
        
        response = client.get("/dashboard/tenants/state")
        assert response.status_code == 200
        data = response.json()
        assert "tenants" in data
        assert "flags" in data
        assert "idps" in data
        assert "quotas" in data

    def test_tenants_with_feature_flags_config(self):
        """Test tenants dashboard with feature flags config."""
        from fast_dashboards.core.registry import registry
        from fast_dashboards.operations.tenants_dashboard.router import _load_feature_flags
        
        class MockLaunchDarkly:
            enabled = True
            sdk_key = "test-sdk-key"
            default_user_key = "test-user"
        
        class MockUnleash:
            enabled = False
            url = ""
            app_name = ""
            instance_id = ""
            api_key = ""
        
        class MockFeatureFlagsConfig:
            launchdarkly = MockLaunchDarkly()
            unleash = MockUnleash()
        
        class MockFeatureFlagsConfiguration:
            @classmethod
            def instance(cls):
                return cls()
            def get_config(self):
                return MockFeatureFlagsConfig()
        
        registry.register_config("feature_flags", MockFeatureFlagsConfiguration)
        
        flags = _load_feature_flags()
        
        assert "launchdarkly" in flags
        assert "unleash" in flags
        assert flags["launchdarkly"]["enabled"] is True
        assert "SDK Active" in flags["launchdarkly"]["mode"]
        assert flags["launchdarkly"]["userKey"] == "test-user"


class TestSecretsDashboardIntegration:
    """Integration tests for secrets dashboard."""

    def test_secrets_dashboard_with_custom_config(self):
        """Test secrets dashboard with custom secrets config."""
        from fast_dashboards.core.registry import registry
        from fast_dashboards.operations.secrets_dashboard.router import router as secrets_router
        
        class MockVaultConfig:
            enabled = True
            url = "https://vault.example.com"
            mount_point = "secret"
        
        class MockAWSConfig:
            enabled = True
            region = "us-west-2"
            prefix = "/prod"
        
        class MockSecretsConfig:
            vault = MockVaultConfig()
            aws = MockAWSConfig()
        
        class MockSecretsConfiguration:
            @classmethod
            def instance(cls):
                return cls()
            def get_config(self):
                return MockSecretsConfig()
        
        registry.register_config("secrets", MockSecretsConfiguration)
        
        app = FastAPI()
        app.include_router(secrets_router)
        client = TestClient(app)
        
        response = client.get("/dashboard/secrets")
        assert response.status_code == 200
        assert "Secrets & Configuration" in response.text
        
        response = client.get("/dashboard/secrets/state")
        assert response.status_code == 200
        data = response.json()
        assert "backends" in data
        assert "vault" in data["backends"]
        assert "aws" in data["backends"]
        assert data["backends"]["vault"]["enabled"] is True
        assert data["backends"]["vault"]["url"] == "https://vault.example.com"


class TestWorkflowsDashboardIntegration:
    """Integration tests for workflows dashboard."""

    def test_workflows_dashboard_with_temporal_config(self):
        """Test workflows dashboard with Temporal configuration."""
        from fast_dashboards.core.registry import registry
        from fast_dashboards.operations.workflows_dashboard.router import (
            router as workflows_router
        )
        
        class MockWorkflowsConfig:
            enabled = True
            engine = "temporal"
            temporal_address = "localhost:7233"
            temporal_namespace = "default"
            prefect_api_url = ""
            dagster_grpc_endpoint = ""
        
        class MockWorkflowsConfiguration:
            _instance = None
            @classmethod
            def instance(cls):
                if cls._instance is None:
                    cls._instance = cls()
                return cls._instance
            def get_config(self):
                return MockWorkflowsConfig()
        
        registry.register_config("workflows", MockWorkflowsConfiguration)
        
        app = FastAPI()
        app.include_router(workflows_router)
        client = TestClient(app)
        
        response = client.get("/dashboard/workflows")
        assert response.status_code == 200
        assert "Workflows" in response.text
        
        response = client.get("/dashboard/workflows/state")
        assert response.status_code == 200
        data = response.json()
        assert "engine" in data
        assert data["engine"]["enabled"] is True
        assert data["engine"]["engineName"] == "temporal"
        assert "localhost:7233" in data["engine"]["temporal"]

    def test_workflows_dashboard_with_prefect_config(self):
        """Test workflows dashboard with Prefect configuration."""
        from fast_dashboards.core.registry import registry
        from fast_dashboards.operations.workflows_dashboard.router import router as workflows_router
        
        class MockWorkflowsConfig:
            enabled = True
            engine = "prefect"
            temporal_address = ""
            temporal_namespace = ""
            prefect_api_url = "http://localhost:4200/api"
            dagster_grpc_endpoint = ""
        
        class MockWorkflowsConfiguration:
            @classmethod
            def instance(cls):
                return cls()
            def get_config(self):
                return MockWorkflowsConfig()
        
        registry.register_config("workflows", MockWorkflowsConfiguration)
        
        app = FastAPI()
        app.include_router(workflows_router)
        client = TestClient(app)
        
        response = client.get("/dashboard/workflows/state")
        assert response.status_code == 200
        data = response.json()
        assert data["engine"]["engineName"] == "prefect"
        assert data["engine"]["prefect"] == "http://localhost:4200/api"


class TestCompositeDashboardIntegration:
    """Integration tests for composite dashboard router."""

    def test_all_dashboards_mounted_together(self):
        """Test that all dashboards can be mounted together."""
        from fast_dashboards.core.router import router as composite_router
        
        app = FastAPI()
        app.include_router(composite_router)
        client = TestClient(app)
        
        # Test all dashboard endpoints
        dashboards = [
            ("/dashboard/health", "FastMVC Service Health"),
            ("/dashboard/queues", "Queues & Jobs"),
            ("/dashboard/tenants", "Tenants & Auth"),
            ("/dashboard/secrets", "Secrets & Configuration"),
            ("/dashboard/workflows", "Workflows"),
        ]
        
        for path, expected_text in dashboards:
            response = client.get(path)
            assert response.status_code == 200, f"Failed for {path}"
            assert expected_text in response.text, f"Missing text for {path}"

    def test_all_state_endpoints(self):
        """Test that all state endpoints return JSON."""
        from fast_dashboards.core.router import router as composite_router
        
        app = FastAPI()
        app.include_router(composite_router)
        client = TestClient(app)
        
        state_endpoints = [
            "/dashboard/queues/state",
            "/dashboard/tenants/state",
            "/dashboard/secrets/state",
            "/dashboard/workflows/state",
        ]
        
        for endpoint in state_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Failed for {endpoint}"
            assert response.headers["content-type"] == "application/json", f"Not JSON for {endpoint}"
            data = response.json()
            assert isinstance(data, dict), f"Not a dict for {endpoint}"


class TestRegistryIntegrationWithApp:
    """Integration tests for registry with FastAPI app lifecycle."""

    def test_registry_isolation_between_apps(self):
        """Test that registry can be used with multiple apps."""
        from fast_dashboards.core.registry import DependencyRegistry
        
        reg1 = DependencyRegistry()
        reg2 = DependencyRegistry()
        
        class Config1:
            @classmethod
            def instance(cls):
                return cls()
            def get_config(self):
                return {"app": 1}
        
        class Config2:
            @classmethod
            def instance(cls):
                return cls()
            def get_config(self):
                return {"app": 2}
        
        reg1.register_config("test", Config1)
        reg2.register_config("test", Config2)
        
        assert reg1.get_config("test").instance().get_config()["app"] == 1
        assert reg2.get_config("test").instance().get_config()["app"] == 2
