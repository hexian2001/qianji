"""Unit tests for browser manager."""

import pytest

from qianji.core.browser_manager import BrowserManager
from qianji.models.config import BrowserConfig


@pytest.mark.unit
class TestBrowserManager:
    """Test BrowserManager class."""

    @pytest.fixture
    def config(self) -> BrowserConfig:
        """Create a test config."""
        return BrowserConfig()

    @pytest.fixture
    def manager(self, config: BrowserConfig) -> BrowserManager:
        """Create a browser manager instance."""
        return BrowserManager(config)

    def test_initialization(self, manager: BrowserManager, config: BrowserConfig) -> None:
        """Test browser manager initialization."""
        assert manager.config == config
        assert manager.is_running is False
        assert manager.browser is None
        assert manager.context is None

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self, manager: BrowserManager) -> None:
        """Test stopping when browser is not running."""
        result = await manager.stop()
        assert result is False

    def test_get_status_not_running(self, manager: BrowserManager) -> None:
        """Test getting status when browser is not running."""
        status = manager.get_status()
        assert status["running"] is False
        assert status["profile"] is None
        assert status["tabs"] == 0
