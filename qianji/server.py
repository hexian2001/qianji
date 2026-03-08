"""
HTTP 服务器 - 对应 OpenClaw browser/server.js
"""

import asyncio
import os
import signal
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.browser_registry import BrowserRegistry
from .models.config import BrowserConfig
from .routes.basic import set_browser_registry


class BrowserServer:
    """浏览器控制服务器 - 支持多浏览器实例

    生命周期管理：
    - idle_timeout: 空闲超时时间（秒），默认 3600 秒（1小时）
    - max_lifetime: 最大生命周期（秒），默认 3600 秒（1小时）
    """

    DEFAULT_LIFETIME = 3600  # 默认 1 小时

    def __init__(
        self,
        config: BrowserConfig | None = None,
        idle_timeout: float | None = None,
        max_lifetime: float | None = None,
        cleanup_interval: float = 60.0,
    ):
        self.config = config or BrowserConfig.from_env()

        # 从环境变量读取生命周期配置（优先级：参数 > 环境变量 > 默认值）
        env_idle_timeout = os.environ.get("QIANJI_IDLE_TIMEOUT")
        env_max_lifetime = os.environ.get("QIANJI_MAX_LIFETIME")

        final_idle_timeout = idle_timeout
        if final_idle_timeout is None and env_idle_timeout is not None:
            final_idle_timeout = float(env_idle_timeout)
        if final_idle_timeout is None:
            final_idle_timeout = self.DEFAULT_LIFETIME

        final_max_lifetime = max_lifetime
        if final_max_lifetime is None and env_max_lifetime is not None:
            final_max_lifetime = float(env_max_lifetime)
        if final_max_lifetime is None:
            final_max_lifetime = self.DEFAULT_LIFETIME

        self.browser_registry = BrowserRegistry(
            self.config,
            idle_timeout=final_idle_timeout,
            max_lifetime=final_max_lifetime,
            cleanup_interval=cleanup_interval,
        )
        self.app: FastAPI | None = None
        self.server: uvicorn.Server | None = None

    def create_app(self) -> FastAPI:
        """创建 FastAPI 应用"""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """应用生命周期管理"""
            # 启动时初始化
            set_browser_registry(self.browser_registry, self.config)

            # 启动后台清理任务（如果配置了生命周期管理）
            if self.browser_registry.idle_timeout or self.browser_registry.max_lifetime:
                await self.browser_registry.start_cleanup_task()
                print(
                    f"✓ Browser lifecycle manager started (idle_timeout={self.browser_registry.idle_timeout}s, max_lifetime={self.browser_registry.max_lifetime}s)"
                )

            # 如果配置了自动启动，则启动默认浏览器
            if self.config.enabled and not self.config.attach_only:
                try:
                    browser_id = await self.browser_registry.create_browser(
                        self.config.default_profile
                    )
                    print(
                        f"✓ Browser auto-started: {browser_id} (profile: {self.config.default_profile})"
                    )
                except Exception as e:
                    print(f"⚠ Failed to auto-start browser: {e}")

            yield

            # 关闭时清理
            await self.browser_registry.stop_cleanup_task()
            await self.browser_registry.close_all()
            print("✓ All browsers stopped")

        app = FastAPI(
            title="qianji",
            description="Universal Browser Automation for AI - 100% OpenClaw Compatible",
            version="2.0.0",
            lifespan=lifespan,
        )

        # CORS 中间件
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 健康检查
        @app.get("/health")
        async def health_check():
            stats = self.browser_registry.get_stats()
            return {
                "status": "ok",
                "version": "2.0.0",
                "browsers": stats,
            }

        # 注册基础路由 (不带 /api/v1 前缀)
        from .routes import basic_router

        app.include_router(basic_router, tags=["basic"])

        # 注册 API 路由 (带 /api/v1 前缀)
        from .routes import (
            agent_act_router,
            agent_debug_router,
            agent_snapshot_router,
            agent_storage_router,
            tabs_router,
        )

        app.include_router(agent_snapshot_router, prefix="/api/v1", tags=["snapshot"])
        app.include_router(agent_act_router, prefix="/api/v1/act", tags=["act"])
        app.include_router(agent_storage_router, prefix="/api/v1/storage", tags=["storage"])
        app.include_router(agent_debug_router, prefix="/api/v1/debug", tags=["debug"])
        app.include_router(tabs_router, prefix="/api/v1/tabs", tags=["tabs"])

        self.app = app
        return app

    async def start(self, host: str = "0.0.0.0", port: int | None = None, log_level: str = "info"):
        """启动服务器"""
        port = port or self.config.control_port

        if self.app is None:
            self.create_app()

        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level=log_level,
            access_log=log_level != "critical",  # 静默模式下禁用访问日志
        )

        self.server = uvicorn.Server(config)

        # 设置信号处理
        for sig in (signal.SIGTERM, signal.SIGINT):
            asyncio.get_event_loop().add_signal_handler(sig, self._signal_handler)

        if log_level != "critical":
            print(f"🚀 qianji server starting on http://{host}:{port}")
        await self.server.serve()

    def _signal_handler(self):
        """信号处理"""
        if self.server:
            self.server.should_exit = True

    async def stop(self):
        """停止服务器"""
        if self.server:
            self.server.should_exit = True
            # 等待服务器停止
            while not self.server.started:
                await asyncio.sleep(0.1)


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="qianji - Universal Browser Automation")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=None, help="Port to bind")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--no-sandbox", action="store_true", help="Disable sandbox")
    parser.add_argument("--browser-path", help="Path to browser executable")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode (minimal output)")
    # 生命周期管理参数（默认 1 小时 = 3600 秒）
    parser.add_argument(
        "--idle-timeout",
        type=float,
        default=None,
        help="Browser idle timeout in seconds (default: 3600 = 1 hour, 0 to disable)",
    )
    parser.add_argument(
        "--max-lifetime",
        type=float,
        default=None,
        help="Browser maximum lifetime in seconds (default: 3600 = 1 hour, 0 to disable)",
    )
    parser.add_argument(
        "--cleanup-interval",
        type=float,
        default=60.0,
        help="Cleanup check interval in seconds (default: 60)",
    )

    args = parser.parse_args()

    # 从环境变量或参数加载配置
    config = BrowserConfig.from_env()

    if args.headless:
        config.headless = True
    if args.no_sandbox:
        config.no_sandbox = True
    if args.browser_path:
        config.executable_path = args.browser_path

    # 静默模式
    log_level = "critical" if args.quiet else "info"

    # 创建并启动服务器（带生命周期管理）
    server = BrowserServer(
        config,
        idle_timeout=args.idle_timeout,
        max_lifetime=args.max_lifetime,
        cleanup_interval=args.cleanup_interval,
    )

    try:
        asyncio.run(server.start(host=args.host, port=args.port, log_level=log_level))
    except KeyboardInterrupt:
        if not args.quiet:
            print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
