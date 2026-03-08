"""
MCP (Model Context Protocol) 支持 - 增强版
让 qianji 可以被 Claude Desktop, Cursor 等工具使用
优化工具设计: 复合工具、精简返回、引导性描述
"""

import asyncio
import json
import logging
import sys
from typing import Any

import httpx

logger = logging.getLogger("qianji.mcp")


class QianjiMCPServer:
    """MCP 服务器实现 - 增强版"""

    def __init__(self, base_url: str = "http://localhost:18796"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.tools = self._define_tools()

    def _define_tools(self) -> list[dict[str, Any]]:
        """定义 MCP 工具列表 - 增强版，带引导性描述和复合工具"""
        return [
            # ============ 导航 ============
            {
                "name": "browser_navigate",
                "description": (
                    "Navigate to a URL. After navigation, call browser_snapshot to see "
                    "the page elements. Or use browser_navigate_and_snapshot to do both in one step."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to navigate to"},
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                        "waitUntil": {
                            "type": "string",
                            "description": "Wait strategy: 'domcontentloaded' (fast, default), 'load', 'networkidle' (slow)",
                            "default": "domcontentloaded",
                        },
                    },
                    "required": ["url"],
                },
            },
            # ============ 复合: 导航+快照 ============
            {
                "name": "browser_navigate_and_snapshot",
                "description": (
                    "Navigate to a URL AND immediately return the page snapshot with interactive elements. "
                    "This is the preferred way to navigate — saves one round trip compared to calling "
                    "browser_navigate then browser_snapshot separately."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to navigate to"},
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                        "waitUntil": {
                            "type": "string",
                            "description": "Wait strategy: 'domcontentloaded' (fast, default), 'load', 'networkidle' (slow)",
                            "default": "domcontentloaded",
                        },
                    },
                    "required": ["url"],
                },
            },
            # ============ 快照 ============
            {
                "name": "browser_snapshot",
                "description": (
                    "Get the current page state with all interactive elements. Returns [ref] labels "
                    "like [e1], [e2] for each element. Use these refs with browser_click, browser_type, etc. "
                    "IMPORTANT: Always call this after page navigation or state changes to get fresh refs. "
                    "Refs from previous snapshots become invalid after page changes."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                        "maxElements": {
                            "type": "integer",
                            "description": "Max interactive elements to return (default: 150)",
                            "default": 150,
                        },
                        "viewportOnly": {
                            "type": "boolean",
                            "description": "Only return elements in current viewport",
                            "default": False,
                        },
                    },
                },
            },
            # ============ 点击 ============
            {
                "name": "browser_click",
                "description": (
                    "Click an element by its ref (e.g. 'e1'). Returns the updated page snapshot "
                    "automatically — no need to call browser_snapshot afterwards unless the page "
                    "navigated to a completely new URL."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ref": {
                            "type": "string",
                            "description": "Element ref from snapshot (e.g. 'e1')",
                        },
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                        "doubleClick": {
                            "type": "boolean",
                            "description": "Double-click instead of single click",
                            "default": False,
                        },
                    },
                    "required": ["ref"],
                },
            },
            # ============ 输入 ============
            {
                "name": "browser_type",
                "description": (
                    "Type text into an input field by its ref. Simulates keyboard typing. "
                    "Use 'submit: true' to press Enter after typing (e.g. for search boxes). "
                    "For clearing and replacing text, use browser_fill instead. "
                    "Returns updated snapshot automatically."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ref": {"type": "string", "description": "Element ref from snapshot"},
                        "text": {"type": "string", "description": "Text to type"},
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                        "submit": {
                            "type": "boolean",
                            "description": "Press Enter after typing",
                            "default": False,
                        },
                    },
                    "required": ["ref", "text"],
                },
            },
            # ============ 填充 ============
            {
                "name": "browser_fill",
                "description": (
                    "Fill (clear and set) an input field by its ref. Unlike browser_type, this "
                    "clears existing text first. Best for form fields. Returns updated snapshot."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ref": {"type": "string", "description": "Element ref from snapshot"},
                        "text": {"type": "string", "description": "Text to fill"},
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                    },
                    "required": ["ref", "text"],
                },
            },
            # ============ 文件上传 ============
            {
                "name": "browser_upload_file",
                "description": (
                    "Upload file(s) to a file input or by clicking an element that triggers "
                    "a file chooser. Returns updated snapshot."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ref": {
                            "type": "string",
                            "description": "Element ref (input[type=file] or button)",
                        },
                        "filePaths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Absolute paths of files to upload",
                        },
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                    },
                    "required": ["ref", "filePaths"],
                },
            },
            # ============ 弹窗管理 ============
            {
                "name": "browser_handle_dialog",
                "description": (
                    "Set how to handle future dialogs (alert/confirm/prompt). "
                    "Default is 'accept'."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mode": {
                            "type": "string",
                            "description": "Mode: 'accept' (default), 'dismiss', 'custom'",
                            "enum": ["accept", "dismiss", "custom"],
                        },
                        "customText": {
                            "type": "string",
                            "description": "Text for prompts in 'custom' mode",
                        },
                    },
                    "required": ["mode"],
                },
            },
            {
                "name": "browser_dialog_history",
                "description": "Get history of recent dialogs (alerts, confirms, prompts encountered).",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            # ============ 下载查询 ============
            {
                "name": "browser_get_downloads",
                "description": "Get list of files downloaded during this session.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            # ============ 滚动 ============
            {
                "name": "browser_scroll",
                "description": (
                    "Scroll the page. Use direction ('up'/'down'/'left'/'right') and amount in pixels. "
                    "Or provide a ref to scroll a specific element into view."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "direction": {
                            "type": "string",
                            "description": "Scroll direction",
                            "enum": ["up", "down", "left", "right"],
                            "default": "down",
                        },
                        "amount": {
                            "type": "integer",
                            "description": "Pixels to scroll",
                            "default": 500,
                        },
                        "ref": {
                            "type": "string",
                            "description": "Scroll element with this ref into view",
                        },
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                    },
                },
            },
            # ============ 悬停 ============
            {
                "name": "browser_hover",
                "description": "Hover over an element by its ref. Useful for triggering tooltips or dropdown menus.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ref": {"type": "string", "description": "Element ref from snapshot"},
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                    },
                    "required": ["ref"],
                },
            },
            # ============ 选择 ============
            {
                "name": "browser_select",
                "description": (
                    "Select option(s) from a dropdown/select element. "
                    "Pass values as an array of option values. Returns updated snapshot."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ref": {
                            "type": "string",
                            "description": "Element ref of the select/combobox",
                        },
                        "values": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Option value(s) to select",
                        },
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                    },
                    "required": ["ref", "values"],
                },
            },
            # ============ 按键 ============
            {
                "name": "browser_press",
                "description": (
                    "Press a keyboard key. Examples: 'Enter', 'Tab', 'Escape', 'ArrowDown', "
                    "'Control+a', 'Meta+c'. Use after focusing an element."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Key to press (e.g. 'Enter', 'Tab', 'Escape')",
                        },
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                    },
                    "required": ["key"],
                },
            },
            # ============ 获取文本 ============
            {
                "name": "browser_get_text",
                "description": "Get the text content of a specific element by its ref.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ref": {"type": "string", "description": "Element ref from snapshot"},
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                    },
                    "required": ["ref"],
                },
            },
            # ============ 获取属性 ============
            {
                "name": "browser_get_attribute",
                "description": "Get an attribute value of an element (e.g. 'href', 'src', 'class').",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ref": {"type": "string", "description": "Element ref from snapshot"},
                        "attribute": {
                            "type": "string",
                            "description": "Attribute name (e.g. 'href', 'src')",
                        },
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                    },
                    "required": ["ref", "attribute"],
                },
            },
            # ============ 等待元素 ============
            {
                "name": "browser_wait_for_element",
                "description": (
                    "Wait for an element to appear on the page. "
                    "Use CSS selectors like '#myId', '.myClass', 'button[type=submit]'. "
                    "Useful when waiting for dynamic content to load."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector to wait for"},
                        "timeout": {
                            "type": "integer",
                            "description": "Max wait time in ms",
                            "default": 30000,
                        },
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                    },
                    "required": ["selector"],
                },
            },
            # ============ 截图 ============
            {
                "name": "browser_screenshot",
                "description": "Take a screenshot of the current page or a specific element.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Output file path"},
                        "fullPage": {
                            "type": "boolean",
                            "description": "Capture full page",
                            "default": False,
                        },
                        "ref": {
                            "type": "string",
                            "description": "Element ref to screenshot (optional)",
                        },
                        "annotate": {
                            "type": "boolean",
                            "description": "Draw red boxes around interactive elements",
                            "default": False,
                        },
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                    },
                    "required": ["path"],
                },
            },
            # ============ 执行 JS ============
            {
                "name": "browser_evaluate",
                "description": (
                    "Execute JavaScript code in the browser. Use for advanced operations "
                    "not covered by other tools. Returns the evaluation result."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "script": {"type": "string", "description": "JavaScript code to execute"},
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                    },
                    "required": ["script"],
                },
            },
            # ============ 后退/前进/刷新 ============
            {
                "name": "browser_go_back",
                "description": "Go back to the previous page.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                    },
                },
            },
            {
                "name": "browser_go_forward",
                "description": "Go forward to the next page.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                    },
                },
            },
            {
                "name": "browser_reload",
                "description": "Reload the current page.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                        "targetId": {"type": "string", "description": "Tab ID (optional)"},
                    },
                },
            },
            # ============ 标签页管理 ============
            {
                "name": "browser_tabs_list",
                "description": "List all open browser tabs.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                    },
                },
            },
            {
                "name": "browser_tabs_open",
                "description": "Open a new browser tab, optionally navigating to a URL.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to open (default: about:blank)",
                            "default": "about:blank",
                        },
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                    },
                },
            },
            {
                "name": "browser_tabs_close",
                "description": "Close a browser tab by its target ID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "targetId": {"type": "string", "description": "Tab ID to close"},
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                    },
                    "required": ["targetId"],
                },
            },
            {
                "name": "browser_tabs_focus",
                "description": "Switch focus to a specific tab by its target ID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "targetId": {"type": "string", "description": "Tab ID to focus"},
                        "browserId": {
                            "type": "string",
                            "description": "Browser instance ID (optional)",
                        },
                    },
                    "required": ["targetId"],
                },
            },
            # ============ 浏览器管理 ============
            {
                "name": "browser_start",
                "description": "Start a new browser instance.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "profile": {"type": "string", "description": "Profile name (optional)"},
                    },
                },
            },
            {
                "name": "browser_close",
                "description": "Close a browser instance.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "browserId": {"type": "string", "description": "Browser ID to close"},
                    },
                    "required": ["browserId"],
                },
            },
            {
                "name": "browser_status",
                "description": "Get current browser server status.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]

    async def handle_tool_call(self, name: str, arguments: dict[str, Any]) -> str:
        """处理工具调用 - 增强版路由"""
        try:
            # 导航
            if name == "browser_navigate":
                resp = await self.client.post(f"{self.base_url}/api/v1/navigate", json=arguments)
                return self._format_response(resp)

            # 导航+快照（复合）
            elif name == "browser_navigate_and_snapshot":
                resp = await self.client.post(
                    f"{self.base_url}/api/v1/navigate_and_snapshot", json=arguments
                )
                data = resp.json()
                # 精简返回：只返回 LLM 需要的字段
                return json.dumps(
                    {
                        "url": data.get("url"),
                        "title": data.get("title"),
                        "summary": data.get("summary"),
                        "interactive": data.get("interactive"),
                    },
                    ensure_ascii=False,
                )

            # 快照
            elif name == "browser_snapshot":
                resp = await self.client.post(f"{self.base_url}/api/v1/snapshot", json=arguments)
                data = resp.json()
                return json.dumps(
                    {
                        "url": data.get("url"),
                        "title": data.get("title"),
                        "summary": data.get("summary"),
                        "interactive": data.get("interactive"),
                    },
                    ensure_ascii=False,
                )

            # 点击
            elif name == "browser_click":
                resp = await self.client.post(f"{self.base_url}/api/v1/act/click", json=arguments)
                data = resp.json()
                # 返回操作结果 + 新快照（精简版）
                result = {"clicked": data.get("clicked")}
                if "snapshot" in data:
                    result["snapshot"] = {
                        "url": data["snapshot"].get("url"),
                        "title": data["snapshot"].get("title"),
                        "summary": data["snapshot"].get("summary"),
                        "interactive": data["snapshot"].get("interactive"),
                    }
                return json.dumps(result, ensure_ascii=False)

            # 输入
            elif name == "browser_type":
                resp = await self.client.post(f"{self.base_url}/api/v1/act/type", json=arguments)
                data = resp.json()
                result = {"typed": data.get("typed")}
                if "snapshot" in data:
                    result["snapshot"] = {
                        "url": data["snapshot"].get("url"),
                        "title": data["snapshot"].get("title"),
                        "summary": data["snapshot"].get("summary"),
                        "interactive": data["snapshot"].get("interactive"),
                    }
                return json.dumps(result, ensure_ascii=False)

            # 填充
            elif name == "browser_fill":
                resp = await self.client.post(f"{self.base_url}/api/v1/act/fill", json=arguments)
                data = resp.json()
                result = {"filled": data.get("filled")}
                if "snapshot" in data:
                    result["snapshot"] = {
                        "url": data["snapshot"].get("url"),
                        "title": data["snapshot"].get("title"),
                        "summary": data["snapshot"].get("summary"),
                        "interactive": data["snapshot"].get("interactive"),
                    }
                return json.dumps(result, ensure_ascii=False)

            # 批量填表
            elif name == "browser_fill_form":
                resp = await self.client.post(
                    f"{self.base_url}/api/v1/act/fill_form", json=arguments
                )
                data = resp.json()
                result = {
                    "fieldsFilled": data.get("fieldsFilled"),
                    "submitted": data.get("submitted"),
                }
                if "snapshot" in data:
                    result["snapshot"] = {
                        "url": data["snapshot"].get("url"),
                        "title": data["snapshot"].get("title"),
                        "interactive": data["snapshot"].get("interactive"),
                        "summary": data["snapshot"].get("summary"),
                    }
                return json.dumps(result, ensure_ascii=False)

            elif name == "browser_scroll":
                resp = await self.client.post(f"{self.base_url}/api/v1/scroll", json=arguments)
                data = resp.json()
                result = {"scrolled": True}
                if "snapshot" in data:
                    result["snapshot"] = {
                        "url": data["snapshot"].get("url"),
                        "title": data["snapshot"].get("title"),
                        "summary": data["snapshot"].get("summary"),
                        "interactive": data["snapshot"].get("interactive"),
                    }
                return json.dumps(result, ensure_ascii=False)

            # 文件上传
            elif name == "browser_upload_file":
                resp = await self.client.post(f"{self.base_url}/api/v1/act/upload", json=arguments)
                data = resp.json()
                result = {"uploaded": data.get("uploaded")}
                if "snapshot" in data:
                    result["snapshot"] = {
                        "url": data["snapshot"].get("url"),
                        "title": data["snapshot"].get("title"),
                        "summary": data["snapshot"].get("summary"),
                        "interactive": data["snapshot"].get("interactive"),
                    }
                return json.dumps(result, ensure_ascii=False)

            # 弹窗管理
            elif name == "browser_handle_dialog":
                resp = await self.client.post(
                    f"{self.base_url}/api/v1/dialog/handle", json=arguments
                )
                return self._format_response(resp)

            elif name == "browser_dialog_history":
                resp = await self.client.get(f"{self.base_url}/api/v1/dialog/history")
                return self._format_response(resp)

            # 下载查询
            elif name == "browser_get_downloads":
                resp = await self.client.get(f"{self.base_url}/api/v1/act/downloads")
                return self._format_response(resp)

            elif name == "browser_hover":
                resp = await self.client.post(f"{self.base_url}/api/v1/act/hover", json=arguments)
                data = resp.json()
                result = {"hovered": data.get("hovered")}
                if "snapshot" in data:
                    result["snapshot"] = {
                        "url": data["snapshot"].get("url"),
                        "title": data["snapshot"].get("title"),
                        "summary": data["snapshot"].get("summary"),
                        "interactive": data["snapshot"].get("interactive"),
                    }
                return json.dumps(result, ensure_ascii=False)

            # 选择
            elif name == "browser_select":
                resp = await self.client.post(f"{self.base_url}/api/v1/act/select", json=arguments)
                data = resp.json()
                result = {"selected": data.get("selected")}
                if "snapshot" in data:
                    result["snapshot"] = {
                        "url": data["snapshot"].get("url"),
                        "title": data["snapshot"].get("title"),
                        "summary": data["snapshot"].get("summary"),
                        "interactive": data["snapshot"].get("interactive"),
                    }
                return json.dumps(result, ensure_ascii=False)

            elif name == "browser_press":
                resp = await self.client.post(f"{self.base_url}/api/v1/act/press", json=arguments)
                data = resp.json()
                result = {"key": data.get("key")}
                if "snapshot" in data:
                    result["snapshot"] = {
                        "url": data["snapshot"].get("url"),
                        "title": data["snapshot"].get("title"),
                        "summary": data["snapshot"].get("summary"),
                        "interactive": data["snapshot"].get("interactive"),
                    }
                return json.dumps(result, ensure_ascii=False)

            # 获取文本
            elif name == "browser_get_text":
                resp = await self.client.post(f"{self.base_url}/api/v1/get_text", json=arguments)
                data = resp.json()
                return json.dumps(
                    {"text": data.get("data", {}).get("text", "")}, ensure_ascii=False
                )

            # 获取属性
            elif name == "browser_get_attribute":
                resp = await self.client.post(
                    f"{self.base_url}/api/v1/get_attribute", json=arguments
                )
                data = resp.json()
                return json.dumps(
                    {
                        "attribute": data.get("data", {}).get("attribute"),
                        "value": data.get("data", {}).get("value"),
                    },
                    ensure_ascii=False,
                )

            # 等待元素
            elif name == "browser_wait_for_element":
                resp = await self.client.post(
                    f"{self.base_url}/api/v1/act/wait_for_element", json=arguments
                )
                data = resp.json()
                return json.dumps({"found": data.get("found", False)}, ensure_ascii=False)

            # 截图
            elif name == "browser_screenshot":
                resp = await self.client.post(f"{self.base_url}/api/v1/screenshot", json=arguments)
                return self._format_response(resp)

            elif name == "browser_evaluate":
                resp = await self.client.post(
                    f"{self.base_url}/api/v1/act/evaluate", json=arguments
                )
                data = resp.json()
                result = {"result": data.get("data", {}).get("result")}
                if "snapshot" in data:
                    result["snapshot"] = {
                        "url": data["snapshot"].get("url"),
                        "title": data["snapshot"].get("title"),
                        "summary": data["snapshot"].get("summary"),
                        "interactive": data["snapshot"].get("interactive"),
                    }
                return json.dumps(result, ensure_ascii=False)

            # 后退
            elif name == "browser_go_back":
                resp = await self.client.post(f"{self.base_url}/api/v1/go-back", params=arguments)
                data = resp.json()
                result = {"url": data.get("url")}
                if "snapshot" in data:
                    result["snapshot"] = {
                        "url": data["snapshot"].get("url"),
                        "title": data["snapshot"].get("title"),
                        "summary": data["snapshot"].get("summary"),
                        "interactive": data["snapshot"].get("interactive"),
                    }
                return json.dumps(result, ensure_ascii=False)

            # 前进
            elif name == "browser_go_forward":
                resp = await self.client.post(
                    f"{self.base_url}/api/v1/go-forward", params=arguments
                )
                data = resp.json()
                result = {"url": data.get("url")}
                if "snapshot" in data:
                    result["snapshot"] = {
                        "url": data["snapshot"].get("url"),
                        "title": data["snapshot"].get("title"),
                        "summary": data["snapshot"].get("summary"),
                        "interactive": data["snapshot"].get("interactive"),
                    }
                return json.dumps(result, ensure_ascii=False)

            # 刷新
            elif name == "browser_reload":
                resp = await self.client.post(f"{self.base_url}/api/v1/reload", params=arguments)
                data = resp.json()
                result = {"url": data.get("url")}
                if "snapshot" in data:
                    result["snapshot"] = {
                        "url": data["snapshot"].get("url"),
                        "title": data["snapshot"].get("title"),
                        "summary": data["snapshot"].get("summary"),
                        "interactive": data["snapshot"].get("interactive"),
                    }
                return json.dumps(result, ensure_ascii=False)

            # 标签页操作
            elif name == "browser_tabs_list":
                params = {}
                if "browserId" in arguments:
                    params["browserId"] = arguments["browserId"]
                resp = await self.client.get(f"{self.base_url}/api/v1/tabs", params=params)
                return self._format_response(resp)

            elif name == "browser_tabs_open":
                resp = await self.client.post(f"{self.base_url}/api/v1/tabs/open", json=arguments)
                return self._format_response(resp)

            elif name == "browser_tabs_close":
                resp = await self.client.post(f"{self.base_url}/api/v1/tabs/close", json=arguments)
                return self._format_response(resp)

            elif name == "browser_tabs_focus":
                resp = await self.client.post(f"{self.base_url}/api/v1/tabs/focus", json=arguments)
                return self._format_response(resp)

            # 浏览器管理
            elif name == "browser_start":
                params = {}
                if "profile" in arguments:
                    params["profile"] = arguments["profile"]
                resp = await self.client.post(f"{self.base_url}/start", params=params)
                return self._format_response(resp)

            elif name == "browser_close":
                browser_id = arguments.get("browserId", "")
                resp = await self.client.post(f"{self.base_url}/browsers/{browser_id}/close")
                return self._format_response(resp)

            elif name == "browser_status":
                resp = await self.client.get(f"{self.base_url}/")
                return self._format_response(resp)

            else:
                return json.dumps({"error": f"Unknown tool: {name}"})

        except httpx.HTTPError as e:
            return json.dumps({"error": f"HTTP error: {str(e)}"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _format_response(self, resp: httpx.Response) -> str:
        """格式化 HTTP 响应"""
        try:
            data = resp.json()
            # 移除冗余字段，精简返回
            for key in ["ok", "success", "elements", "text"]:
                data.pop(key, None)
            # 去掉空值
            data = {k: v for k, v in data.items() if v is not None}
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            return resp.text

    # ============ MCP STDIO 协议实现 ============

    async def run(self):
        """运行 MCP 服务器（STDIO 模式）"""
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin.buffer)

        writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout.buffer
        )
        writer = asyncio.StreamWriter(
            writer_transport, writer_protocol, reader, asyncio.get_event_loop()
        )

        while True:
            try:
                line = await reader.readline()
                if not line:
                    break

                line = line.decode("utf-8").strip()
                if not line:
                    continue

                request = json.loads(line)
                response = await self._handle_request(request)

                if response:
                    response_line = json.dumps(response, ensure_ascii=False) + "\n"
                    writer.write(response_line.encode("utf-8"))
                    await writer.drain()

            except json.JSONDecodeError:
                continue
            except Exception as e:
                logger.error(f"MCP error: {e}")
                continue

    async def _handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """处理 MCP 请求"""
        method = request.get("method", "")
        req_id = request.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": False},
                    },
                    "serverInfo": {
                        "name": "qianji",
                        "version": "2.0.0",
                    },
                    "instructions": (
                        "Browser automation tool for web navigation and interaction. "
                        "Key tools: browser_navigate_and_snapshot (navigate + get page state), "
                        "browser_click (click element), browser_type (type text), "
                        "browser_fill (clear and fill input). "
                        "Always use browser_navigate_and_snapshot first when visiting a new URL."
                    ),
                },
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": self.tools,
                },
            }

        elif method == "tools/call":
            params = request.get("params", {})
            name = params.get("name", "")
            arguments = params.get("arguments", {})

            result = await self.handle_tool_call(name, arguments)

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result,
                        }
                    ],
                    "isError": "error" in result.lower() if isinstance(result, str) else False,
                },
            }

        elif method == "notifications/initialized":
            return None  # 不需要回复

        elif method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {},
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}",
            },
        }


def main():
    """MCP 服务器入口点"""
    server = QianjiMCPServer()
    asyncio.run(server.run())


def sync_main():
    """同步入口点（用于 pyproject.toml scripts）"""
    main()


if __name__ == "__main__":
    main()
