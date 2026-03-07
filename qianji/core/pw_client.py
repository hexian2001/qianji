"""
Playwright 客户端 - 对应 OpenClaw browser/pw-ai.js + cdp.js
处理所有页面操作：导航、点击、输入、截图等
"""

import asyncio
import base64
import json
from typing import Optional, Dict, List, Any, Callable
from playwright.async_api import Page, ElementHandle, TimeoutError as PWTimeoutError

from ..models.snapshot import Snapshot, SnapshotElement


class PlaywrightClient:
    """Playwright 客户端 - 封装所有页面操作"""
    
    def __init__(self):
        self._ref_counter = 0
        self._last_snapshot: Optional[Snapshot] = None
    
    def _generate_ref(self) -> str:
        """生成元素引用 ID"""
        self._ref_counter += 1
        return f"e{self._ref_counter}"
    
    async def navigate(self, page: Page, url: str, timeout: int = 30000) -> Dict[str, Any]:
        """导航到 URL"""
        try:
            response = await page.goto(url, timeout=timeout, wait_until="networkidle")
            return {
                "url": page.url,
                "title": await page.title(),
                "status": response.status if response else None,
            }
        except PWTimeoutError:
            # 超时但可能已加载
            return {
                "url": page.url,
                "title": await page.title(),
                "status": None,
            }
    
    async def go_back(self, page: Page) -> Dict[str, Any]:
        """后退"""
        await page.go_back(wait_until="networkidle")
        return {
            "url": page.url,
            "title": await page.title(),
        }
    
    async def go_forward(self, page: Page) -> Dict[str, Any]:
        """前进"""
        await page.go_forward(wait_until="networkidle")
        return {
            "url": page.url,
            "title": await page.title(),
        }
    
    async def reload(self, page: Page) -> Dict[str, Any]:
        """刷新"""
        await page.reload(wait_until="networkidle")
        return {
            "url": page.url,
            "title": await page.title(),
        }
    
    async def get_content(self, page: Page, format: str = "text") -> str:
        """获取页面内容"""
        if format == "html":
            return await page.content()
        elif format == "markdown":
            # 简化的 markdown 转换
            return await self._to_markdown(page)
        else:
            return await page.inner_text("body")
    
    async def _to_markdown(self, page: Page) -> str:
        """将页面转换为 markdown"""
        # 简化的 markdown 提取
        script = """
        () => {
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
            let result = [];
            let node;
            while (node = walker.nextNode()) {
                const tag = node.tagName.toLowerCase();
                if (tag === 'h1') result.push('# ' + node.textContent);
                else if (tag === 'h2') result.push('## ' + node.textContent);
                else if (tag === 'h3') result.push('### ' + node.textContent);
                else if (tag === 'p') result.push(node.textContent);
                else if (tag === 'a') result.push(`[${node.textContent}](${node.href})`);
            }
            return result.join('\\n\\n');
        }
        """
        return await page.evaluate(script)
    
    async def create_snapshot(self, page: Page, refs: str = "role") -> Snapshot:
        """创建页面快照 - 对应 OpenClaw 的 snapshot"""
        self._ref_counter = 0
        
        # 获取页面基本信息
        url = page.url
        title = await page.title()
        
        # 获取页面文本
        try:
            text = await page.inner_text("body")
        except:
            text = ""
        
        # 获取视口信息
        viewport = page.viewport_size
        scroll = await page.evaluate("() => ({ x: window.scrollX, y: window.scrollY })")
        
        # 创建快照
        snapshot = Snapshot(
            url=url,
            title=title,
            text=text,
            viewport_width=viewport.get("width", 1280) if viewport else 1280,
            viewport_height=viewport.get("height", 720) if viewport else 720,
            scroll_x=scroll.get("x", 0),
            scroll_y=scroll.get("y", 0),
        )
        
        # 提取可交互元素
        elements = await self._extract_elements(page, refs)
        snapshot.elements = elements
        snapshot.refs = list(elements.keys())
        
        self._last_snapshot = snapshot
        return snapshot
    
    async def _extract_elements(self, page: Page, refs: str = "role") -> Dict[str, SnapshotElement]:
        """提取页面元素"""
        elements: Dict[str, SnapshotElement] = {}
        
        # 使用 Playwright 的 accessibility 快照
        try:
            snapshot = await page.accessibility.snapshot()
            if snapshot:
                await self._process_accessibility_node(snapshot, elements, page)
        except:
            pass
        
        # 如果 accessibility 没有返回足够信息，使用 DOM 查询
        if len(elements) < 5:
            await self._extract_from_dom(page, elements)
        
        return elements
    
    async def _process_accessibility_node(self, node: Dict, elements: Dict, page: Page, parent_ref: Optional[str] = None):
        """处理 accessibility 节点"""
        role = node.get("role", "")
        name = node.get("name", "")
        
        # 只保留可交互元素
        interactive_roles = {
            "button", "link", "textbox", "checkbox", "radio",
            "combobox", "menuitem", "tab", "treeitem", "searchbox",
            "spinbutton", "switch"
        }
        
        if role in interactive_roles and name:
            ref = self._generate_ref()
            elements[ref] = SnapshotElement(
                ref=ref,
                element_type=role,
                name=name,
                role=role,
            )
        
        # 处理子节点
        children = node.get("children", [])
        for child in children:
            await self._process_accessibility_node(child, elements, page, parent_ref)
    
    async def _extract_from_dom(self, page: Page, elements: Dict):
        """从 DOM 提取元素"""
        # 常见的可交互元素选择器
        selectors = [
            ("button", "button"),
            ("link", "a[href]"),
            ("textbox", "input[type='text'], input:not([type]), textarea"),
            ("checkbox", "input[type='checkbox']"),
            ("radio", "input[type='radio']"),
            ("combobox", "select"),
            ("searchbox", "input[type='search']"),
        ]
        
        for element_type, selector in selectors:
            try:
                handles = await page.query_selector_all(selector)
                for handle in handles:
                    try:
                        # 获取元素信息
                        name = await handle.get_attribute("aria-label") or \
                               await handle.get_attribute("placeholder") or \
                               await handle.inner_text() or \
                               await handle.get_attribute("value") or \
                               await handle.get_attribute("name") or ""
                        
                        name = name.strip()[:50] if name else ""
                        
                        if name or element_type == "button":
                            ref = self._generate_ref()
                            elements[ref] = SnapshotElement(
                                ref=ref,
                                element_type=element_type,
                                name=name,
                                role=element_type,
                            )
                    except:
                        continue
            except:
                continue
    
    async def click_by_ref(self, page: Page, ref: str, snapshot: Snapshot, 
                          double_click: bool = False, timeout: int = 5000) -> bool:
        """通过 ref 点击元素"""
        element = snapshot.get_element(ref)
        if not element:
            raise ValueError(f"Element ref not found: {ref}")
        
        # 通过 role 和 name 定位元素
        if element.role and element.name:
            locator = page.get_by_role(element.role, name=element.name, exact=False)
            if await locator.count() > 0:
                if double_click:
                    await locator.dblclick(timeout=timeout)
                else:
                    await locator.click(timeout=timeout)
                return True
        
        # 回退到通用选择器
        # 这里简化处理，实际应该存储更精确的选择器
        raise ValueError(f"Cannot locate element with ref: {ref}")
    
    async def fill_by_ref(self, page: Page, ref: str, text: str, 
                         snapshot: Snapshot, timeout: int = 5000) -> bool:
        """通过 ref 填充输入"""
        element = snapshot.get_element(ref)
        if not element:
            raise ValueError(f"Element ref not found: {ref}")
        
        # 通过 role 和 name 定位
        if element.role and element.name:
            locator = page.get_by_role(element.role, name=element.name, exact=False)
            if await locator.count() > 0:
                await locator.fill(text, timeout=timeout)
                return True
        
        raise ValueError(f"Cannot locate element with ref: {ref}")
    
    async def type_by_ref(self, page: Page, ref: str, text: str,
                         snapshot: Snapshot, submit: bool = False,
                         timeout: int = 5000) -> bool:
        """通过 ref 输入文本"""
        element = snapshot.get_element(ref)
        if not element:
            raise ValueError(f"Element ref not found: {ref}")
        
        if element.role and element.name:
            locator = page.get_by_role(element.role, name=element.name, exact=False)
            if await locator.count() > 0:
                await locator.type(text, timeout=timeout)
                if submit:
                    await locator.press("Enter")
                return True
        
        raise ValueError(f"Cannot locate element with ref: {ref}")
    
    async def screenshot(self, page: Page, path: str, 
                        full_page: bool = False,
                        ref: Optional[str] = None,
                        snapshot: Optional[Snapshot] = None) -> str:
        """截图"""
        if ref and snapshot:
            # 元素截图
            element = snapshot.get_element(ref)
            if element and element.role and element.name:
                locator = page.get_by_role(element.role, name=element.name, exact=False)
                await locator.screenshot(path=path)
                return path
        
        # 页面截图
        await page.screenshot(path=path, full_page=full_page)
        return path
    
    async def pdf(self, page: Page, path: str) -> str:
        """生成 PDF"""
        await page.pdf(path=path)
        return path
    
    async def evaluate(self, page: Page, script: str, arg: Any = None) -> Any:
        """执行 JavaScript"""
        if arg is not None:
            return await page.evaluate(script, arg)
        return await page.evaluate(script)
    
    async def wait_for_timeout(self, page: Page, timeout: int):
        """等待指定时间"""
        await page.wait_for_timeout(timeout)
    
    async def wait_for_selector(self, page: Page, selector: str, 
                               timeout: int = 30000) -> bool:
        """等待选择器出现"""
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except PWTimeoutError:
            return False
    
    async def wait_for_navigation(self, page: Page, timeout: int = 30000) -> bool:
        """等待导航完成"""
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
            return True
        except PWTimeoutError:
            return False
