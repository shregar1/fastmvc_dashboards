"""
fastmvc_dashboards

Dashboards extension for FastMVC.

This package re-exports the composite DashboardRouter and individual
dashboard routers from the existing monolithic FastMVC codebase.
"""

from __future__ import annotations

from fastapi import APIRouter

from core.dashboard.router import router as DashboardRouter  # type: ignore
from core.health.dashboard import router as HealthDashboardRouter  # type: ignore
from core.api_dashboard import ApiDashboardRouter  # type: ignore
from core.queues_dashboard import QueuesDashboardRouter  # type: ignore
from core.tenants_dashboard import TenantsDashboardRouter  # type: ignore
from core.secrets_dashboard import SecretsDashboardRouter  # type: ignore
from core.workflows_dashboard import WorkflowsDashboardRouter  # type: ignore

__all__ = [
    "APIRouter",
    "DashboardRouter",
    "HealthDashboardRouter",
    "ApiDashboardRouter",
    "QueuesDashboardRouter",
    "TenantsDashboardRouter",
    "SecretsDashboardRouter",
    "WorkflowsDashboardRouter",
]

