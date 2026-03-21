"""
fastmvc_dashboards – Dashboards extension for FastMVC.

Requires the host app to provide: configurations.*, core.datastores,
start_utils (db_session, redis_session), core.tenancy, services.secrets,
services.workflows, and related modules. Use within a FastMVC application.

Public attributes are loaded on first access so ``import fastmvc_dashboards.layout``
(and tests of layout helpers) work without the full app stack.
"""

from __future__ import annotations

__all__ = [
    "ApiDashboardRouter",
    "DashboardRouter",
    "EndpointSample",
    "HealthDashboardRouter",
    "QueuesDashboardRouter",
    "register_endpoint_sample",
    "SecretsDashboardRouter",
    "TenantsDashboardRouter",
    "WorkflowsDashboardRouter",
]


def __getattr__(name: str):
    if name == "ApiDashboardRouter":
        from .api_dashboard import ApiDashboardRouter

        return ApiDashboardRouter
    if name == "EndpointSample":
        from .api_dashboard import EndpointSample

        return EndpointSample
    if name == "register_endpoint_sample":
        from .api_dashboard import register_endpoint_sample

        return register_endpoint_sample
    if name == "DashboardRouter":
        from .router import router as DashboardRouter

        return DashboardRouter
    if name == "HealthDashboardRouter":
        from .health import HealthDashboardRouter

        return HealthDashboardRouter
    if name == "QueuesDashboardRouter":
        from .queues_dashboard import QueuesDashboardRouter

        return QueuesDashboardRouter
    if name == "SecretsDashboardRouter":
        from .secrets_dashboard import SecretsDashboardRouter

        return SecretsDashboardRouter
    if name == "TenantsDashboardRouter":
        from .tenants_dashboard import TenantsDashboardRouter

        return TenantsDashboardRouter
    if name == "WorkflowsDashboardRouter":
        from .workflows_dashboard import WorkflowsDashboardRouter

        return WorkflowsDashboardRouter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
