"""Unit tests for configuration models."""

import pytest

from qianji.models.config import BrowserConfig, ProfileConfig


@pytest.mark.unit
class TestProfileConfig:
    """Test ProfileConfig model."""

    def test_default_profile_creation(self) -> None:
        """Test creating a default profile."""
        profile = ProfileConfig(name="default")
        assert profile.name == "default"
        assert profile.headless is True
        assert profile.no_sandbox is False
        assert profile.args == []

    def test_custom_profile_creation(self) -> None:
        """Test creating a custom profile."""
        profile = ProfileConfig(
            name="custom",
            headless=False,
            no_sandbox=True,
            args=["--window-size=1920,1080"],
        )
        assert profile.name == "custom"
        assert profile.headless is False
        assert profile.no_sandbox is True
        assert "--window-size=1920,1080" in profile.args


@pytest.mark.unit
class TestBrowserConfig:
    """Test BrowserConfig model."""

    def test_default_config_creation(self) -> None:
        """Test creating default browser config."""
        config = BrowserConfig()
        assert config.control_port == 18796
        assert config.headless is True
        assert config.no_sandbox is False

    def test_get_profile_existing(self) -> None:
        """Test getting an existing profile."""
        config = BrowserConfig()
        config.profiles["default"] = ProfileConfig(name="default")
        profile = config.get_profile("default")
        assert profile.name == "default"

    def test_get_profile_nonexistent(self) -> None:
        """Test getting a non-existent profile creates new profile."""
        config = BrowserConfig()
        profile = config.get_profile("nonexistent")
        assert profile.name == "nonexistent"
        assert "nonexistent" in config.profiles
