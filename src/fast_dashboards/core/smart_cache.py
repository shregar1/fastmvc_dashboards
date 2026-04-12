"""Backward-compatible re-exports; implementation is :mod:`fast_platform.caching`."""

from __future__ import annotations

from fast_platform.caching import (
    CacheBackend,
    CacheConfig,
    CacheEntry,
    CacheInvalidator,
    CacheStrategy,
    InMemoryCacheBackend,
    InvalidationEvent,
    SmartCacheManager,
    cache_invalidator,
    smart_cache,
)

__all__ = [
    "SmartCacheManager",
    "smart_cache",
    "CacheConfig",
    "CacheStrategy",
    "InvalidationEvent",
    "CacheEntry",
    "CacheBackend",
    "InMemoryCacheBackend",
    "CacheInvalidator",
    "cache_invalidator",
]
