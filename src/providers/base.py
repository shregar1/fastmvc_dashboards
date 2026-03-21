"""Unified interface for third-party dashboard embed URLs."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class DashboardEmbedProvider(Protocol):
    """Build a time-limited URL for embedding (Metabase, Grafana, custom)."""

    def build_embed_url(self, *, resource_id: str, ttl_seconds: int) -> str:
        """Return a full HTTPS (or HTTP) URL safe to use in an iframe ``src``."""
