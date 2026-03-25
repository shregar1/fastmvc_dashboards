"""Mock start_utils module."""
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Generator


class MockDBSession:
    """Mock database session."""

    async def execute(self, *args, **kwargs):
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class MockRedisSession:
    """Mock Redis session."""

    async def ping(self):
        return False

    async def info(self):
        return {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


@asynccontextmanager
async def db_session() -> AsyncGenerator[MockDBSession, None]:
    """Mock database session context manager."""
    yield MockDBSession()


@asynccontextmanager
async def redis_session() -> AsyncGenerator[MockRedisSession, None]:
    """Mock Redis session context manager."""
    yield MockRedisSession()
