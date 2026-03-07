"""
基础路由 - 对应 OpenClaw browser/routes/basic.js
提供状态查询、启动、停止等功能
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from ..models.config import BrowserConfig
from ..models.responses import StatusResponse, GenericResponse
from ..core.browser_manager import BrowserManager

router = APIRouter()

# 全局浏览器管理器实例
_browser_manager: Optional[BrowserManager] = None
_config: Optional[BrowserConfig] = None


def set_browser_manager(manager: BrowserManager, config: BrowserConfig):
    """设置浏览器管理器"""
    global _browser_manager, _config
    _browser_manager = manager
    _config = config


def get_browser_manager() -> BrowserManager:
    """获取浏览器管理器"""
    if _browser_manager is None:
        raise HTTPException(status_code=503, detail="Browser manager not initialized")
    return _browser_manager


def get_config() -> BrowserConfig:
    """获取配置"""
    if _config is None:
        raise HTTPException(status_code=503, detail="Config not initialized")
    return _config


@router.get("/", response_model=StatusResponse)
async def get_status():
    """获取浏览器状态"""
    manager = get_browser_manager()
    config = get_config()
    
    status = manager.get_status()
    profile = manager._profile
    
    # 检测浏览器
    detected_browser = None
    detected_path = None
    detect_error = None
    
    try:
        import shutil
        for browser in ["chromium", "chrome", "google-chrome", "msedge"]:
            path = shutil.which(browser)
            if path:
                detected_browser = browser
                detected_path = path
                break
    except Exception as e:
        detect_error = str(e)
    
    return StatusResponse(
        enabled=config.enabled,
        profile=profile.name if profile else config.default_profile,
        running=status["running"],
        cdpReady=status["running"],
        cdpHttp=status["running"],
        pid=None,  # Playwright 不直接暴露 PID
        cdpPort=None,
        cdpUrl=None,
        chosenBrowser="chromium",
        detectedBrowser=detected_browser,
        detectedExecutablePath=detected_path,
        detectError=detect_error,
        userDataDir=manager._user_data_dir,
        color=profile.color if profile else config.color,
        headless=profile.headless if profile else config.headless,
        noSandbox=profile.no_sandbox if profile else config.no_sandbox,
        executablePath=profile.executable_path if profile else config.executable_path,
        attachOnly=config.attach_only,
    )


@router.post("/start", response_model=GenericResponse)
async def start_browser(profile: Optional[str] = None):
    """启动浏览器"""
    manager = get_browser_manager()
    
    try:
        await manager.start(profile)
        return GenericResponse(
            ok=True,
            success=True,
            data={"profile": profile or manager.config.default_profile}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop", response_model=GenericResponse)
async def stop_browser():
    """停止浏览器"""
    manager = get_browser_manager()
    
    try:
        stopped = await manager.stop()
        return GenericResponse(
            ok=True,
            success=True,
            data={"stopped": stopped}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset", response_model=GenericResponse)
async def reset_browser():
    """重置浏览器"""
    manager = get_browser_manager()
    
    try:
        await manager.reset()
        return GenericResponse(
            ok=True,
            success=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
