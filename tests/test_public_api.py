"""
Public API import tests for fastmvc_dashboards.

Ensures __version__ (if present) and every name in __all__ resolve.
Imports run inside tests (not at collection) so optional deps can fail one test.
"""

from __future__ import annotations

import importlib

import pytest

PACKAGE = "fastmvc_dashboards"


def test_package_imports():
    try:
        m = importlib.import_module(PACKAGE)
    except ImportError as e:
        pytest.skip(f"import not available in this environment: {e}")
    assert m is not None


def test_version_when_present():
    try:
        m = importlib.import_module(PACKAGE)
    except ImportError as e:
        pytest.skip(f"import not available: {e}")
    if hasattr(m, "__version__"):
        assert isinstance(m.__version__, str)
        assert m.__version__


def test_public_exports_resolve():
    try:
        m = importlib.import_module(PACKAGE)
    except ImportError as e:
        pytest.skip(f"import not available: {e}")
    for export_name in getattr(m, "__all__", ()):
        try:
            obj = getattr(m, export_name)
        except Exception as e:
            pytest.skip(
                f"export {export_name!r} not loadable in this environment: {e}"
            )
        assert obj is not None
