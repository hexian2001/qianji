"""
命令行接口 - 直接模式（无需服务器）
直接控制浏览器，不通过 HTTP API
"""

import asyncio
import argparse
import json
import sys
from typing import Optional

from .core.browser_manager import BrowserManager
from .core.pw_client import PlaywrightClient
from .models.config import BrowserConfig


class QianjiDirectClient:
    """qianji 直接客户端 - 不通过 HTTP，直接控制"""
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig.from_env()
        self.browser_manager: Optional[BrowserManager] = None
        self.pw_client = PlaywrightClient()
    
    async def ensure_browser(self):
        """确保浏览器已启动"""
        if self.browser_manager is None:
            self.browser_manager = BrowserManager(self.config)
        
        if not self.browser_manager.is_running:
            await self.browser_manager.start()
            print(f"✓ Browser started (headless={self.config.headless})")
    
    async def status(self) -> dict:
        """获取状态"""
        if self.browser_manager and self.browser_manager.is_running:
            return {
                "running": True,
                "profile": self.browser_manager._profile.name if self.browser_manager._profile else None,
                "tabs": len(self.browser_manager.tab_manager.tabs),
            }
        return {"running": False}
    
    async def start(self, profile: Optional[str] = None):
        """启动浏览器"""
        await self.ensure_browser()
        return {"ok": True, "profile": profile or self.config.default_profile}
    
    async def stop(self):
        """停止浏览器"""
        if self.browser_manager and self.browser_manager.is_running:
            await self.browser_manager.stop()
            print("✓ Browser stopped")
            return {"ok": True}
        return {"ok": True, "message": "Browser not running"}
    
    async def navigate(self, url: str) -> dict:
        """导航"""
        await self.ensure_browser()
        tab = self.browser_manager.tab_manager.get_tab()
        if not tab:
            raise RuntimeError("No tab available")
        
        result = await self.pw_client.navigate(tab.page, url)
        await tab.update_info()
        
        return {
            "ok": True,
            "url": result["url"],
            "title": result.get("title"),
        }
    
    async def snapshot(self) -> dict:
        """获取快照"""
        await self.ensure_browser()
        tab = self.browser_manager.tab_manager.get_tab()
        if not tab:
            raise RuntimeError("No tab available")
        
        snapshot = await self.pw_client.create_snapshot(tab.page)
        await tab.update_info()
        
        return {
            "ok": True,
            "url": snapshot.url,
            "title": snapshot.title,
            "text": snapshot.text[:5000],
            "interactive": snapshot.to_interactive_text(),
        }
    
    async def click(self, ref: str) -> dict:
        """点击"""
        await self.ensure_browser()
        tab = self.browser_manager.tab_manager.get_tab()
        if not tab:
            raise RuntimeError("No tab available")
        
        # 先创建快照
        snapshot = await self.pw_client.create_snapshot(tab.page)
        
        # 点击
        await self.pw_client.click_by_ref(tab.page, ref, snapshot)
        await tab.update_info()
        
        return {"ok": True, "url": tab.url}
    
    async def fill(self, ref: str, text: str) -> dict:
        """填充表单"""
        await self.ensure_browser()
        tab = self.browser_manager.tab_manager.get_tab()
        if not tab:
            raise RuntimeError("No tab available")
        
        snapshot = await self.pw_client.create_snapshot(tab.page)
        await self.pw_client.fill_by_ref(tab.page, ref, text, snapshot)
        
        return {"ok": True}
    
    async def type(self, ref: str, text: str, submit: bool = False) -> dict:
        """输入文本"""
        await self.ensure_browser()
        tab = self.browser_manager.tab_manager.get_tab()
        if not tab:
            raise RuntimeError("No tab available")
        
        snapshot = await self.pw_client.create_snapshot(tab.page)
        await self.pw_client.type_by_ref(tab.page, ref, text, snapshot, submit=submit)
        
        return {"ok": True}
    
    async def screenshot(self, path: str, full_page: bool = False) -> dict:
        """截图"""
        await self.ensure_browser()
        tab = self.browser_manager.tab_manager.get_tab()
        if not tab:
            raise RuntimeError("No tab available")
        
        await self.pw_client.screenshot(tab.page, path, full_page=full_page)
        
        return {"ok": True, "path": path}
    
    async def evaluate(self, script: str) -> dict:
        """执行 JavaScript"""
        await self.ensure_browser()
        tab = self.browser_manager.tab_manager.get_tab()
        if not tab:
            raise RuntimeError("No tab available")
        
        result = await self.pw_client.evaluate(tab.page, script)
        
        return {"ok": True, "result": result}
    
    async def close(self):
        """关闭"""
        if self.browser_manager and self.browser_manager.is_running:
            await self.browser_manager.stop()


async def cmd_status(client: QianjiDirectClient, args):
    """状态命令"""
    status = await client.status()
    print(json.dumps(status, indent=2, ensure_ascii=False))


async def cmd_start(client: QianjiDirectClient, args):
    """启动命令"""
    result = await client.start(args.profile)
    print(f"✓ Browser started")


async def cmd_stop(client: QianjiDirectClient, args):
    """停止命令"""
    result = await client.stop()
    print(f"✓ Browser stopped")


async def cmd_navigate(client: QianjiDirectClient, args):
    """导航命令"""
    result = await client.navigate(args.url)
    print(f"✓ Navigated to: {result.get('url')}")
    print(f"  Title: {result.get('title')}")


async def cmd_snapshot(client: QianjiDirectClient, args):
    """快照命令"""
    result = await client.snapshot()
    print(f"✓ Snapshot of: {result.get('url')}")
    print(f"  Title: {result.get('title')}")
    print(f"\n  Interactive elements:")
    print(result.get('interactive', 'None'))


async def cmd_click(client: QianjiDirectClient, args):
    """点击命令"""
    result = await client.click(args.ref)
    print(f"✓ Clicked: {args.ref}")


async def cmd_fill(client: QianjiDirectClient, args):
    """填充命令"""
    result = await client.fill(args.ref, args.text)
    print(f"✓ Filled: {args.ref}")


async def cmd_type(client: QianjiDirectClient, args):
    """输入命令"""
    result = await client.type(args.ref, args.text, args.submit)
    print(f"✓ Typed into: {args.ref}")


async def cmd_screenshot(client: QianjiDirectClient, args):
    """截图命令"""
    result = await client.screenshot(args.output, args.full_page)
    print(f"✓ Screenshot saved: {result.get('path')}")


async def cmd_evaluate(client: QianjiDirectClient, args):
    """执行 JS 命令"""
    result = await client.evaluate(args.script)
    print(f"✓ Result:")
    print(json.dumps(result.get('result'), indent=2, ensure_ascii=False))


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="qianji CLI - Universal Browser Automation (Direct Mode)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  qianji status                    # 查看状态
  qianji start                     # 启动浏览器
  qianji navigate https://example.com
  qianji snapshot                  # 获取页面快照
  qianji click e1                  # 点击元素 e1
  qianji fill e2 "hello world"     # 在 e2 填充文本
  qianji type e3 "hello" --submit  # 在 e3 输入并提交
  qianji screenshot output.png     # 截图
  qianji evaluate "document.title" # 执行 JS
  qianji stop                      # 停止浏览器

Environment Variables:
  QIANJI_HEADLESS=true|false       # 无头模式
  QIANJI_BROWSER_PATH=/path/to/chrome  # 浏览器路径
  QIANJI_NO_SANDBOX=true           # 禁用沙盒
        """
    )
    
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--browser-path", help="Path to browser executable")
    parser.add_argument("--no-sandbox", action="store_true", help="Disable sandbox")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # status
    subparsers.add_parser("status", help="Get browser status")
    
    # start
    start_parser = subparsers.add_parser("start", help="Start browser")
    start_parser.add_argument("--profile", help="Profile name")
    
    # stop
    subparsers.add_parser("stop", help="Stop browser")
    
    # navigate
    nav_parser = subparsers.add_parser("navigate", help="Navigate to URL")
    nav_parser.add_argument("url", help="URL to navigate")
    
    # snapshot
    subparsers.add_parser("snapshot", help="Get page snapshot")
    
    # click
    click_parser = subparsers.add_parser("click", help="Click element")
    click_parser.add_argument("ref", help="Element ref (e.g., e1)")
    
    # fill
    fill_parser = subparsers.add_parser("fill", help="Fill form field")
    fill_parser.add_argument("ref", help="Element ref")
    fill_parser.add_argument("text", help="Text to fill")
    
    # type
    type_parser = subparsers.add_parser("type", help="Type text")
    type_parser.add_argument("ref", help="Element ref")
    type_parser.add_argument("text", help="Text to type")
    type_parser.add_argument("--submit", action="store_true", help="Press Enter after typing")
    
    # screenshot
    ss_parser = subparsers.add_parser("screenshot", help="Take screenshot")
    ss_parser.add_argument("output", help="Output file path")
    ss_parser.add_argument("--full-page", action="store_true", help="Full page screenshot")
    
    # evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Execute JavaScript")
    eval_parser.add_argument("script", help="JavaScript code")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 加载配置
    config = BrowserConfig.from_env()
    
    # 命令行参数覆盖环境变量
    if args.headless:
        config.headless = True
    if args.browser_path:
        config.executable_path = args.browser_path
    if args.no_sandbox:
        config.no_sandbox = True
    
    client = QianjiDirectClient(config)
    
    try:
        commands = {
            "status": cmd_status,
            "start": cmd_start,
            "stop": cmd_stop,
            "navigate": cmd_navigate,
            "snapshot": cmd_snapshot,
            "click": cmd_click,
            "fill": cmd_fill,
            "type": cmd_type,
            "screenshot": cmd_screenshot,
            "evaluate": cmd_evaluate,
        }
        
        cmd_func = commands.get(args.command)
        if cmd_func:
            await cmd_func(client, args)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        # 如果不是 stop 命令，保持浏览器运行
        if args.command == "stop":
            await client.close()


def sync_main():
    """同步入口函数"""
    asyncio.run(main())


if __name__ == "__main__":
    sync_main()
