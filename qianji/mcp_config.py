"""
智能 MCP 配置生成器
自动检测项目路径，生成可直接使用的 MCP 配置
支持防止重复启动检查
"""

import json
import os
import platform
import socket
import sys
from pathlib import Path
from typing import Any


def find_project_root() -> Path:
    """自动查找项目根目录"""
    # 从当前文件开始向上查找
    current = Path(__file__).resolve()

    # 向上查找包含 pyproject.toml 或 setup.py 的目录
    for parent in [current.parent] + list(current.parents):
        if (parent / "pyproject.toml").exists() or (parent / "setup.py").exists():
            return parent

    # 如果没找到，返回当前文件的父目录
    return current.parent.parent


def find_python_executable() -> str:
    """查找 Python 解释器路径"""
    # 优先使用当前虚拟环境的 Python
    if hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        # 在虚拟环境中
        return sys.executable

    # 尝试查找项目中的虚拟环境
    project_root = find_project_root()

    venv_paths = [
        project_root / ".venv" / "bin" / "python",
        project_root / ".venv" / "Scripts" / "python.exe",
        project_root / "venv" / "bin" / "python",
        project_root / "venv" / "Scripts" / "python.exe",
        project_root / "env" / "bin" / "python",
        project_root / "env" / "Scripts" / "python.exe",
    ]

    for venv_python in venv_paths:
        if venv_python.exists():
            return str(venv_python)

    # 回退到系统 Python
    return sys.executable


def find_free_port(start_port: int = 18796, max_port: int = 18850) -> int:
    """查找可用端口"""
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("localhost", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No free port found between {start_port} and {max_port}")


def is_server_running(port: int) -> bool:
    """检查服务器是否已在运行"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(("localhost", port))
            return result == 0
    except:
        return False


def get_running_server_port(start_port: int = 18796, max_port: int = 18850) -> int | None:
    """查找正在运行的服务器端口"""
    for port in range(start_port, max_port):
        if is_server_running(port):
            # 验证是否是 qianji 服务器
            try:
                import urllib.request

                with urllib.request.urlopen(
                    f"http://localhost:{port}/health", timeout=2
                ) as response:
                    data = json.loads(response.read())
                    if data.get("status") == "ok":
                        return port
            except:
                continue
    return None


def generate_mcp_config(
    server_port: int | None = None,
    auto_start: bool = True,
    custom_env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    生成 MCP 配置

    Args:
        server_port: 指定服务器端口，None 则自动查找
        auto_start: 是否自动启动服务器
        custom_env: 自定义环境变量

    Returns:
        MCP 配置字典
    """
    project_root = find_project_root()
    python_path = "nohup " + find_python_executable()

    # 确定服务器端口
    if server_port is None:
        # 先检查是否有正在运行的服务器
        running_port = get_running_server_port()
        if running_port:
            server_port = running_port
            auto_start = False  # 服务器已在运行，不需要自动启动
        else:
            server_port = find_free_port()

    # 构建环境变量
    env = {
        "PYTHONPATH": str(project_root),
        "QIANJI_CONTROL_PORT": str(server_port),
    }

    # 添加自定义环境变量
    if custom_env:
        env.update(custom_env)

    # 根据是否自动启动构建配置
    if auto_start:
        # 自动启动服务器模式
        # 使用一个包装脚本来启动服务器和 MCP
        wrapper_script = project_root / "qianji" / "mcp_wrapper.py"

        config = {
            "mcpServers": {
                "qianji": {
                    "command": python_path,
                    "args": [str(wrapper_script), "--port", str(server_port), "--mcp"],
                    "env": env,
                }
            }
        }
    else:
        # 仅 MCP 模式（连接到已有服务器）
        mcp_script = project_root / "qianji" / "mcp.py"

        config = {
            "mcpServers": {
                "qianji": {
                    "command": python_path,
                    "args": [str(mcp_script), "--server-url", f"http://localhost:{server_port}"],
                    "env": env,
                }
            }
        }

    return config


def print_config_json(config: dict[str, Any]):
    """打印格式化的 JSON 配置"""
    print("\n" + "=" * 70)
    print("Generated MCP Configuration")
    print("=" * 70)
    print("\n复制以下配置到你的 MCP 配置文件:\n")
    print(json.dumps(config, indent=2, ensure_ascii=False))
    print("\n" + "=" * 70)


def print_config_locations():
    """打印配置文件位置"""
    system = platform.system()

    print("\n配置文件位置:")
    print("-" * 50)

    if system == "Darwin":  # macOS
        print("Claude Desktop: ~/Library/Application Support/Claude/claude_desktop_config.json")
        print("Cursor: ~/Library/Application Support/Cursor/mcp.json")
    elif system == "Windows":
        print("Claude Desktop: %APPDATA%/Claude/claude_desktop_config.json")
        print("Cursor: %APPDATA%/Cursor/mcp.json")
    else:  # Linux
        print("Claude Desktop: ~/.config/Claude/claude_desktop_config.json")
        print("Cursor: ~/.config/Cursor/mcp.json")
        print(
            "Cline: ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
        )

    print("-" * 50)


def write_config_to_file(config: dict[str, Any], filepath: Path):
    """写入配置文件"""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # 如果文件存在，合并配置
    if filepath.exists():
        try:
            with open(filepath) as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            existing = {}

        if "mcpServers" not in existing:
            existing["mcpServers"] = {}

        existing["mcpServers"]["qianji"] = config["mcpServers"]["qianji"]

        with open(filepath, "w") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
    else:
        with open(filepath, "w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Configuration written to: {filepath}")


def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate MCP configuration for qianji",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 生成配置（自动检测）
  python -m qianji.mcp_config

  # 指定端口
  python -m qianji.mcp_config --port 18797

  # 不自动启动服务器（连接到已有服务器）
  python -m qianji.mcp_config --no-auto-start

  # 写入 Claude Desktop 配置
  python -m qianji.mcp_config --write --target claude

  # 添加自定义环境变量
  python -m qianji.mcp_config --env KEY=value --env ANOTHER=val
        """,
    )

    parser.add_argument("--port", type=int, default=None, help="Server port (default: auto-detect)")
    parser.add_argument(
        "--no-auto-start",
        action="store_true",
        help="Don't auto-start server, connect to existing one",
    )
    parser.add_argument("--write", action="store_true", help="Write configuration to file")
    parser.add_argument(
        "--target",
        choices=["claude", "cursor", "cline"],
        default="claude",
        help="Target application for --write (default: claude)",
    )
    parser.add_argument(
        "--env", action="append", default=[], help="Additional environment variables (KEY=value)"
    )
    parser.add_argument(
        "--output", type=Path, default=None, help="Output file path (default: print to stdout)"
    )

    args = parser.parse_args()

    # 解析环境变量
    custom_env = {}
    for env_var in args.env:
        if "=" in env_var:
            key, value = env_var.split("=", 1)
            custom_env[key] = value

    # 检查是否有正在运行的服务器
    running_port = get_running_server_port()
    if running_port and not args.port:
        print(f"✓ Found running qianji server on port {running_port}")
        print("  Will connect to existing server\n")
        server_port = running_port
        auto_start = False
    else:
        server_port = args.port
        auto_start = not args.no_auto_start

    # 生成配置
    config = generate_mcp_config(
        server_port=server_port,
        auto_start=auto_start,
        custom_env=custom_env if custom_env else None,
    )

    # 输出配置
    if args.write:
        system = platform.system()
        if args.target == "claude":
            if system == "Darwin":
                config_path = (
                    Path.home()
                    / "Library"
                    / "Application Support"
                    / "Claude"
                    / "claude_desktop_config.json"
                )
            elif system == "Windows":
                config_path = (
                    Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
                )
            else:
                config_path = Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
        elif args.target == "cursor":
            if system == "Darwin":
                config_path = (
                    Path.home() / "Library" / "Application Support" / "Cursor" / "mcp.json"
                )
            elif system == "Windows":
                config_path = Path(os.environ.get("APPDATA", "")) / "Cursor" / "mcp.json"
            else:
                config_path = Path.home() / ".config" / "Cursor" / "mcp.json"
        else:  # cline
            config_path = (
                Path.home()
                / ".config"
                / "Code"
                / "User"
                / "globalStorage"
                / "saoudrizwan.claude-dev"
                / "settings"
                / "cline_mcp_settings.json"
            )

        write_config_to_file(config, config_path)
    elif args.output:
        write_config_to_file(config, args.output)
    else:
        print_config_json(config)
        print_config_locations()

    # 打印使用说明
    print("\n使用说明:")
    print("-" * 50)
    if auto_start:
        print("1. 将此配置添加到 MCP 客户端")
        print("2. 启动 MCP 客户端时会自动启动 qianji 服务器")
        print("3. 服务器将在后台运行，多个 MCP 连接共享同一实例")
    else:
        print("1. 确保 qianji 服务器已在运行")
        print(f"   qianji-server --port {server_port}")
        print("2. 将此配置添加到 MCP 客户端")
        print("3. MCP 客户端将连接到现有服务器")
    print("-" * 50)


if __name__ == "__main__":
    main()
