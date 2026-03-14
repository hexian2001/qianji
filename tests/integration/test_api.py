"""Integration tests for HTTP API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio

from qianji.models.config import BrowserConfig
from qianji.server import BrowserServer


@pytest.mark.integration
class TestAPIEndpoints:
    """Test HTTP API endpoints."""

    @pytest_asyncio.fixture
    async def client(self):
        """Create an async test client."""
        config = BrowserConfig()
        config.enabled = False
        server = BrowserServer(config)
        app = server.create_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client

    @pytest.mark.asyncio
    async def test_status_endpoint(self, client) -> None:
        """Test GET / status endpoint."""
        response = await client.get("/")
        # 503 is acceptable when browser is not running
        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_browsers_list_endpoint(self, client) -> None:
        """Test GET /browsers endpoint."""
        response = await client.get("/browsers")
        # 503 is acceptable when browser is not running
        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_close_browser_endpoint(self, client) -> None:
        """Test POST /browsers/{browser_id}/close endpoint."""
        with patch("qianji.routes.basic.get_browser_registry") as mock_registry:
            mock_reg = MagicMock()
            mock_reg.close_browser = AsyncMock(return_value=True)
            mock_registry.return_value = mock_reg

            response = await client.post("/browsers/browser_1/close")

            assert response.status_code == 200
            assert response.json()["data"] == {
                "browserId": "browser_1",
                "closed": True,
                "purgedProfile": False,
            }
            mock_reg.close_browser.assert_awaited_once_with("browser_1", purge_profile=False)

    @pytest.mark.asyncio
    async def test_navigate_endpoint(self, client) -> None:
        """Test POST /api/v1/navigate endpoint."""
        # Skip this test as it requires actual browser
        pytest.skip("Requires actual browser instance")
