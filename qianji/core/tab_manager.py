"""
标签页管理 - 对应 OpenClaw browser/routes/tabs.js
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from playwright.async_api import Page, BrowserContext
import uuid


@dataclass
class Tab:
    """标签页"""
    target_id: str
    page: Page
    url: str = ""
    title: str = ""
    active: bool = False
    
    async def update_info(self):
        """更新页面信息"""
        self.url = self.page.url
        # 使用 evaluate 获取标题，避免可能的错误
        try:
            self.title = await self.page.title()
        except:
            self.title = ""


class TabManager:
    """标签页管理器"""
    
    def __init__(self):
        self.tabs: Dict[str, Tab] = {}
        self.active_tab_id: Optional[str] = None
        self._lock = asyncio.Lock()
    
    async def create_tab(self, page: Page) -> Tab:
        """创建新标签页"""
        target_id = str(uuid.uuid4())[:8]
        tab = Tab(
            target_id=target_id,
            page=page,
        )
        await tab.update_info()
        
        async with self._lock:
            self.tabs[target_id] = tab
            self.active_tab_id = target_id
            tab.active = True
        
        return tab
    
    async def close_tab(self, target_id: str) -> bool:
        """关闭标签页"""
        async with self._lock:
            if target_id not in self.tabs:
                return False
            
            tab = self.tabs[target_id]
            try:
                await tab.page.close()
            except:
                pass
            
            del self.tabs[target_id]
            
            # 更新活动标签页
            if self.active_tab_id == target_id:
                if self.tabs:
                    self.active_tab_id = next(iter(self.tabs.keys()))
                    self.tabs[self.active_tab_id].active = True
                else:
                    self.active_tab_id = None
            
            return True
    
    def get_tab(self, target_id: Optional[str] = None) -> Optional[Tab]:
        """获取标签页"""
        if target_id is None:
            target_id = self.active_tab_id
        
        if target_id is None:
            return None
        
        return self.tabs.get(target_id)
    
    async def focus_tab(self, target_id: str) -> bool:
        """聚焦标签页"""
        async with self._lock:
            if target_id not in self.tabs:
                return False
            
            # 取消之前的活动状态
            if self.active_tab_id and self.active_tab_id in self.tabs:
                self.tabs[self.active_tab_id].active = False
            
            # 设置新的活动标签页
            self.active_tab_id = target_id
            self.tabs[target_id].active = True
            
            # 将页面带到前面
            try:
                await self.tabs[target_id].page.bring_to_front()
            except:
                pass
            
            return True
    
    def list_tabs(self) -> List[Dict[str, Any]]:
        """列出所有标签页"""
        return [
            {
                "targetId": tab.target_id,
                "url": tab.url,
                "title": tab.title,
                "active": tab.active,
            }
            for tab in self.tabs.values()
        ]
    
    async def ensure_tab_available(self, target_id: Optional[str] = None) -> Tab:
        """确保标签页可用"""
        tab = self.get_tab(target_id)
        if tab is None:
            raise ValueError(f"Tab not found: {target_id}")
        
        # 更新信息
        await tab.update_info()
        return tab
    
    async def close_all(self):
        """关闭所有标签页"""
        async with self._lock:
            for tab in list(self.tabs.values()):
                try:
                    await tab.page.close()
                except:
                    pass
            
            self.tabs.clear()
            self.active_tab_id = None
