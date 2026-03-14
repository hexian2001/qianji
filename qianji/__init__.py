"""
qianji v2 - 浏览器自动化服务
基于 Playwright 的 Python 实现
"""

from .core.browser_manager import BrowserManager
from .models.config import BrowserConfig, ProfileConfig
from .models.snapshot import ElementRef, Snapshot
from .server import BrowserServer

__version__ = "0.2.1"
__all__ = [
    "BrowserServer",
    "BrowserManager",
    "BrowserConfig",
    "ProfileConfig",
    "Snapshot",
    "ElementRef",
]
