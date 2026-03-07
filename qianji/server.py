"""
HTTP 服务器 - 对应 OpenClaw browser/server.js
"""

import asyncio
import signal
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .models.config import BrowserConfig
from .core.browser_manager import BrowserManager
from .routes import create_api_router
from .routes.basic import set_browser_manager


class BrowserServer:
    """浏览器控制服务器"""
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig.from_env()
        self.browser_manager = BrowserManager(self.config)
        self.app: Optional[FastAPI] = None
        self.server: Optional[uvicorn.Server] = None
    
    def create_app(self) -> FastAPI:
        """创建 FastAPI 应用"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """应用生命周期管理"""
            # 启动时初始化
            set_browser_manager(self.browser_manager, self.config)
            
            # 如果配置了自动启动，则启动浏览器
            if self.config.enabled and not self.config.attach_only:
                try:
                    await self.browser_manager.start()
                    print(f"✓ Browser auto-started on profile: {self.config.default_profile}")
                except Exception as e:
                    print(f"⚠ Failed to auto-start browser: {e}")
            
            yield
            
            # 关闭时清理
            if self.browser_manager.is_running:
                await self.browser_manager.stop()
                print("✓ Browser stopped")
        
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
            return {
                "status": "ok",
                "version": "2.0.0",
                "browser_running": self.browser_manager.is_running,
            }
        
        # 注册 API 路由
        api_router = create_api_router()
        app.include_router(api_router)
        
        self.app = app
        return app
    
    async def start(self, host: str = "0.0.0.0", port: Optional[int] = None):
        """启动服务器"""
        port = port or self.config.control_port
        
        if self.app is None:
            self.create_app()
        
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info",
        )
        
        self.server = uvicorn.Server(config)
        
        # 设置信号处理
        for sig in (signal.SIGTERM, signal.SIGINT):
            asyncio.get_event_loop().add_signal_handler(sig, self._signal_handler)
        
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
    
    args = parser.parse_args()
    
    # 从环境变量或参数加载配置
    config = BrowserConfig.from_env()
    
    if args.headless:
        config.headless = True
    if args.no_sandbox:
        config.no_sandbox = True
    if args.browser_path:
        config.executable_path = args.browser_path
    
    # 创建并启动服务器
    server = BrowserServer(config)
    
    try:
        asyncio.run(server.start(host=args.host, port=args.port))
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
