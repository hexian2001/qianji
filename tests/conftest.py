"""Pytest configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_browser_manager() -> AsyncGenerator[MagicMock, None]:
    """Mock browser manager fixture."""
    with patch("qianji.core.browser_manager.BrowserManager") as mock:
        instance = MagicMock()
        instance.start = AsyncMock(return_value=True)
        instance.stop = AsyncMock(return_value=True)
        instance.is_running = True
        mock.return_value = instance
        yield instance


@pytest.fixture
async def mock_playwright() -> AsyncGenerator[MagicMock, None]:
    """Mock playwright fixture."""
    with patch("qianji.core.pw_client.async_playwright") as mock:
        pw = MagicMock()
        browser = MagicMock()
        context = MagicMock()
        page = MagicMock()

        browser.new_context = AsyncMock(return_value=context)
        context.new_page = AsyncMock(return_value=page)
        pw.chromium.launch = AsyncMock(return_value=browser)

        mock.return_value.__aenter__ = AsyncMock(return_value=pw)
        mock.return_value.__aexit__ = AsyncMock(return_value=None)

        yield pw


@pytest.fixture
def sample_config() -> dict:
    """Sample configuration fixture."""
    return {
        "port": 18796,
        "headless": True,
        "no_sandbox": False,
        "idle_timeout": 3600,
        "max_lifetime": 3600,
    }
