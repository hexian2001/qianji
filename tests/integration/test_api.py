"""Integration tests for HTTP API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from qianji.models.config import BrowserConfig
from qianji.server import BrowserServer


@pytest.mark.integration
class TestAPIEndpoints:
    """Test HTTP API endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client."""
        config = BrowserConfig()
        server = BrowserServer(config)
        app = server.create_app()
        return TestClient(app)

    def test_status_endpoint(self, client: TestClient) -> None:
        """Test GET / status endpoint."""
        response = client.get("/")
        # 503 is acceptable when browser is not running
        assert response.status_code in [200, 503]

    def test_browsers_list_endpoint(self, client: TestClient) -> None:
        """Test GET /browsers endpoint."""
        response = client.get("/browsers")
        # 503 is acceptable when browser is not running
        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_start_browser_endpoint(self, client: TestClient) -> None:
        """Test POST /start endpoint."""
        with patch("qianji.routes.basic.get_browser_registry") as mock_registry:
            mock_reg = MagicMock()
            mock_reg.create_browser = AsyncMock(return_value="browser_1")
            mock_reg._browsers = {}
            mock_registry.return_value = mock_reg

            response = client.post("/start")
            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is True

    def test_navigate_endpoint(self, client: TestClient) -> None:
        """Test POST /api/v1/navigate endpoint."""
        # Skip this test as it requires actual browser
        pytest.skip("Requires actual browser instance")
