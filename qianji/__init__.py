"""
qianji v2 - 完全复刻 OpenClaw Browser
基于 Playwright 的 Python 实现

100% API 兼容 OpenClaw browser 系统
"""

from .core.browser_manager import BrowserManager
from .models.config import BrowserConfig, ProfileConfig
from .models.snapshot import ElementRef, Snapshot
from .server import BrowserServer

__version__ = "2.0.0"
__all__ = [
    "BrowserServer",
    "BrowserManager",
    "BrowserConfig",
    "ProfileConfig",
    "Snapshot",
    "ElementRef",
]
