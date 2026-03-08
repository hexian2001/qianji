"""
MCP 安装脚本
配置 Claude Desktop 和 Cursor 使用 qianji MCP
"""

import json
import os
import platform
import sys
from pathlib import Path


def get_claude_config_path() -> Path:
    """获取 Claude Desktop 配置路径"""
    system = platform.system()
    if system == "Darwin":  # macOS
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json"
        )
    elif system == "Windows":
        return Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
    else:  # Linux
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def get_cursor_config_path() -> Path:
    """获取 Cursor 配置路径"""
    system = platform.system()
    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Cursor" / "mcp.json"
    elif system == "Windows":
        return Path(os.environ.get("APPDATA", "")) / "Cursor" / "mcp.json"
    else:  # Linux
        return Path.home() / ".config" / "Cursor" / "mcp.json"


def get_mcp_server_config(
    server_url: str = "http://localhost:18796",
    python_path: str | None = None,
    auto_start: bool = True,
    idle_timeout: int | None = None,
    max_lifetime: int | None = None,
) -> dict:
    """生成 MCP 服务器配置

    Args:
        server_url: qianji 服务器 URL
        python_path: Python 解释器路径（默认自动检测）
        auto_start: 是否自动启动服务器（默认 True）
        idle_timeout: 浏览器空闲超时（秒）
        max_lifetime: 浏览器最大生命周期（秒）
    """
    # 获取 Python 解释器路径
    if python_path is None:
        python_path = sys.executable

    project_root = Path(__file__).parent.parent.absolute()
    wrapper_path = project_root / "qianji" / "mcp_wrapper.py"

    # 构建 args
    args = [
        str(wrapper_path),
        "--port",
        server_url.split(":")[-1],
    ]

    # 如果不自动启动，添加 --no-auto-start
    if not auto_start:
        args.append("--no-auto-start")

    args.append("--mcp")

    # 构建 env
    env = {"PYTHONPATH": str(project_root), "QIANJI_CONTROL_PORT": server_url.split(":")[-1]}

    # 添加生命周期配置
    if idle_timeout is not None:
        env["QIANJI_IDLE_TIMEOUT"] = str(idle_timeout)
    if max_lifetime is not None:
        env["QIANJI_MAX_LIFETIME"] = str(max_lifetime)

    return {"command": python_path, "args": args, "env": env}


def setup_claude_mcp(server_url: str = "http://localhost:18796"):
    """配置 Claude Desktop MCP"""
    config_path = get_claude_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # 读取现有配置
    config = {}
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse existing config at {config_path}")
            config = {}

    # 确保 mcpServers 存在
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # 添加 qianji MCP 服务器
    config["mcpServers"]["qianji"] = get_mcp_server_config(server_url)

    # 写入配置
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"✓ Claude Desktop MCP configured at: {config_path}")
    print(f"  Server URL: {server_url}")


def setup_cursor_mcp(server_url: str = "http://localhost:18796"):
    """配置 Cursor MCP"""
    config_path = get_cursor_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # 读取现有配置
    config = {}
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse existing config at {config_path}")
            config = {}

    # 确保 mcpServers 存在
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # 添加 qianji MCP 服务器
    config["mcpServers"]["qianji"] = get_mcp_server_config(server_url)

    # 写入配置
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"✓ Cursor MCP configured at: {config_path}")
    print(f"  Server URL: {server_url}")


def print_manual_config(server_url: str = "http://localhost:18796", python_path: str | None = None):
    """打印手动配置说明"""
    if python_path is None:
        python_path = sys.executable

    print("\n" + "=" * 60)
    print("Manual MCP Configuration")
    print("=" * 60)
    print("\nAdd the following to your MCP configuration:\n")
    project_root = Path(__file__).parent.parent.absolute()
    wrapper_path = project_root / "qianji" / "mcp_wrapper.py"

    config = {
        "mcpServers": {
            "qianji": {
                "command": python_path,
                "args": [str(wrapper_path), "--port", server_url.split(":")[-1], "--mcp"],
                "env": {
                    "PYTHONPATH": str(project_root),
                    "QIANJI_CONTROL_PORT": server_url.split(":")[-1],
                },
            }
        }
    }

    print(json.dumps(config, indent=2))
    print("\n" + "=" * 60)
    print("\nConfiguration Notes:")
    print("  - The wrapper will auto-start the qianji server if not running")
    print("  - Server will be accessible at " + server_url)
    print("  - Environment variables:")
    print("    - QIANJI_IDLE_TIMEOUT: Browser idle timeout (seconds)")
    print("    - QIANJI_MAX_LIFETIME: Browser max lifetime (seconds)")
    print("  - To disable auto-start, add '--no-auto-start' to args")
    print("=" * 60)


def main():
    """MCP 安装脚本入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Setup qianji MCP for Claude Desktop and Cursor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Configure both Claude and Cursor with auto-start
  python -m qianji.mcp_setup

  # Configure with custom Python path
  python -m qianji.mcp_setup --python /root/miniconda3/envs/py312/bin/python

  # Configure without auto-start (manual server management)
  python -m qianji.mcp_setup --no-auto-start

  # Print manual configuration
  python -m qianji.mcp_setup --manual
        """,
    )
    parser.add_argument(
        "--server-url",
        default="http://localhost:18796",
        help="qianji server URL (default: http://localhost:18796)",
    )
    parser.add_argument(
        "--python",
        dest="python_path",
        default=None,
        help="Python interpreter path (default: auto-detect)",
    )
    parser.add_argument("--claude", action="store_true", help="Configure Claude Desktop only")
    parser.add_argument("--cursor", action="store_true", help="Configure Cursor only")
    parser.add_argument("--manual", action="store_true", help="Print manual configuration only")
    parser.add_argument(
        "--no-auto-start",
        action="store_true",
        help="Don't auto-start server (manual server management)",
    )
    parser.add_argument(
        "--idle-timeout",
        type=int,
        default=None,
        help="Browser idle timeout in seconds (default: 3600)",
    )
    parser.add_argument(
        "--max-lifetime",
        type=int,
        default=None,
        help="Browser max lifetime in seconds (default: 3600)",
    )

    args = parser.parse_args()

    if args.manual:
        print_manual_config(args.server_url, args.python_path)
        return

    # 如果没有指定，默认配置所有
    configure_all = not (args.claude or args.cursor)

    print("Setting up qianji MCP...")
    print(f"Server URL: {args.server_url}")
    print(f"Python: {args.python_path or 'auto-detect'}")
    print(f"Auto-start: {not args.no_auto_start}")
    if args.idle_timeout:
        print(f"Idle timeout: {args.idle_timeout}s")
    if args.max_lifetime:
        print(f"Max lifetime: {args.max_lifetime}s")
    print()

    # 更新全局配置函数参数
    global get_mcp_server_config
    original_get_config = get_mcp_server_config

    def get_mcp_server_config_with_args(server_url):
        return original_get_config(
            server_url=server_url,
            python_path=args.python_path,
            auto_start=not args.no_auto_start,
            idle_timeout=args.idle_timeout,
            max_lifetime=args.max_lifetime,
        )

    # 替换函数
    import qianji.mcp_setup

    qianji.mcp_setup.get_mcp_server_config = get_mcp_server_config_with_args

    if configure_all or args.claude:
        try:
            setup_claude_mcp(args.server_url)
        except Exception as e:
            print(f"✗ Failed to configure Claude Desktop: {e}")

    if configure_all or args.cursor:
        try:
            setup_cursor_mcp(args.server_url)
        except Exception as e:
            print(f"✗ Failed to configure Cursor: {e}")

    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    if args.no_auto_start:
        print("1. Start qianji server manually:")
        print(f"   python -m qianji.server --port {args.server_url.split(':')[-1]}")
        print("2. Restart Claude Desktop or Cursor")
    else:
        print("1. Restart Claude Desktop or Cursor")
        print("2. The MCP wrapper will auto-start the server when needed")
    print("3. The browser tools will be available in your AI assistant")
    print("\nAvailable tools:")
    print("  - browser_navigate: Navigate to a URL")
    print("  - browser_navigate_and_snapshot: Navigate and get snapshot")
    print("  - browser_snapshot: Get page snapshot with interactive elements")
    print("  - browser_click: Click an element")
    print("  - browser_fill: Fill a form field")
    print("  - browser_type: Type text")
    print("  - browser_upload_file: Upload file(s)")
    print("  - browser_handle_dialog: Handle dialogs")
    print("  - browser_screenshot: Take a screenshot")
    print("  - browser_evaluate: Execute JavaScript")
    print("  - browser_go_back: Go back")
    print("  - browser_go_forward: Go forward")
    print("  - browser_reload: Reload page")


def sync_main():
    """同步入口"""
    main()


if __name__ == "__main__":
    main()
