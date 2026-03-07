"""
浏览器管理器 - 对应 OpenClaw browser/chrome.js + profiles-service.js
"""

import asyncio
import os
import tempfile
import shutil
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext

from ..models.config import BrowserConfig, ProfileConfig
from .tab_manager import TabManager


class BrowserManager:
    """浏览器管理器 - 管理 Playwright 浏览器实例"""
    
    def __init__(self, config: BrowserConfig):
        self.config = config
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.tab_manager = TabManager()
        self._profile: Optional[ProfileConfig] = None
        self._user_data_dir: Optional[str] = None
        self._running = False
    
    @property
    def is_running(self) -> bool:
        """浏览器是否运行中"""
        return self._running and self.browser is not None
    
    async def start(self, profile_name: Optional[str] = None) -> bool:
        """启动浏览器"""
        if self.is_running:
            return True
        
        profile = self.config.get_profile(profile_name)
        self._profile = profile
        
        # 启动 Playwright
        self.playwright = await async_playwright().start()
        
        # 浏览器启动参数
        browser_args = []
        if profile.no_sandbox:
            browser_args.extend(["--no-sandbox", "--disable-setuid-sandbox"])
        
        # 添加自定义参数
        browser_args.extend(profile.args)
        
        # 确定可执行路径
        executable_path = profile.executable_path or self.config.executable_path
        
        # 创建临时用户数据目录
        if profile.user_data_dir:
            self._user_data_dir = profile.user_data_dir
        else:
            self._user_data_dir = tempfile.mkdtemp(prefix="qianji_profile_")
        
        # 启动浏览器
        try:
            if executable_path:
                # 使用指定浏览器
                self.browser = await self.playwright.chromium.launch(
                    executable_path=executable_path,
                    headless=profile.headless,
                    args=browser_args,
                )
            else:
                # 使用 Playwright 内置浏览器
                self.browser = await self.playwright.chromium.launch(
                    headless=profile.headless,
                    args=browser_args,
                )
            
            # 创建上下文
            self.context = await self.browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_data_dir=self._user_data_dir if profile.user_data_dir else None,
            )
            
            self._running = True
            
            # 创建第一个标签页
            page = await self.context.new_page()
            await self.tab_manager.create_tab(page)
            
            return True
            
        except Exception as e:
            await self.stop()
            raise RuntimeError(f"Failed to start browser: {e}")
    
    async def stop(self) -> bool:
        """停止浏览器"""
        if not self.is_running:
            return False
        
        # 关闭所有标签页
        await self.tab_manager.close_all()
        
        # 关闭上下文
        if self.context:
            try:
                await self.context.close()
            except:
                pass
            self.context = None
        
        # 关闭浏览器
        if self.browser:
            try:
                await self.browser.close()
            except:
                pass
            self.browser = None
        
        # 停止 Playwright
        if self.playwright:
            try:
                await self.playwright.stop()
            except:
                pass
            self.playwright = None
        
        # 清理临时用户数据目录
        if self._user_data_dir and not self._profile.user_data_dir:
            try:
                shutil.rmtree(self._user_data_dir, ignore_errors=True)
            except:
                pass
        
        self._running = False
        self._profile = None
        self._user_data_dir = None
        
        return True
    
    async def reset(self) -> bool:
        """重置浏览器（关闭并重新启动）"""
        profile_name = self._profile.name if self._profile else None
        await self.stop()
        return await self.start(profile_name)
    
    def get_status(self) -> Dict[str, Any]:
        """获取浏览器状态"""
        return {
            "running": self.is_running,
            "profile": self._profile.name if self._profile else None,
            "tabs": len(self.tab_manager.tabs),
            "activeTab": self.tab_manager.active_tab_id,
        }
