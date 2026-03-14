"""
浏览器注册表 - 管理多个浏览器实例
支持 N 浏览器 × M 页面架构
"""

import asyncio
import os
import shutil
from dataclasses import dataclass, field
from typing import Any

from ..models.config import BrowserConfig
from .browser_manager import BrowserManager


@dataclass
class BrowserInstance:
    """浏览器实例包装器"""

    browser_id: str
    manager: BrowserManager
    profile_name: str
    user_data_dir: str
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    last_activity_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    # 实例级别的生命周期配置（覆盖全局配置）
    idle_timeout: float | None = None
    max_lifetime: float | None = None


class BrowserRegistry:
    """浏览器注册表 - 管理多个浏览器实例

    支持生命周期管理：
    - idle_timeout: 空闲超时时间（秒），超过此时间未活动的浏览器将被自动关闭
    - max_lifetime: 最大生命周期（秒），超过此时间的浏览器将被强制关闭
    """

    def __init__(
        self,
        config: BrowserConfig,
        idle_timeout: float | None = None,
        max_lifetime: float | None = None,
        cleanup_interval: float = 60.0,
    ):
        self.config = config
        self._browsers: dict[str, BrowserInstance] = {}
        self._counter = 0
        self._lock = asyncio.Lock()

        # 生命周期配置
        self.idle_timeout = idle_timeout  # 空闲超时（秒）
        self.max_lifetime = max_lifetime  # 最大生命周期（秒）
        self.cleanup_interval = cleanup_interval  # 清理检查间隔（秒）

        # 后台清理任务
        self._cleanup_task: asyncio.Task | None = None
        self._running = False

    def _generate_browser_id(self) -> str:
        """生成唯一的浏览器ID"""
        self._counter += 1
        return f"browser_{self._counter}"

    def _get_user_data_dir(self, browser_id: str, profile_name: str) -> str:
        """为每个浏览器实例生成独立的用户数据目录"""
        base_dir = os.path.expanduser("~/.qianji/user_data")
        # 使用 browser_id 作为目录名，确保每个实例独立
        user_data_dir = os.path.join(base_dir, f"{profile_name}_{browser_id}")
        os.makedirs(user_data_dir, exist_ok=True)
        return user_data_dir

    async def create_browser(
        self,
        profile_name: str | None = None,
        browser_id: str | None = None,
        idle_timeout: float | None = None,
        max_lifetime: float | None = None,
        headless: bool | None = None,
        no_sandbox: bool | None = None,
        args: list[str] | None = None,
    ) -> str:
        """
        创建新浏览器实例

        Args:
            profile_name: 配置文件名称
            browser_id: 指定的浏览器ID（可选，自动生成）
            idle_timeout: 空闲超时时间（秒），默认使用全局配置
            max_lifetime: 最大生命周期（秒），默认使用全局配置
            headless: 是否使用无头模式，默认使用全局配置
            no_sandbox: 是否禁用沙箱，默认使用全局配置
            args: 额外的浏览器启动参数

        Returns:
            browser_id: 浏览器实例ID
        """
        async with self._lock:
            # 生成或验证 browser_id
            if browser_id is None:
                browser_id = self._generate_browser_id()
            elif browser_id in self._browsers:
                raise ValueError(f"Browser ID already exists: {browser_id}")

            profile = profile_name or self.config.default_profile

            # 为每个实例创建独立的用户数据目录
            user_data_dir = self._get_user_data_dir(browser_id, profile)

            # 创建临时配置（如果需要覆盖 headless/no_sandbox/args）
            import copy

            config = copy.deepcopy(self.config)
            if headless is not None:
                config.headless = headless
            if no_sandbox is not None:
                config.no_sandbox = no_sandbox
            if args:
                # 将额外参数添加到所有配置文件
                for profile_config in config.profiles.values():
                    profile_config.args.extend(args)

            # 创建新的 BrowserManager，传入独立的用户数据目录
            manager = BrowserManager(config)

            # 启动浏览器（使用独立的用户数据目录）
            await manager.start(profile, user_data_dir=user_data_dir)

            # 使用实例配置或回退到全局配置
            instance_idle_timeout = idle_timeout if idle_timeout is not None else self.idle_timeout
            instance_max_lifetime = max_lifetime if max_lifetime is not None else self.max_lifetime

            # 注册实例
            instance = BrowserInstance(
                browser_id=browser_id,
                manager=manager,
                profile_name=profile,
                user_data_dir=user_data_dir,
                idle_timeout=instance_idle_timeout,
                max_lifetime=instance_max_lifetime,
            )
            self._browsers[browser_id] = instance

            return browser_id

    async def get_browser(self, browser_id: str) -> BrowserManager | None:
        """获取浏览器管理器"""
        instance = self._browsers.get(browser_id)
        if instance and instance.manager.is_running:
            # 更新最后活动时间
            instance.last_activity_at = asyncio.get_event_loop().time()
            return instance.manager
        return None

    def update_activity(self, browser_id: str) -> bool:
        """更新浏览器最后活动时间

        Args:
            browser_id: 浏览器ID

        Returns:
            bool: 是否成功更新
        """
        instance = self._browsers.get(browser_id)
        if instance:
            instance.last_activity_at = asyncio.get_event_loop().time()
            return True
        return False

    def get_browser_age(self, browser_id: str) -> float | None:
        """获取浏览器已运行时间（秒）

        Args:
            browser_id: 浏览器ID

        Returns:
            float: 运行时间（秒），如果不存在返回 None
        """
        instance = self._browsers.get(browser_id)
        if instance:
            return asyncio.get_event_loop().time() - instance.created_at
        return None

    def get_browser_idle_time(self, browser_id: str) -> float | None:
        """获取浏览器空闲时间（秒）

        Args:
            browser_id: 浏览器ID

        Returns:
            float: 空闲时间（秒），如果不存在返回 None
        """
        instance = self._browsers.get(browser_id)
        if instance:
            return asyncio.get_event_loop().time() - instance.last_activity_at
        return None

    async def start_cleanup_task(self):
        """启动后台清理任务"""
        if self._cleanup_task is not None:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup_task(self):
        """停止后台清理任务"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_loop(self):
        """后台清理循环"""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired_browsers()
            except asyncio.CancelledError:
                break
            except Exception:
                # 清理出错不应中断循环
                pass

    async def _cleanup_expired_browsers(self):
        """清理过期浏览器（支持实例级别配置）"""
        now = asyncio.get_event_loop().time()
        to_close = []

        async with self._lock:
            for browser_id, instance in list(self._browsers.items()):
                if not instance.manager.is_running:
                    continue

                # 使用实例级别的 max_lifetime，如果没有则使用全局配置
                max_lifetime = (
                    instance.max_lifetime
                    if instance.max_lifetime is not None
                    else self.max_lifetime
                )
                if max_lifetime is not None:
                    age = now - instance.created_at
                    if age >= max_lifetime:
                        to_close.append((browser_id, "max_lifetime"))
                        continue

                # 使用实例级别的 idle_timeout，如果没有则使用全局配置
                idle_timeout = (
                    instance.idle_timeout
                    if instance.idle_timeout is not None
                    else self.idle_timeout
                )
                if idle_timeout is not None:
                    idle_time = now - instance.last_activity_at
                    if idle_time >= idle_timeout:
                        to_close.append((browser_id, "idle_timeout"))

        # 在锁外关闭浏览器
        for browser_id, reason in to_close:
            try:
                await self.close_browser(browser_id)
            except Exception:
                pass

    async def ensure_browser(
        self, browser_id: str | None = None, profile_name: str | None = None
    ) -> tuple[str, BrowserManager]:
        """
        确保浏览器实例存在并运行

        Args:
            browser_id: 浏览器ID（可选）
            profile_name: 配置文件名称（创建新实例时使用）

        Returns:
            (browser_id, manager): 浏览器ID和管理器
        """
        async with self._lock:
            # 如果指定了 browser_id，尝试获取
            if browser_id:
                instance = self._browsers.get(browser_id)
                if instance:
                    if not instance.manager.is_running:
                        # 重新启动
                        await instance.manager.start()
                    # 更新活动时间
                    instance.last_activity_at = asyncio.get_event_loop().time()
                    return browser_id, instance.manager

            # 检查是否有任何运行的浏览器
            for bid, instance in self._browsers.items():
                if instance.manager.is_running:
                    # 更新活动时间
                    instance.last_activity_at = asyncio.get_event_loop().time()
                    return bid, instance.manager

        # 在锁外创建新浏览器，避免 ensure_browser -> create_browser 重入死锁
        new_browser_id = await self.create_browser(profile_name)
        return new_browser_id, self._browsers[new_browser_id].manager

    async def close_browser(self, browser_id: str, *, purge_profile: bool = False) -> bool:
        """关闭指定浏览器"""
        async with self._lock:
            instance = self._browsers.get(browser_id)
            if not instance:
                return False

            user_data_dir = instance.user_data_dir
            await instance.manager.stop()
            del self._browsers[browser_id]

        if purge_profile and user_data_dir:
            shutil.rmtree(user_data_dir, ignore_errors=True)
        return True

    async def close_all(self):
        """关闭所有浏览器"""
        async with self._lock:
            for instance in list(self._browsers.values()):
                await instance.manager.stop()
            self._browsers.clear()

    def list_browsers(self) -> list[dict[str, Any]]:
        """列出所有浏览器实例，包含生命周期信息"""
        now = asyncio.get_event_loop().time()
        return [
            {
                "browserId": bid,
                "profileName": instance.profile_name,
                "running": instance.manager.is_running,
                "tabs": len(instance.manager.tab_manager.tabs),
                "userDataDir": instance.manager._user_data_dir,
                # 生命周期信息
                "createdAt": instance.created_at,
                "lastActivityAt": instance.last_activity_at,
                "age": now - instance.created_at,
                "idleTime": now - instance.last_activity_at,
                # 实例级别的生命周期配置
                "lifecycle": {
                    "idleTimeout": instance.idle_timeout,
                    "maxLifetime": instance.max_lifetime,
                },
            }
            for bid, instance in self._browsers.items()
        ]

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息，包含生命周期配置"""
        total_browsers = len(self._browsers)
        running_browsers = sum(1 for b in self._browsers.values() if b.manager.is_running)
        total_tabs = sum(len(b.manager.tab_manager.tabs) for b in self._browsers.values())

        return {
            "totalBrowsers": total_browsers,
            "runningBrowsers": running_browsers,
            "totalTabs": total_tabs,
            # 生命周期配置
            "lifecycle": {
                "idleTimeout": self.idle_timeout,
                "maxLifetime": self.max_lifetime,
                "cleanupInterval": self.cleanup_interval,
            },
            "browsers": self.list_browsers(),
        }
