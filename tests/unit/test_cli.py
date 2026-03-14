"""Unit tests for CLI HTTP client behavior."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from qianji.cli import QianjiClient


@pytest.mark.unit
class TestQianjiClient:
    """Test QianjiClient request routing."""

    @pytest.mark.asyncio
    async def test_close_browser_uses_resource_path(self) -> None:
        """close_browser should call the canonical resource close endpoint."""
        client = QianjiClient("http://localhost:18796")
        await client.client.aclose()

        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"ok": True, "data": {"browserId": "browser_1"}}

        mock_http_client = MagicMock()
        mock_http_client.post = AsyncMock(return_value=response)
        mock_http_client.aclose = AsyncMock(return_value=None)
        client.client = mock_http_client

        result = await client.close_browser("browser_1")

        mock_http_client.post.assert_awaited_once_with(
            "http://localhost:18796/browsers/browser_1/close"
        )
        assert result == {"ok": True, "data": {"browserId": "browser_1"}}

        await client.close()
