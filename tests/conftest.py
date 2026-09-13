"""Shared fixtures for Agent Company AI tests."""

from __future__ import annotations

import asyncio

import pytest
from agent_company_ai.config import CompanyConfig, AutonomousConfig
from agent_company_ai.core.cost_tracker import CostTracker
from agent_company_ai.tools.registry import ToolRegistry, Tool


@pytest.fixture
def config():
    """Return a default CompanyConfig."""
    return CompanyConfig()


@pytest.fixture
def autonomous_config():
    """Return a default AutonomousConfig."""
    return AutonomousConfig()


@pytest.fixture
def cost_tracker():
    """Return a fresh CostTracker."""
    return CostTracker()


@pytest.fixture
def tool_registry():
    """Return an isolated ToolRegistry (not the global singleton)."""
    return ToolRegistry()


@pytest.fixture(autouse=True)
def _ensure_event_loop():
    """Guarantee a usable current event loop for every test.

    Some older tests are driven by the legacy ``asyncio.get_event_loop()``
    helper. ``asyncio.run()`` (used by newer tests) closes the loop on exit, so
    whichever style ran first would break the other depending on file ordering.
    That made the suite order-dependent for no product reason. Ensuring a loop
    here keeps both styles valid and the suite deterministic.
    """
    try:
        asyncio.get_event_loop_policy().get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    yield
