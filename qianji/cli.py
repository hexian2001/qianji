"""
命令行接口 - 提供 CLI 工具
"""

import asyncio
import argparse
import json
import sys
from typing import Optional

import httpx


class QianjiClient:
    """qianji HTTP 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:18791"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        await self.client.aclose()
    
    async def status(self) -> dict:
        """获取状态"""
        resp = await self.client.get(f"{self.base_url}/")
        resp.raise_for_status()
        return resp.json()
    
    async def start(self, profile: Optional[str] = None) -> dict:
        """启动浏览器"""
        resp = await self.client.post(f"{self.base_url}/start", params={"profile": profile})
        resp.raise_for_status()
        return resp.json()
    
    async def stop(self) -> dict:
        """停止浏览器"""
        resp = await self.client.post(f"{self.base_url}/stop")
        resp.raise_for_status()
        return resp.json()
    
    async def navigate(self, url: str, target_id: Optional[str] = None) -> dict:
        """导航"""
        data = {"url": url}
        if target_id:
            data["targetId"] = target_id
        resp = await self.client.post(f"{self.base_url}/api/v1/navigate", json=data)
        resp.raise_for_status()
        return resp.json()
    
    async def snapshot(self, target_id: Optional[str] = None) -> dict:
        """获取快照"""
        data = {}
        if target_id:
            data["targetId"] = target_id
        resp = await self.client.post(f"{self.base_url}/api/v1/snapshot", json=data)
        resp.raise_for_status()
        return resp.json()
    
    async def click(self, ref: str, target_id: Optional[str] = None) -> dict:
        """点击"""
        data = {"ref": ref}
        if target_id:
            data["targetId"] = target_id
        resp = await self.client.post(f"{self.base_url}/api/v1/act/click", json=data)
        resp.raise_for_status()
        return resp.json()
    
    async def type(self, ref: str, text: str, target_id: Optional[str] = None, submit: bool = False) -> dict:
        """输入"""
        data = {"ref": ref, "text": text, "submit": submit}
        if target_id:
            data["targetId"] = target_id
        resp = await self.client.post(f"{self.base_url}/api/v1/act/type", json=data)
        resp.raise_for_status()
        return resp.json()
    
    async def screenshot(self, path: str, target_id: Optional[str] = None, full_page: bool = False) -> dict:
        """截图"""
        data = {"path": path, "fullPage": full_page}
        if target_id:
            data["targetId"] = target_id
        resp = await self.client.post(f"{self.base_url}/api/v1/screenshot", json=data)
        resp.raise_for_status()
        return resp.json()


async def cmd_status(client: QianjiClient, args):
    """状态命令"""
    status = await client.status()
    print(json.dumps(status, indent=2, ensure_ascii=False))


async def cmd_start(client: QianjiClient, args):
    """启动命令"""
    result = await client.start(args.profile)
    print(f"✓ Browser started: {result}")


async def cmd_stop(client: QianjiClient, args):
    """停止命令"""
    result = await client.stop()
    print(f"✓ Browser stopped: {result}")


async def cmd_navigate(client: QianjiClient, args):
    """导航命令"""
    result = await client.navigate(args.url, args.target)
    print(f"✓ Navigated to: {result.get('url')}")
    print(f"  Title: {result.get('title')}")


async def cmd_snapshot(client: QianjiClient, args):
    """快照命令"""
    result = await client.snapshot(args.target)
    print(f"✓ Snapshot of: {result.get('url')}")
    print(f"  Title: {result.get('title')}")
    print(f"\n  Interactive elements:")
    print(result.get('interactive', 'None'))


async def cmd_click(client: QianjiClient, args):
    """点击命令"""
    result = await client.click(args.ref, args.target)
    print(f"✓ Clicked: {args.ref}")


async def cmd_type(client: QianjiClient, args):
    """输入命令"""
    result = await client.type(args.ref, args.text, args.target, args.submit)
    print(f"✓ Typed into: {args.ref}")


async def cmd_screenshot(client: QianjiClient, args):
    """截图命令"""
    result = await client.screenshot(args.output, args.target, args.full_page)
    print(f"✓ Screenshot saved: {result.get('path')}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="qianji CLI - Universal Browser Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  qianji status                    # 查看状态
  qianji start                     # 启动浏览器
  qianji navigate https://example.com
  qianji snapshot                  # 获取页面快照
  qianji click e1                  # 点击元素 e1
  qianji type e2 "hello world"     # 在 e2 输入文本
  qianji screenshot output.png     # 截图
        """
    )
    
    parser.add_argument("--server", default="http://localhost:18791", help="Server URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # status
    subparsers.add_parser("status", help="Get server status")
    
    # start
    start_parser = subparsers.add_parser("start", help="Start browser")
    start_parser.add_argument("--profile", help="Profile name")
    
    # stop
    subparsers.add_parser("stop", help="Stop browser")
    
    # navigate
    nav_parser = subparsers.add_parser("navigate", help="Navigate to URL")
    nav_parser.add_argument("url", help="URL to navigate")
    nav_parser.add_argument("--target", help="Target tab ID")
    
    # snapshot
    snap_parser = subparsers.add_parser("snapshot", help="Get page snapshot")
    snap_parser.add_argument("--target", help="Target tab ID")
    
    # click
    click_parser = subparsers.add_parser("click", help="Click element")
    click_parser.add_argument("ref", help="Element ref (e.g., e1)")
    click_parser.add_argument("--target", help="Target tab ID")
    
    # type
    type_parser = subparsers.add_parser("type", help="Type text")
    type_parser.add_argument("ref", help="Element ref")
    type_parser.add_argument("text", help="Text to type")
    type_parser.add_argument("--target", help="Target tab ID")
    type_parser.add_argument("--submit", action="store_true", help="Press Enter after typing")
    
    # screenshot
    ss_parser = subparsers.add_parser("screenshot", help="Take screenshot")
    ss_parser.add_argument("output", help="Output file path")
    ss_parser.add_argument("--target", help="Target tab ID")
    ss_parser.add_argument("--full-page", action="store_true", help="Full page screenshot")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    client = QianjiClient(args.server)
    
    try:
        commands = {
            "status": cmd_status,
            "start": cmd_start,
            "stop": cmd_stop,
            "navigate": cmd_navigate,
            "snapshot": cmd_snapshot,
            "click": cmd_click,
            "type": cmd_type,
            "screenshot": cmd_screenshot,
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
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
