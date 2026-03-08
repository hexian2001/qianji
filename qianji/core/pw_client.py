"""
Playwright 客户端 - V3
多策略元素定位、CSS selector、iframe 提取、DOM hash、
快照裁剪、弹窗/下载监听、标注截图
"""

import logging
import os
import tempfile
import time
from collections import deque
from typing import Any

from playwright.async_api import (
    Dialog,
    Download,
    Frame,
    Locator,
    Page,
)
from playwright.async_api import (
    TimeoutError as PWTimeoutError,
)

from ..models.snapshot import Snapshot, SnapshotElement

logger = logging.getLogger("qianji.pw_client")

# ============================================================
#  JavaScript 片段
# ============================================================

# 为元素计算唯一 CSS selector
_COMPUTE_SELECTOR_JS = """
(element) => {
    function getSelector(el) {
        if (el.id) {
            return '#' + CSS.escape(el.id);
        }
        const testId = el.getAttribute('data-testid') || el.getAttribute('data-test-id');
        if (testId) {
            return `[data-testid="${CSS.escape(testId)}"]`;
        }
        let parts = [];
        let current = el;
        while (current && current !== document.body && current !== document.documentElement) {
            let sel = current.tagName.toLowerCase();
            if (current.id) {
                sel = '#' + CSS.escape(current.id);
                parts.unshift(sel);
                break;
            }
            if (current.className && typeof current.className === 'string') {
                const classes = current.className.trim().split(/\\s+/).filter(c => c && !c.match(/^(active|hover|focus|selected|open|show|visible|hidden)/i));
                if (classes.length > 0) {
                    sel += '.' + classes.slice(0, 2).map(c => CSS.escape(c)).join('.');
                }
            }
            const parent = current.parentElement;
            if (parent) {
                const siblings = Array.from(parent.children).filter(c => c.tagName === current.tagName);
                if (siblings.length > 1) {
                    sel += `:nth-of-type(${siblings.indexOf(current) + 1})`;
                }
            }
            parts.unshift(sel);
            current = current.parentElement;
        }
        return parts.join(' > ');
    }
    try {
        return getSelector(element);
    } catch(e) {
        return null;
    }
}
"""

# 提取所有可交互元素
_EXTRACT_ELEMENTS_JS = """
() => {
    const results = [];
    const interactiveSelectors = [
        'a[href]',
        'button',
        'input:not([type="hidden"])',
        'textarea',
        'select',
        '[role="button"]',
        '[role="link"]',
        '[role="textbox"]',
        '[role="checkbox"]',
        '[role="radio"]',
        '[role="combobox"]',
        '[role="menuitem"]',
        '[role="tab"]',
        '[role="treeitem"]',
        '[role="switch"]',
        '[role="slider"]',
        '[role="searchbox"]',
        '[role="option"]',
        '[role="listbox"]',
        '[tabindex]:not([tabindex="-1"])',
        '[contenteditable="true"]',
        '[contenteditable=""]',
        '[onclick]',
        'summary',
        'details > summary',
    ];

    const selector = interactiveSelectors.join(', ');
    const elements = document.querySelectorAll(selector);
    const seen = new Set();

    function getSelector(el) {
        if (el.id) return '#' + CSS.escape(el.id);
        const testId = el.getAttribute('data-testid') || el.getAttribute('data-test-id');
        if (testId) return `[data-testid="${CSS.escape(testId)}"]`;

        let parts = [];
        let current = el;
        while (current && current !== document.body && current !== document.documentElement) {
            let sel = current.tagName.toLowerCase();
            if (current.id) {
                sel = '#' + CSS.escape(current.id);
                parts.unshift(sel);
                break;
            }
            if (current.className && typeof current.className === 'string') {
                const classes = current.className.trim().split(/\\s+/).filter(c => c && !c.match(/^(active|hover|focus|selected|open|show|visible|hidden)/i));
                if (classes.length > 0) {
                    sel += '.' + classes.slice(0, 2).map(c => CSS.escape(c)).join('.');
                }
            }
            const parent = current.parentElement;
            if (parent) {
                const siblings = Array.from(parent.children).filter(c => c.tagName === current.tagName);
                if (siblings.length > 1) {
                    sel += `:nth-of-type(${siblings.indexOf(current) + 1})`;
                }
            }
            parts.unshift(sel);
            current = current.parentElement;
        }
        return parts.join(' > ');
    }

    function getElementType(el) {
        const role = el.getAttribute('role');
        if (role) return role;
        const tag = el.tagName.toLowerCase();
        if (tag === 'a') return 'link';
        if (tag === 'button' || tag === 'summary') return 'button';
        if (tag === 'select') return 'combobox';
        if (tag === 'textarea') return 'textbox';
        if (tag === 'input') {
            const type = (el.type || 'text').toLowerCase();
            const typeMap = {
                'text': 'textbox', 'email': 'textbox', 'password': 'textbox',
                'tel': 'textbox', 'url': 'textbox', 'search': 'searchbox',
                'number': 'spinbutton', 'checkbox': 'checkbox', 'radio': 'radio',
                'submit': 'button', 'reset': 'button', 'button': 'button',
                'file': 'file', 'range': 'slider',
            };
            return typeMap[type] || 'textbox';
        }
        if (el.getAttribute('contenteditable')) return 'textbox';
        if (el.getAttribute('onclick')) return 'button';
        return 'generic';
    }

    function getDisplayName(el) {
        const ariaLabel = el.getAttribute('aria-label');
        if (ariaLabel) return ariaLabel.trim().substring(0, 80);

        const placeholder = el.getAttribute('placeholder');
        if (placeholder) return placeholder.trim().substring(0, 80);

        const title = el.getAttribute('title');
        if (title) return title.trim().substring(0, 80);

        if (el.tagName.toLowerCase() === 'input') {
            const value = el.value || '';
            if (value && el.type !== 'password') {
                return value.trim().substring(0, 80);
            }
        }

        const text = (el.textContent || '').replace(/\\s+/g, ' ').trim();
        return text.substring(0, 80) || null;
    }

    for (const el of elements) {
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
            continue;
        }

        const rect = el.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) continue;

        const cssSelector = getSelector(el);
        if (seen.has(cssSelector)) continue;
        seen.add(cssSelector);

        const elementType = getElementType(el);
        const displayName = getDisplayName(el);

        if (!displayName && elementType === 'generic') continue;

        const inViewport = (
            rect.top < window.innerHeight &&
            rect.bottom > 0 &&
            rect.left < window.innerWidth &&
            rect.right > 0
        );

        results.push({
            selector: cssSelector,
            type: elementType,
            name: displayName || '',
            role: el.getAttribute('role') || elementType,
            ariaLabel: el.getAttribute('aria-label') || null,
            placeholder: el.getAttribute('placeholder') || null,
            value: el.value || null,
            checked: el.checked || null,
            disabled: el.disabled || false,
            visible: true,
            inViewport: inViewport,
            bbox: {
                x: Math.round(rect.x),
                y: Math.round(rect.y),
                width: Math.round(rect.width),
                height: Math.round(rect.height)
            },
        });
    }
    return results;
}
"""

# DOM hash 计算（轻量）
_DOM_HASH_JS = """
() => {
    const interactive = document.querySelectorAll('a,button,input,select,textarea,[role]').length;
    const textLen = document.body ? document.body.innerText.length : 0;
    const url = location.href;
    return `${url}|${interactive}|${textLen}`;
}
"""

# 标注 overlay 注入
_INJECT_ANNOTATIONS_JS = """
(elements) => {
    const container = document.createElement('div');
    container.id = '__qianji_annotations__';
    container.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:2147483647;';
    for (const el of elements) {
        const box = document.createElement('div');
        box.style.cssText = `position:absolute;left:${el.x}px;top:${el.y}px;width:${el.w}px;height:${el.h}px;border:2px solid red;background:rgba(255,0,0,0.08);`;
        const label = document.createElement('span');
        label.textContent = el.ref;
        label.style.cssText = 'position:absolute;top:-16px;left:0;background:red;color:white;font-size:10px;padding:1px 3px;font-family:monospace;border-radius:2px;';
        box.appendChild(label);
        container.appendChild(box);
    }
    document.body.appendChild(container);
}
"""

_REMOVE_ANNOTATIONS_JS = """
() => {
    const el = document.getElementById('__qianji_annotations__');
    if (el) el.remove();
}
"""


# ============================================================
#  SnapshotCache
# ============================================================


class SnapshotCache:
    """快照缓存 — 按 (browser_id, tab_id) 缓存最近快照"""

    def __init__(self, max_age: float = 30.0):
        self._cache: dict[str, Snapshot] = {}
        self._max_age = max_age

    def _key(self, browser_id: str, tab_id: str) -> str:
        return f"{browser_id}:{tab_id}"

    def get(self, browser_id: str, tab_id: str) -> Snapshot | None:
        """获取缓存快照（未过期 + dom_hash 未变时返回）"""
        key = self._key(browser_id, tab_id)
        snap = self._cache.get(key)
        if snap and not snap.is_stale(self._max_age):
            return snap
        return None

    def put(self, browser_id: str, tab_id: str, snapshot: Snapshot):
        self._cache[self._key(browser_id, tab_id)] = snapshot

    def invalidate(self, browser_id: str, tab_id: str):
        self._cache.pop(self._key(browser_id, tab_id), None)

    def invalidate_all(self):
        self._cache.clear()

    def get_by_id(self, snapshot_id: str) -> Snapshot | None:
        for snap in self._cache.values():
            if snap.snapshot_id == snapshot_id:
                return snap
        return None


# 全局单例
snapshot_cache = SnapshotCache()


# ============================================================
#  PlaywrightClient
# ============================================================


class PlaywrightClient:
    """Playwright 客户端 V3 — iframe、弹窗、下载、标注截图"""

    def __init__(self):
        self._ref_counter = 0
        self._last_snapshot: Snapshot | None = None
        # V3: 弹窗历史
        self._dialog_history: deque = deque(maxlen=20)
        self._dialog_mode: str = "accept"  # accept / dismiss / custom
        self._dialog_custom_text: str | None = None
        # V3: 下载历史
        self._downloads: deque = deque(maxlen=50)
        self._download_dir: str = tempfile.mkdtemp(prefix="qianji_downloads_")
        # V3: 已注册监听器的页面集合
        self._listened_pages: set = set()

    def _generate_ref(self, frame_prefix: str = "") -> str:
        self._ref_counter += 1
        return f"{frame_prefix}e{self._ref_counter}"

    # ============ 页面监听器 ============

    def setup_page_listeners(self, page: Page):
        """为页面注册弹窗和下载监听器（幂等）"""
        page_id = id(page)
        if page_id in self._listened_pages:
            return
        self._listened_pages.add(page_id)

        async def _on_dialog(dialog: Dialog):
            info = {
                "type": dialog.type,
                "message": dialog.message,
                "default_value": dialog.default_value,
                "timestamp": time.time(),
                "action": self._dialog_mode,
            }
            self._dialog_history.append(info)
            logger.info(f"Dialog [{dialog.type}]: {dialog.message}")

            try:
                if self._dialog_mode == "dismiss":
                    await dialog.dismiss()
                elif self._dialog_mode == "custom" and self._dialog_custom_text is not None:
                    await dialog.accept(self._dialog_custom_text)
                else:
                    await dialog.accept()
            except Exception as e:
                logger.warning(f"Failed to handle dialog: {e}")

        async def _on_download(download: Download):
            try:
                path = os.path.join(self._download_dir, download.suggested_filename)
                await download.save_as(path)
                info = {
                    "filename": download.suggested_filename,
                    "url": download.url,
                    "path": path,
                    "timestamp": time.time(),
                }
                self._downloads.append(info)
                logger.info(f"Download: {download.suggested_filename} -> {path}")
            except Exception as e:
                logger.warning(f"Failed to save download: {e}")

        page.on("dialog", _on_dialog)
        page.on("download", _on_download)

    def set_dialog_mode(self, mode: str, custom_text: str | None = None):
        """设置弹窗处理策略"""
        self._dialog_mode = mode  # accept / dismiss / custom
        self._dialog_custom_text = custom_text

    def get_dialog_history(self) -> list[dict]:
        return list(self._dialog_history)

    def get_downloads(self) -> list[dict]:
        return list(self._downloads)

    # ============ 导航 ============

    async def navigate(
        self, page: Page, url: str, timeout: int = 30000, wait_until: str = "domcontentloaded"
    ) -> dict[str, Any]:
        self.setup_page_listeners(page)
        try:
            response = await page.goto(url, timeout=timeout, wait_until=wait_until)
            return {
                "url": page.url,
                "title": await page.title(),
                "status": response.status if response else None,
            }
        except PWTimeoutError:
            return {
                "url": page.url,
                "title": await page.title(),
                "status": None,
            }

    async def go_back(self, page: Page, wait_until: str = "domcontentloaded") -> dict[str, Any]:
        await page.go_back(wait_until=wait_until)
        return {"url": page.url, "title": await page.title()}

    async def go_forward(self, page: Page, wait_until: str = "domcontentloaded") -> dict[str, Any]:
        await page.go_forward(wait_until=wait_until)
        return {"url": page.url, "title": await page.title()}

    async def reload(self, page: Page, wait_until: str = "domcontentloaded") -> dict[str, Any]:
        await page.reload(wait_until=wait_until)
        return {"url": page.url, "title": await page.title()}

    # ============ 快照 (V3: iframe + dom_hash + truncation) ============

    async def create_snapshot(
        self, page: Page, refs: str = "role", max_elements: int = 150, viewport_only: bool = False
    ) -> Snapshot:
        """创建页面快照 — V3: iframe 遍历 + DOM hash + 裁剪"""
        self.setup_page_listeners(page)
        self._ref_counter = 0

        url = page.url
        title = await page.title()

        try:
            text = await page.inner_text("body")
        except Exception as e:
            logger.debug(f"Failed to get page text: {e}")
            text = ""

        viewport = page.viewport_size
        try:
            scroll = await page.evaluate("() => ({ x: window.scrollX, y: window.scrollY })")
        except Exception:
            scroll = {"x": 0, "y": 0}

        # DOM hash
        try:
            dom_hash = await page.evaluate(_DOM_HASH_JS)
        except Exception:
            dom_hash = ""

        snapshot = Snapshot(
            url=url,
            title=title,
            text=text,
            viewport_width=viewport.get("width", 1280) if viewport else 1280,
            viewport_height=viewport.get("height", 720) if viewport else 720,
            scroll_x=scroll.get("x", 0),
            scroll_y=scroll.get("y", 0),
            dom_hash=dom_hash,
            max_elements=max_elements,
        )

        # ---- 主 frame 提取 ----
        all_elements: list[tuple[SnapshotElement, bool]] = []  # (element, in_viewport)
        main_elements = await self._extract_elements_from_frame(page.main_frame)
        for elem in main_elements:
            all_elements.append((elem, elem.in_viewport))

        # ---- iframe 提取 ----
        frame_index = 0
        for frame in page.frames:
            if frame == page.main_frame:
                continue
            if frame.is_detached():
                continue
            frame_index += 1
            fid = f"f{frame_index}_"
            frame_name = frame.name or frame.url.split("/")[-1][:30] or f"frame{frame_index}"
            try:
                iframe_elements = await self._extract_elements_from_frame(
                    frame, frame_prefix=fid, frame_id=fid.rstrip("_"), frame_name=frame_name
                )
                for elem in iframe_elements:
                    all_elements.append((elem, elem.in_viewport))
            except Exception as e:
                logger.debug(f"Failed to extract from iframe {frame_name}: {e}")

        # ---- Accessibility 补充（主 frame） ----
        main_count = sum(1 for e, _ in all_elements if not e.frame_id)
        if main_count < 3:
            try:
                a11y_snapshot = await page.accessibility.snapshot()
                if a11y_snapshot:
                    a11y_elements: dict[str, SnapshotElement] = {}
                    await self._process_accessibility_node(a11y_snapshot, a11y_elements, page)
                    for elem in a11y_elements.values():
                        all_elements.append((elem, True))
            except Exception as e:
                logger.debug(f"Accessibility snapshot failed: {e}")

        # ---- 裁剪 ----
        snapshot.total_elements_found = len(all_elements)

        if viewport_only:
            all_elements = [(e, v) for e, v in all_elements if v or e.frame_id]

        # 优先 viewport 内 → viewport 外
        viewport_in = [(e, v) for e, v in all_elements if v]
        viewport_out = [(e, v) for e, v in all_elements if not v]

        selected = []
        for e, v in viewport_in:
            if len(selected) >= max_elements:
                break
            selected.append(e)
        remaining = max_elements - len(selected)
        if remaining > 0:
            for e, v in viewport_out:
                if len(selected) >= max_elements:
                    break
                selected.append(e)

        snapshot.elements = {e.ref: e for e in selected}
        snapshot.refs = [e.ref for e in selected]

        self._last_snapshot = snapshot
        return snapshot

    async def _extract_elements_from_frame(
        self,
        frame: Frame,
        frame_prefix: str = "",
        frame_id: str | None = None,
        frame_name: str | None = None,
    ) -> list[SnapshotElement]:
        """从单个 frame 提取可交互元素"""
        elements: list[SnapshotElement] = []
        try:
            raw_elements = await frame.evaluate(_EXTRACT_ELEMENTS_JS)
            for raw in raw_elements:
                ref = self._generate_ref(frame_prefix)
                elements.append(
                    SnapshotElement(
                        ref=ref,
                        element_type=raw.get("type", "generic"),
                        name=raw.get("name"),
                        role=raw.get("role"),
                        selector=raw.get("selector"),
                        aria_label=raw.get("ariaLabel"),
                        placeholder=raw.get("placeholder"),
                        value=raw.get("value"),
                        checked=raw.get("checked"),
                        disabled=raw.get("disabled", False),
                        visible=raw.get("visible", True),
                        in_viewport=raw.get("inViewport", True),
                        bbox=raw.get("bbox"),
                        frame_id=frame_id,
                        frame_name=frame_name,
                    )
                )
        except Exception as e:
            logger.warning(f"Element extraction from frame failed: {e}")
        return elements

    async def _process_accessibility_node(
        self, node: dict, elements: dict, page: Page, parent_ref: str | None = None
    ):
        """处理 accessibility 节点（回退路径）"""
        role = node.get("role", "")
        name = node.get("name", "")
        interactive_roles = {
            "button",
            "link",
            "textbox",
            "checkbox",
            "radio",
            "combobox",
            "menuitem",
            "tab",
            "treeitem",
            "searchbox",
            "spinbutton",
            "switch",
            "slider",
            "option",
            "listbox",
        }
        if role in interactive_roles and name:
            ref = self._generate_ref()
            elements[ref] = SnapshotElement(ref=ref, element_type=role, name=name, role=role)
        for child in node.get("children", []):
            await self._process_accessibility_node(child, elements, page, parent_ref)

    # ============ DOM 变化检测 ============

    async def check_page_changed(self, page: Page, snapshot: Snapshot) -> bool:
        """检查页面是否发生了变化（对比 dom_hash）"""
        if not snapshot.dom_hash:
            return True
        try:
            current_hash = await page.evaluate(_DOM_HASH_JS)
            return current_hash != snapshot.dom_hash
        except Exception:
            return True

    # ============ 元素定位（多策略 + iframe 感知） ============

    def _get_frame_for_element(self, page: Page, element: SnapshotElement) -> Frame:
        """根据元素的 frame_id 获取正确的 frame"""
        if not element.frame_id:
            return page.main_frame

        # frame_id 格式: f1, f2, ...
        try:
            frame_index = int(element.frame_id.replace("f", "")) - 1
            non_main = [f for f in page.frames if f != page.main_frame and not f.is_detached()]
            if 0 <= frame_index < len(non_main):
                return non_main[frame_index]
        except (ValueError, IndexError):
            pass

        logger.warning(f"Frame {element.frame_id} not found, falling back to main frame")
        return page.main_frame

    async def _locate_element(
        self, page: Page, element: SnapshotElement, timeout: int = 5000
    ) -> Locator:
        """多策略元素定位链: CSS selector → role+name → aria-label → placeholder → text"""
        frame = self._get_frame_for_element(page, element)

        # 策略 1: CSS selector
        if element.selector:
            try:
                locator = frame.locator(element.selector)
                if await locator.count() > 0:
                    first = locator.first
                    if await first.is_visible():
                        return first
            except Exception as e:
                logger.debug(f"CSS selector failed for {element.ref}: {e}")

        # 策略 2: role + name
        if element.role and element.name:
            try:
                locator = frame.get_by_role(element.role, name=element.name, exact=False)
                count = await locator.count()
                if count == 1:
                    return locator.first
                elif count > 1:
                    exact_locator = frame.get_by_role(element.role, name=element.name, exact=True)
                    if await exact_locator.count() == 1:
                        return exact_locator.first
                    for i in range(count):
                        item = locator.nth(i)
                        if await item.is_visible():
                            return item
                    return locator.first
            except Exception as e:
                logger.debug(f"Role+name failed for {element.ref}: {e}")

        # 策略 3: aria-label
        if element.aria_label:
            try:
                locator = frame.get_by_label(element.aria_label, exact=False)
                if await locator.count() > 0:
                    return locator.first
            except Exception as e:
                logger.debug(f"aria-label failed for {element.ref}: {e}")

        # 策略 4: placeholder
        if element.placeholder:
            try:
                locator = frame.get_by_placeholder(element.placeholder, exact=False)
                if await locator.count() > 0:
                    return locator.first
            except Exception as e:
                logger.debug(f"placeholder failed for {element.ref}: {e}")

        # 策略 5: text
        if element.name and element.element_type in ("button", "link"):
            try:
                locator = frame.get_by_text(element.name, exact=False)
                if await locator.count() > 0:
                    return locator.first
            except Exception as e:
                logger.debug(f"text match failed for {element.ref}: {e}")

        raise ValueError(
            f"Cannot locate element {element.ref} "
            f"(type={element.element_type}, name={element.name!r}) "
            f"after trying all strategies"
        )

    # ============ 操作（使用多策略定位） ============

    async def click_by_ref(
        self,
        page: Page,
        ref: str,
        snapshot: Snapshot,
        double_click: bool = False,
        timeout: int = 5000,
    ) -> bool:
        element = snapshot.get_element(ref)
        if not element:
            raise ValueError(f"Element ref not found: {ref}")
        locator = await self._locate_element(page, element, timeout)
        if double_click:
            await locator.dblclick(timeout=timeout)
        else:
            await locator.click(timeout=timeout)
        return True

    async def fill_by_ref(
        self, page: Page, ref: str, text: str, snapshot: Snapshot, timeout: int = 5000
    ) -> bool:
        element = snapshot.get_element(ref)
        if not element:
            raise ValueError(f"Element ref not found: {ref}")
        locator = await self._locate_element(page, element, timeout)
        await locator.fill(text, timeout=timeout)
        return True

    async def type_by_ref(
        self,
        page: Page,
        ref: str,
        text: str,
        snapshot: Snapshot,
        submit: bool = False,
        timeout: int = 5000,
    ) -> bool:
        element = snapshot.get_element(ref)
        if not element:
            raise ValueError(f"Element ref not found: {ref}")
        locator = await self._locate_element(page, element, timeout)
        await locator.type(text, timeout=timeout)
        if submit:
            await locator.press("Enter")
        return True

    async def hover_by_ref(
        self, page: Page, ref: str, snapshot: Snapshot, timeout: int = 5000
    ) -> bool:
        element = snapshot.get_element(ref)
        if not element:
            raise ValueError(f"Element ref not found: {ref}")
        locator = await self._locate_element(page, element, timeout)
        await locator.hover(timeout=timeout)
        return True

    async def select_by_ref(
        self, page: Page, ref: str, values: list, snapshot: Snapshot, timeout: int = 5000
    ) -> bool:
        element = snapshot.get_element(ref)
        if not element:
            raise ValueError(f"Element ref not found: {ref}")
        locator = await self._locate_element(page, element, timeout)
        await locator.select_option(values, timeout=timeout)
        return True

    async def get_text_by_ref(
        self, page: Page, ref: str, snapshot: Snapshot, timeout: int = 5000
    ) -> str:
        element = snapshot.get_element(ref)
        if not element:
            raise ValueError(f"Element ref not found: {ref}")
        locator = await self._locate_element(page, element, timeout)
        return await locator.inner_text(timeout=timeout)

    async def get_attribute_by_ref(
        self, page: Page, ref: str, attribute: str, snapshot: Snapshot, timeout: int = 5000
    ) -> str | None:
        element = snapshot.get_element(ref)
        if not element:
            raise ValueError(f"Element ref not found: {ref}")
        locator = await self._locate_element(page, element, timeout)
        return await locator.get_attribute(attribute, timeout=timeout)

    # ============ 文件上传 ============

    async def upload_file(
        self, page: Page, ref: str, file_paths: list[str], snapshot: Snapshot, timeout: int = 5000
    ) -> bool:
        """通过 file input 或 filechooser 事件上传文件"""
        element = snapshot.get_element(ref)
        if not element:
            raise ValueError(f"Element ref not found: {ref}")

        locator = await self._locate_element(page, element, timeout)

        if element.element_type == "file":
            # 直接是 <input type="file">
            await locator.set_input_files(file_paths)
        else:
            # 非 file input — 点击触发 filechooser
            async with page.expect_file_chooser(timeout=timeout) as fc_info:
                await locator.click(timeout=timeout)
            file_chooser = await fc_info.value
            await file_chooser.set_files(file_paths)

        return True

    # ============ 批量操作 ============

    async def fill_form(
        self,
        page: Page,
        fields: list[dict[str, str]],
        snapshot: Snapshot,
        submit_ref: str | None = None,
        timeout: int = 5000,
    ) -> bool:
        for fld in fields:
            ref = fld.get("ref")
            text = fld.get("text", "")
            if ref and text:
                await self.fill_by_ref(page, ref, text, snapshot, timeout)
        if submit_ref:
            await self.click_by_ref(page, submit_ref, snapshot, timeout=timeout)
        return True

    # ============ 滚动 ============

    async def scroll(
        self,
        page: Page,
        direction: str = "down",
        amount: int = 500,
        ref: str | None = None,
        snapshot: Snapshot | None = None,
    ) -> dict[str, Any]:
        if ref and snapshot:
            element = snapshot.get_element(ref)
            if element:
                locator = await self._locate_element(page, element)
                await locator.scroll_into_view_if_needed()
                return {"scrolled_to": ref, "url": page.url}

        delta_x, delta_y = 0, 0
        if direction == "down":
            delta_y = amount
        elif direction == "up":
            delta_y = -amount
        elif direction == "right":
            delta_x = amount
        elif direction == "left":
            delta_x = -amount

        await page.mouse.wheel(delta_x, delta_y)
        await page.wait_for_timeout(300)

        try:
            scroll = await page.evaluate("() => ({ x: window.scrollX, y: window.scrollY })")
        except Exception:
            scroll = None
        return {
            "direction": direction,
            "amount": amount,
            "scroll_x": scroll.get("x", 0) if scroll else 0,
            "scroll_y": scroll.get("y", 0) if scroll else 0,
        }

    # ============ 截图/PDF ============

    async def screenshot(
        self,
        page: Page,
        path: str,
        full_page: bool = False,
        ref: str | None = None,
        snapshot: Snapshot | None = None,
    ) -> str:
        if ref and snapshot:
            element = snapshot.get_element(ref)
            if element:
                try:
                    locator = await self._locate_element(page, element)
                    await locator.screenshot(path=path)
                    return path
                except Exception as e:
                    logger.warning(f"Element screenshot failed: {e}, falling back to full page")

        await page.screenshot(path=path, full_page=full_page)
        return path

    async def annotated_screenshot(self, page: Page, path: str, snapshot: Snapshot) -> str:
        """截图并标注所有可交互元素（红色边框 + ref 标签）"""
        # 收集有 bbox 的元素坐标
        annotations = []
        for elem in snapshot.elements.values():
            if elem.bbox and elem.in_viewport:
                annotations.append(
                    {
                        "ref": elem.ref,
                        "x": elem.bbox["x"],
                        "y": elem.bbox["y"],
                        "w": elem.bbox["width"],
                        "h": elem.bbox["height"],
                    }
                )

        if annotations:
            try:
                await page.evaluate(_INJECT_ANNOTATIONS_JS, annotations)
            except Exception as e:
                logger.warning(f"Failed to inject annotations: {e}")

        # 截图
        await page.screenshot(path=path)

        # 清除标注
        if annotations:
            try:
                await page.evaluate(_REMOVE_ANNOTATIONS_JS)
            except Exception:
                pass

        return path

    async def pdf(self, page: Page, path: str) -> str:
        await page.pdf(path=path)
        return path

    # ============ JavaScript ============

    async def evaluate(self, page: Page, script: str, arg: Any = None) -> Any:
        if arg is not None:
            return await page.evaluate(script, arg)
        return await page.evaluate(script)

    # ============ 等待 ============

    async def wait_for_timeout(self, page: Page, timeout: int):
        await page.wait_for_timeout(timeout)

    async def wait_for_selector(self, page: Page, selector: str, timeout: int = 30000) -> bool:
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except PWTimeoutError:
            return False

    async def wait_for_navigation(self, page: Page, timeout: int = 30000) -> bool:
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=timeout)
            return True
        except PWTimeoutError:
            return False

    # ============ 页面内容 ============

    async def get_content(self, page: Page, format: str = "text") -> str:
        if format == "html":
            return await page.content()
        elif format == "markdown":
            return await self._to_markdown(page)
        else:
            return await page.inner_text("body")

    async def _to_markdown(self, page: Page) -> str:
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
