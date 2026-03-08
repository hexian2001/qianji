"""
MCP 包装脚本 - 简化版
- 确保全局只有一个 server 在 18796 端口
- 复用已有的 qianji-server 和 qianji-mcp 命令
"""

import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_PORT = 18796


def log(message: str):
    """输出日志到 stderr"""
    print(message, file=sys.stderr, flush=True)


def is_server_running(port: int) -> bool:
    """检查 server 是否正在运行"""
    try:
        import http.client

        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        conn.request("GET", "/health")
        response = conn.getresponse()
        return response.status == 200
    except:
        return False


def wait_for_server(port: int, timeout: float = 60) -> bool:
    """等待 server 启动"""
    start = time.time()
    while time.time() - start < timeout:
        if is_server_running(port):
            return True
        time.sleep(0.1)
    return False


def start_server(port: int, quiet: bool = True) -> subprocess.Popen:
    """启动 qianji-server"""
    env = os.environ.copy()
    env["QIANJI_CONTROL_PORT"] = str(port)

    # 确保 PYTHONPATH 包含项目根目录
    project_root = str(Path(__file__).parent.parent)
    current_pythonpath = env.get("PYTHONPATH", "")
    if project_root not in current_pythonpath:
        env["PYTHONPATH"] = (
            f"{project_root}:{current_pythonpath}" if current_pythonpath else project_root
        )

    # 使用绝对路径的 Python 解释器来运行 server
    python = sys.executable
    cmd = [python, "-m", "qianji.server", "--port", str(port)]
    if quiet:
        cmd.append("--quiet")

    if not quiet:
        log(f"  Command: {' '.join(cmd)}")
        log(f"  PYTHONPATH: {env.get('PYTHONPATH', 'not set')}")

    # 先检查是否已有 server 在运行（避免重复启动）
    if is_server_running(port):
        if not quiet:
            log(f"  Server already running on port {port}")
        return None

    # 启动 server，完全脱离当前进程
    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL if quiet else None,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )

    if not quiet:
        log(f"  Started process with PID: {process.pid}")

    # 等待 server 就绪
    if wait_for_server(port, timeout=60):
        if not quiet:
            log(f"  Server is ready on port {port}")
        return process

    # 启动失败，检查进程状态
    exit_code = process.poll()
    if not quiet:
        log(f"  Process exit code: {exit_code}")

    # 终止进程
    try:
        process.terminate()
        process.wait(timeout=2)
    except:
        process.kill()

    # 再次检查是否已经有其他 server 在运行（可能是其他进程启动的）
    if is_server_running(port):
        if not quiet:
            log(f"  Another server is now running on port {port}")
        return None

    raise RuntimeError(f"Server failed to start on port {port} (exit code: {exit_code})")


def ensure_server(port: int = DEFAULT_PORT, quiet: bool = True) -> bool:
    """确保 server 在运行"""
    if is_server_running(port):
        if not quiet:
            log(f"✓ Server already running on port {port}")
        return True

    if not quiet:
        log(f"Starting server on port {port}...")

    log("DEBUG: About to start server...")  # 调试信息
    process = start_server(port, quiet=quiet)
    log(f"DEBUG: start_server returned: {process}")  # 调试信息

    if process is None:
        log("DEBUG: Server already running or started by another process")
        return True

    if not quiet:
        log(f"✓ Server started (PID: {process.pid})")

    log("DEBUG: ensure_server completed successfully")
    return True


def run_mcp(port: int, quiet: bool = True):
    """运行 MCP server"""
    from qianji.mcp import QianjiMCPServer

    if not quiet:
        log(f"Starting MCP server on port {port}...")

    # 检查 stdin 是否可用
    if sys.stdin.isatty():
        log("WARNING: stdin is a tty, MCP may not work correctly")
        log("MCP expects JSON-RPC messages from stdin")

    mcp_server = QianjiMCPServer(base_url=f"http://127.0.0.1:{port}")
    asyncio.run(mcp_server.run())


def main():
    import argparse

    parser = argparse.ArgumentParser(description="qianji MCP Wrapper")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--mcp", action="store_true", help="Run MCP server")
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()
    quiet = not args.verbose

    try:
        # 确保 server 运行
        ensure_server(args.port, quiet=quiet)

        # 运行 MCP
        if args.mcp:
            run_mcp(args.port, quiet=quiet)

    except Exception as e:
        log(f"✗ Error: {e}")
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
