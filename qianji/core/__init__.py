"""
Core 包 - 共享单例
"""

from .browser_manager import BrowserManager
from .browser_registry import BrowserRegistry
from .pw_client import PlaywrightClient, SnapshotCache, snapshot_cache
from .tab_manager import TabManager

# 全局单例 PlaywrightClient（所有路由共享）
_pw_client: PlaywrightClient = PlaywrightClient()


def get_pw_client() -> PlaywrightClient:
    """获取全局 PlaywrightClient 单例"""
    return _pw_client


def get_snapshot_cache() -> SnapshotCache:
    """获取全局快照缓存"""
    return snapshot_cache
