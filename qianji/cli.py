"""
命令行接口 - 提供 CLI 工具
支持多浏览器架构
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from typing import Any

import httpx


def is_root_user() -> bool:
    """检测是否为 root 用户"""
    try:
        return os.getuid() == 0
    except AttributeError:
        # Windows 系统没有 getuid
        return False


def is_server_running(base_url: str) -> bool:
    """检测服务器是否正在运行"""
    try:
        import urllib.request

        urllib.request.urlopen(f"{base_url}/", timeout=2)
        return True
    except:
        return False


def start_server_in_background(port: int = 18796) -> bool:
    """在后台启动服务器（使用 nohup）"""
    try:
        # 获取 Python 解释器路径
        python_cmd = sys.executable

        # 构建启动命令
        cmd = [
            "nohup",
            python_cmd,
            "-m",
            "qianji.server",
            "--port",
            str(port),
            "--no-sandbox" if is_root_user() else "",
        ]
        # 过滤空字符串
        cmd = [c for c in cmd if c]

        # 启动服务器（后台运行）
        log_file = "/tmp/qianji_server.log"
        with open(log_file, "w") as f:
            subprocess.Popen(
                cmd, stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, close_fds=True
            )

        # 等待服务器启动
        base_url = f"http://localhost:{port}"
        for i in range(30):  # 最多等待 30 秒
            if is_server_running(base_url):
                return True
            time.sleep(1)

        return False
    except Exception as e:
        print(f"启动服务器失败: {e}")
        return False


async def ensure_server(base_url: str) -> bool:
    """确保服务器正在运行"""
    if is_server_running(base_url):
        return True

    # 从 URL 中提取端口
    try:
        port = int(base_url.split(":")[-1].split("/")[0])
    except:
        port = 18796

    print(f"⏳ 服务器未运行，正在启动（端口 {port}）...")

    if start_server_in_background(port):
        print(f"✓ 服务器已启动: {base_url}")
        return True
    else:
        print("✗ 服务器启动失败")
        return False


def output_result(data: Any, format_type: str = "text", prefix: str = ""):
    """统一输出结果

    Args:
        data: 要输出的数据
        format_type: 输出格式，"text" 或 "json"
        prefix: text 格式时的前缀
    """
    if format_type == "json":
        if isinstance(data, dict) or isinstance(data, list):
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(json.dumps({"result": data}, indent=2, ensure_ascii=False))
    else:
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    print(f"{prefix}{key}:")
                    output_result(value, format_type, prefix + "  ")
                elif isinstance(value, list):
                    print(f"{prefix}{key}:")
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            print(f"{prefix}  [{i}]:")
                            output_result(item, format_type, prefix + "    ")
                        else:
                            print(f"{prefix}  - {item}")
                else:
                    print(f"{prefix}{key}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    print(f"{prefix}[{i}]:")
                    output_result(item, format_type, prefix + "  ")
                else:
                    print(f"{prefix}- {item}")
        else:
            print(f"{prefix}{data}")


class QianjiClient:
    """qianji HTTP 客户端 - 支持多浏览器"""

    def __init__(self, base_url: str = "http://localhost:18796"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.client.aclose()

    async def status(self) -> dict:
        """获取状态"""
        resp = await self.client.get(f"{self.base_url}/")
        resp.raise_for_status()
        return resp.json()

    async def start(
        self,
        profile: str | None = None,
        headless: bool | None = None,
        no_sandbox: bool | None = None,
        args: list | None = None,
    ) -> dict:
        """启动浏览器"""
        params = {}
        if profile:
            params["profile"] = profile
        if headless is not None:
            params["headless"] = headless
        if no_sandbox is not None:
            params["no_sandbox"] = no_sandbox
        if args:
            params["args"] = args
        resp = await self.client.post(f"{self.base_url}/start", params=params)
        resp.raise_for_status()
        return resp.json()

    async def stop(self, browser_id: str | None = None) -> dict:
        """停止浏览器"""
        params = {"browser_id": browser_id} if browser_id else None
        resp = await self.client.post(f"{self.base_url}/stop", params=params)
        resp.raise_for_status()
        return resp.json()

    async def list_browsers(self) -> dict:
        """列出所有浏览器"""
        resp = await self.client.get(f"{self.base_url}/browsers")
        resp.raise_for_status()
        return resp.json()

    async def create_browser(
        self,
        profile: str | None = None,
        browser_id: str | None = None,
        headless: bool | None = None,
        no_sandbox: bool | None = None,
        args: list | None = None,
    ) -> dict:
        """创建新浏览器"""
        params = {}
        if profile:
            params["profile"] = profile
        if browser_id:
            params["browser_id"] = browser_id
        if headless is not None:
            params["headless"] = headless
        if no_sandbox is not None:
            params["no_sandbox"] = no_sandbox
        if args:
            params["args"] = args
        resp = await self.client.post(f"{self.base_url}/browsers/create", params=params)
        resp.raise_for_status()
        return resp.json()

    async def close_browser(self, browser_id: str) -> dict:
        """关闭指定浏览器"""
        resp = await self.client.post(f"{self.base_url}/browsers/{browser_id}/close")
        resp.raise_for_status()
        return resp.json()

    async def list_tabs(self, browser_id: str | None = None) -> dict:
        """列出所有标签页"""
        params = {"browserId": browser_id} if browser_id else None
        resp = await self.client.get(f"{self.base_url}/api/v1/tabs", params=params)
        resp.raise_for_status()
        return resp.json()

    async def open_tab(self, url: str = "about:blank", browser_id: str | None = None) -> dict:
        """打开新标签页"""
        data = {"url": url}
        if browser_id:
            data["browserId"] = browser_id
        resp = await self.client.post(f"{self.base_url}/api/v1/tabs/open", json=data)
        resp.raise_for_status()
        return resp.json()

    async def close_tab(self, target_id: str, browser_id: str | None = None) -> dict:
        """关闭标签页"""
        data = {"targetId": target_id}
        if browser_id:
            data["browserId"] = browser_id
        resp = await self.client.post(f"{self.base_url}/api/v1/tabs/close", json=data)
        resp.raise_for_status()
        return resp.json()

    async def navigate(
        self, url: str, browser_id: str | None = None, target_id: str | None = None
    ) -> dict:
        """导航"""
        data = {"url": url}
        if browser_id:
            data["browserId"] = browser_id
        if target_id:
            data["targetId"] = target_id
        resp = await self.client.post(f"{self.base_url}/api/v1/navigate", json=data)
        resp.raise_for_status()
        return resp.json()

    async def snapshot(self, browser_id: str | None = None, target_id: str | None = None) -> dict:
        """获取快照"""
        data = {}
        if browser_id:
            data["browserId"] = browser_id
        if target_id:
            data["targetId"] = target_id
        resp = await self.client.post(f"{self.base_url}/api/v1/snapshot", json=data)
        resp.raise_for_status()
        return resp.json()

    async def click(
        self, ref: str, browser_id: str | None = None, target_id: str | None = None
    ) -> dict:
        """点击"""
        data = {"ref": ref}
        if browser_id:
            data["browserId"] = browser_id
        if target_id:
            data["targetId"] = target_id
        resp = await self.client.post(f"{self.base_url}/api/v1/act/click", json=data)
        resp.raise_for_status()
        return resp.json()

    async def type(
        self,
        ref: str,
        text: str,
        browser_id: str | None = None,
        target_id: str | None = None,
        submit: bool = False,
    ) -> dict:
        """输入"""
        data = {"ref": ref, "text": text, "submit": submit}
        if browser_id:
            data["browserId"] = browser_id
        if target_id:
            data["targetId"] = target_id
        resp = await self.client.post(f"{self.base_url}/api/v1/act/type", json=data)
        resp.raise_for_status()
        return resp.json()

    async def screenshot(
        self,
        path: str,
        browser_id: str | None = None,
        target_id: str | None = None,
        full_page: bool = False,
    ) -> dict:
        """截图"""
        data = {"path": path, "fullPage": full_page}
        if browser_id:
            data["browserId"] = browser_id
        if target_id:
            data["targetId"] = target_id
        resp = await self.client.post(f"{self.base_url}/api/v1/screenshot", json=data)
        resp.raise_for_status()
        return resp.json()

    async def fill(
        self, ref: str, text: str, browser_id: str | None = None, target_id: str | None = None
    ) -> dict:
        """填充表单"""
        data = {"ref": ref, "text": text}
        if browser_id:
            data["browserId"] = browser_id
        if target_id:
            data["targetId"] = target_id
        resp = await self.client.post(f"{self.base_url}/api/v1/act/fill", json=data)
        resp.raise_for_status()
        return resp.json()

    async def evaluate(
        self, script: str, browser_id: str | None = None, target_id: str | None = None
    ) -> dict:
        """执行 JavaScript"""
        data = {"script": script}
        if browser_id:
            data["browserId"] = browser_id
        if target_id:
            data["targetId"] = target_id
        resp = await self.client.post(f"{self.base_url}/api/v1/act/evaluate", json=data)
        resp.raise_for_status()
        return resp.json()


async def cmd_status(client: QianjiClient, args):
    """状态命令"""
    result = await client.status()
    if args.format == "json":
        output_result(result, "json")
    else:
        print("Server Status:")
        print(f"  Enabled: {result.get('enabled', False)}")
        print(f"  Running: {result.get('running', False)}")
        print(f"  CDP Ready: {result.get('cdpReady', False)}")
        print(f"  Profile: {result.get('profile', 'default')}")
        print(f"  Browser: {result.get('chosenBrowser', 'unknown')}")
        print(f"  Executable: {result.get('executablePath', 'unknown')}")


async def cmd_start(client: QianjiClient, args):
    """启动浏览器命令"""
    # 自动检测 root 用户，默认启用 no-sandbox
    no_sandbox = args.no_sandbox
    if is_root_user() and not args.sandbox:
        no_sandbox = True
        if args.format == "text":
            print("ℹ️ 检测到 root 用户，自动启用 --no-sandbox（可使用 --sandbox 强制禁用）")

    # 构建额外参数列表
    extra_args = []
    if args.window_size:
        extra_args.append(f"--window-size={args.window_size}")
    if args.user_agent:
        extra_args.append(f"--user-agent={args.user_agent}")
    if args.proxy:
        extra_args.append(f"--proxy-server={args.proxy}")
    if args.disable_dev_shm:
        extra_args.append("--disable-dev-shm-usage")
    if args.disable_gpu:
        extra_args.append("--disable-gpu")
    if args.disable_extensions:
        extra_args.append("--disable-extensions")

    result = await client.start(
        profile=args.profile,
        headless=args.headless,
        no_sandbox=no_sandbox,
        args=extra_args if extra_args else None,
    )

    if args.format == "json":
        output_result(result, "json")
    else:
        browser_id = result.get("browserId", "unknown")
        status = result.get("status", "unknown")
        print(f"✓ Browser {browser_id} is {status}")
        print(f"  Profile: {result.get('profile', 'default')}")
        if status == "starting":
            print("  ⏳ 浏览器正在后台启动，请稍等几秒后使用 'qianji browsers' 查看状态")


async def cmd_stop(client: QianjiClient, args):
    """停止浏览器命令"""
    result = await client.stop(args.browser)
    if args.format == "json":
        output_result(result, "json")
    else:
        print("✓ Browser stopped")
        output_result(result.get("data", {}), "text", "  ")


async def cmd_browsers(client: QianjiClient, args):
    """列出所有浏览器命令"""
    result = await client.list_browsers()
    data = result.get("data", {})

    if args.format == "json":
        output_result(result, "json")
    else:
        print(f"Browsers: {data.get('totalBrowsers', 0)}")
        print(f"Active: {data.get('runningBrowsers', 0)}")
        print(f"Total Tabs: {data.get('totalTabs', 0)}")
        for info in data.get("browsers", []):
            bid = info.get("browserId", "unknown")
            print(f"\n  {bid}:")
            print(f"    Profile: {info.get('profileName', 'default')}")
            print(f"    Running: {info.get('running', False)}")
            print(f"    Tabs: {info.get('tabs', 0)}")
            print(f"    User Data: {info.get('userDataDir', 'N/A')}")


async def cmd_new_browser(client: QianjiClient, args):
    """创建新浏览器命令"""
    # 自动检测 root 用户，默认启用 no-sandbox
    no_sandbox = args.no_sandbox
    if is_root_user() and not args.sandbox:
        no_sandbox = True
        if args.format == "text":
            print("ℹ️ 检测到 root 用户，自动启用 --no-sandbox（可使用 --sandbox 强制禁用）")

    # 构建额外参数列表
    extra_args = []
    if args.window_size:
        extra_args.append(f"--window-size={args.window_size}")
    if args.user_agent:
        extra_args.append(f"--user-agent={args.user_agent}")
    if args.proxy:
        extra_args.append(f"--proxy-server={args.proxy}")
    if args.disable_dev_shm:
        extra_args.append("--disable-dev-shm-usage")
    if args.disable_gpu:
        extra_args.append("--disable-gpu")
    if args.disable_extensions:
        extra_args.append("--disable-extensions")

    result = await client.create_browser(
        profile=args.profile,
        browser_id=args.id,
        headless=args.headless,
        no_sandbox=no_sandbox,
        args=extra_args if extra_args else None,
    )

    if args.format == "json":
        output_result(result, "json")
    else:
        browser_id = result.get("browserId", "unknown")
        status = result.get("status", "unknown")
        print(f"✓ Browser {browser_id} is {status}")
        if status == "starting":
            print("  ⏳ 浏览器正在后台启动，请稍等几秒后使用 'qianji browsers' 查看状态")


async def cmd_close_browser(client: QianjiClient, args):
    """关闭指定浏览器命令"""
    result = await client.close_browser(args.browser_id)
    if args.format == "json":
        output_result(result, "json")
    else:
        print(f"✓ Browser closed: {args.browser_id}")


async def cmd_tabs(client: QianjiClient, args):
    """列出标签页命令"""
    result = await client.list_tabs(args.browser)
    data = result.get("data", {})

    if args.format == "json":
        output_result(result, "json")
    else:
        if args.browser:
            print(f"Tabs for {args.browser}:")
            for tab in data.get("tabs", []):
                print(f"  {tab.get('targetId')}: {tab.get('title', 'N/A')}")
                print(f"    URL: {tab.get('url', 'N/A')}")
        else:
            for browser_id, tabs in data.get("tabs", {}).items():
                print(f"\n{browser_id}:")
                for tab in tabs:
                    print(f"  {tab.get('targetId')}: {tab.get('title', 'N/A')}")


async def cmd_navigate(client: QianjiClient, args):
    """导航命令"""
    result = await client.navigate(args.url, args.browser, args.target)

    if args.format == "json":
        output_result(result, "json")
    else:
        print(f"✓ Navigated to: {result.get('url')}")
        print(f"  Title: {result.get('title')}")


async def cmd_snapshot(client: QianjiClient, args):
    """快照命令"""
    result = await client.snapshot(args.browser, args.target)

    if args.format == "json":
        output_result(result, "json")
    else:
        print(f"✓ Snapshot of: {result.get('url')}")
        print(f"  Title: {result.get('title')}")
        print("\n  Interactive elements:")
        print(result.get("interactive", "None"))


async def cmd_click(client: QianjiClient, args):
    """点击命令"""
    result = await client.click(args.ref, args.browser, args.target)
    if args.format == "json":
        output_result(result, "json")
    else:
        print(f"✓ Clicked: {args.ref}")


async def cmd_type(client: QianjiClient, args):
    """输入命令"""
    result = await client.type(args.ref, args.text, args.browser, args.target, args.submit)
    if args.format == "json":
        output_result(result, "json")
    else:
        print(f"✓ Typed into: {args.ref}")


async def cmd_screenshot(client: QianjiClient, args):
    """截图命令"""
    result = await client.screenshot(args.output, args.browser, args.target, args.full_page)
    if args.format == "json":
        output_result(result, "json")
    else:
        print(f"✓ Screenshot saved: {result.get('path')}")


async def cmd_fill(client: QianjiClient, args):
    """填充命令"""
    result = await client.fill(args.ref, args.text, args.browser, args.target)
    if args.format == "json":
        output_result(result, "json")
    else:
        print(f"✓ Filled: {args.ref}")


async def cmd_evaluate(client: QianjiClient, args):
    """执行 JS 命令"""
    result = await client.evaluate(args.script, args.browser, args.target)
    if args.format == "json":
        output_result(result, "json")
    else:
        print("✓ Result:")
        print(json.dumps(result.get("data", {}).get("result"), indent=2, ensure_ascii=False))


def add_format_argument(parser):
    """为 parser 添加 format 参数"""
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format (default: text)"
    )


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="qianji CLI - Universal Browser Automation (Multi-Browser Support)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  qianji status                    # 查看状态
  qianji browsers                  # 列出所有浏览器
  qianji new-browser --id chrome1  # 创建新浏览器
  qianji start                     # 启动默认浏览器
  qianji navigate https://example.com --browser chrome1
  qianji snapshot                  # 获取页面快照
  qianji click e1 --browser chrome1 --target tab1
  qianji type e2 "hello world" --browser chrome1
  qianji screenshot output.png --browser chrome1

Multi-Browser Options:
  --browser BROWSER_ID             # 指定浏览器实例
  --target TARGET_ID               # 指定标签页
  --format {text,json}             # 输出格式
        """,
    )

    parser.add_argument("--server", default="http://localhost:18796", help="Server URL")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # status
    status_parser = subparsers.add_parser("status", help="Get server status")
    add_format_argument(status_parser)

    # browsers - 列出所有浏览器
    browsers_parser = subparsers.add_parser("browsers", help="List all browser instances")
    add_format_argument(browsers_parser)

    # new-browser - 创建新浏览器
    new_browser_parser = subparsers.add_parser("new-browser", help="Create new browser instance")
    new_browser_parser.add_argument("--profile", help="Profile name")
    new_browser_parser.add_argument("--id", help="Browser ID (optional)")
    new_browser_parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    new_browser_parser.add_argument(
        "--no-sandbox", action="store_true", help="Disable sandbox (for Docker/root)"
    )
    new_browser_parser.add_argument(
        "--sandbox", action="store_true", help="Force enable sandbox (override root auto-detection)"
    )
    new_browser_parser.add_argument("--window-size", help="Window size (e.g., 1920,1080)")
    new_browser_parser.add_argument("--user-agent", help="Custom User-Agent")
    new_browser_parser.add_argument("--proxy", help="Proxy server (e.g., http://proxy:8080)")
    new_browser_parser.add_argument(
        "--disable-dev-shm", action="store_true", help="Disable /dev/shm usage"
    )
    new_browser_parser.add_argument("--disable-gpu", action="store_true", help="Disable GPU")
    new_browser_parser.add_argument(
        "--disable-extensions", action="store_true", help="Disable extensions"
    )
    add_format_argument(new_browser_parser)

    # close-browser - 关闭浏览器
    close_browser_parser = subparsers.add_parser("close-browser", help="Close browser instance")
    close_browser_parser.add_argument("browser_id", help="Browser ID to close")
    add_format_argument(close_browser_parser)

    # start
    start_parser = subparsers.add_parser("start", help="Start default browser")
    start_parser.add_argument("--profile", help="Profile name")
    start_parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    start_parser.add_argument(
        "--no-sandbox", action="store_true", help="Disable sandbox (for Docker/root)"
    )
    start_parser.add_argument(
        "--sandbox", action="store_true", help="Force enable sandbox (override root auto-detection)"
    )
    start_parser.add_argument("--window-size", help="Window size (e.g., 1920,1080)")
    start_parser.add_argument("--user-agent", help="Custom User-Agent")
    start_parser.add_argument("--proxy", help="Proxy server (e.g., http://proxy:8080)")
    start_parser.add_argument(
        "--disable-dev-shm", action="store_true", help="Disable /dev/shm usage"
    )
    start_parser.add_argument("--disable-gpu", action="store_true", help="Disable GPU")
    start_parser.add_argument(
        "--disable-extensions", action="store_true", help="Disable extensions"
    )
    add_format_argument(start_parser)

    # stop
    stop_parser = subparsers.add_parser("stop", help="Stop browser")
    stop_parser.add_argument("--browser", help="Browser ID to stop")
    add_format_argument(stop_parser)

    # tabs
    tabs_parser = subparsers.add_parser("tabs", help="List all tabs")
    tabs_parser.add_argument("--browser", help="Browser ID")
    add_format_argument(tabs_parser)

    # navigate
    nav_parser = subparsers.add_parser("navigate", help="Navigate to URL")
    nav_parser.add_argument("url", help="URL to navigate")
    nav_parser.add_argument("--browser", help="Browser ID")
    nav_parser.add_argument("--target", help="Target tab ID")
    add_format_argument(nav_parser)

    # snapshot
    snap_parser = subparsers.add_parser("snapshot", help="Get page snapshot")
    snap_parser.add_argument("--browser", help="Browser ID")
    snap_parser.add_argument("--target", help="Target tab ID")
    add_format_argument(snap_parser)

    # click
    click_parser = subparsers.add_parser("click", help="Click element")
    click_parser.add_argument("ref", help="Element ref (e.g., e1)")
    click_parser.add_argument("--browser", help="Browser ID")
    click_parser.add_argument("--target", help="Target tab ID")
    add_format_argument(click_parser)

    # type
    type_parser = subparsers.add_parser("type", help="Type text")
    type_parser.add_argument("ref", help="Element ref (e.g., e1)")
    type_parser.add_argument("text", help="Text to type")
    type_parser.add_argument("--browser", help="Browser ID")
    type_parser.add_argument("--target", help="Target tab ID")
    type_parser.add_argument("--submit", action="store_true", help="Submit after typing")
    add_format_argument(type_parser)

    # fill
    fill_parser = subparsers.add_parser("fill", help="Fill form field")
    fill_parser.add_argument("ref", help="Element ref (e.g., e1)")
    fill_parser.add_argument("text", help="Text to fill")
    fill_parser.add_argument("--browser", help="Browser ID")
    fill_parser.add_argument("--target", help="Target tab ID")
    add_format_argument(fill_parser)

    # screenshot
    screenshot_parser = subparsers.add_parser("screenshot", help="Take screenshot")
    screenshot_parser.add_argument("output", help="Output file path")
    screenshot_parser.add_argument("--browser", help="Browser ID")
    screenshot_parser.add_argument("--target", help="Target tab ID")
    screenshot_parser.add_argument("--full-page", action="store_true", help="Capture full page")
    add_format_argument(screenshot_parser)

    # evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Execute JavaScript")
    eval_parser.add_argument("script", help="JavaScript code")
    eval_parser.add_argument("--browser", help="Browser ID")
    eval_parser.add_argument("--target", help="Target tab ID")
    add_format_argument(eval_parser)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 对于需要服务器的命令，自动检测并启动服务器
    server_required_commands = [
        "start",
        "new-browser",
        "stop",
        "tabs",
        "navigate",
        "snapshot",
        "click",
        "type",
        "fill",
        "screenshot",
        "evaluate",
        "browsers",
        "close-browser",
    ]

    if args.command in server_required_commands:
        if not await ensure_server(args.server):
            print(f"✗ 无法连接到服务器: {args.server}")
            print(
                f"  请手动启动服务器: python -m qianji.server --port {args.server.split(':')[-1]}"
            )
            sys.exit(1)

    client = QianjiClient(args.server)

    try:
        commands = {
            "status": cmd_status,
            "browsers": cmd_browsers,
            "new-browser": cmd_new_browser,
            "close-browser": cmd_close_browser,
            "start": cmd_start,
            "stop": cmd_stop,
            "tabs": cmd_tabs,
            "navigate": cmd_navigate,
            "snapshot": cmd_snapshot,
            "click": cmd_click,
            "type": cmd_type,
            "fill": cmd_fill,
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
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())


def sync_main():
    """同步入口函数 - 用于命令行调用"""
    asyncio.run(main())
