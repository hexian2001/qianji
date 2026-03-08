"""
基础路由 - 对应 OpenClaw browser/routes/basic.js
提供状态查询、浏览器管理等功能
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ..core.browser_manager import BrowserManager
from ..core.browser_registry import BrowserRegistry
from ..models.config import BrowserConfig
from ..models.responses import GenericResponse, StatusResponse

router = APIRouter()

# 全局浏览器注册表实例
_browser_registry: BrowserRegistry | None = None
_config: BrowserConfig | None = None


def set_browser_registry(registry: BrowserRegistry, config: BrowserConfig):
    """设置浏览器注册表"""
    global _browser_registry, _config
    _browser_registry = registry
    _config = config


def get_browser_registry() -> BrowserRegistry:
    """获取浏览器注册表"""
    if _browser_registry is None:
        raise HTTPException(status_code=503, detail="Browser registry not initialized")
    return _browser_registry


def get_config() -> BrowserConfig:
    """获取配置"""
    if _config is None:
        raise HTTPException(status_code=503, detail="Config not initialized")
    return _config


async def ensure_browser_manager(
    browser_id: str | None = None, profile_name: str | None = None
) -> tuple[str, BrowserManager]:
    """确保浏览器管理器存在并运行"""
    registry = get_browser_registry()
    return await registry.ensure_browser(browser_id, profile_name)


@router.get("/", response_model=StatusResponse)
async def get_status():
    """获取浏览器状态"""
    registry = get_browser_registry()
    config = get_config()

    stats = registry.get_stats()

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

    # 获取第一个运行的浏览器作为默认状态
    default_profile = None
    headless = config.headless
    no_sandbox = config.no_sandbox

    for browser_info in stats["browsers"]:
        if browser_info["running"]:
            default_profile = browser_info["profileName"]
            break

    return StatusResponse(
        enabled=config.enabled,
        profile=default_profile or config.default_profile,
        running=stats["runningBrowsers"] > 0,
        cdpReady=stats["runningBrowsers"] > 0,
        cdpHttp=stats["runningBrowsers"] > 0,
        pid=None,
        cdpPort=None,
        cdpUrl=None,
        chosenBrowser="chromium",
        detectedBrowser=detected_browser,
        detectedExecutablePath=detected_path,
        detectError=detect_error,
        userDataDir=None,
        color=config.color,
        headless=headless,
        noSandbox=no_sandbox,
        executablePath=config.executable_path,
        attachOnly=config.attach_only,
    )


@router.get("/browsers", response_model=GenericResponse)
async def list_browsers():
    """列出所有浏览器实例"""
    registry = get_browser_registry()

    return GenericResponse(
        ok=True,
        success=True,
        data=registry.get_stats(),
    )


@router.post("/browsers/create", response_model=GenericResponse)
async def create_browser(
    profile: str | None = None,
    browser_id: str | None = None,
    idle_timeout: float | None = None,
    max_lifetime: float | None = None,
    headless: bool | None = None,
    no_sandbox: bool | None = None,
    args: list[str] | None = None,
):
    """创建新浏览器实例

    Args:
        profile: 浏览器配置文件名称
        browser_id: 指定的浏览器ID（可选）
        idle_timeout: 空闲超时时间（秒），默认使用服务器配置
        max_lifetime: 最大生命周期（秒），默认使用服务器配置
        headless: 是否使用无头模式，默认使用服务器配置
        no_sandbox: 是否禁用沙箱，默认使用服务器配置
        args: 额外的浏览器启动参数
    """
    registry = get_browser_registry()

    # 如果没有指定 browser_id，生成一个
    if not browser_id:
        browser_id = f"browser_{len(registry._browsers) + 1}"

    # 在后台启动浏览器，避免HTTP超时
    async def create_browser_async():
        try:
            await registry.create_browser(
                profile_name=profile,
                browser_id=browser_id,
                idle_timeout=idle_timeout,
                max_lifetime=max_lifetime,
                headless=headless,
                no_sandbox=no_sandbox,
                args=args,
            )
        except Exception as e:
            print(f"[ERROR] Failed to create browser {browser_id}: {e}")

    # 启动后台任务
    import asyncio

    asyncio.create_task(create_browser_async())

    return GenericResponse(
        ok=True,
        success=True,
        data={
            "browserId": browser_id,
            "profile": profile,
            "status": "starting",
            "lifecycle": {
                "idleTimeout": idle_timeout,
                "maxLifetime": max_lifetime,
            },
        },
    )


@router.post("/browsers/{browser_id}/close", response_model=GenericResponse)
async def close_browser(browser_id: str):
    """关闭指定浏览器实例"""
    registry = get_browser_registry()

    success = await registry.close_browser(browser_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Browser not found: {browser_id}")

    return GenericResponse(
        ok=True,
        success=True,
        data={"browserId": browser_id, "closed": True},
    )


@router.post("/start", response_model=GenericResponse)
async def start_browser(
    profile: str | None = None,
    headless: bool | None = None,
    no_sandbox: bool | None = None,
    args: list[str] | None = None,
    background_tasks: BackgroundTasks = None,
):
    """启动浏览器（兼容旧版API，创建新浏览器实例）

    Args:
        profile: 浏览器配置文件名称
        headless: 是否使用无头模式，默认使用服务器配置
        no_sandbox: 是否禁用沙箱，默认使用服务器配置
        args: 额外的浏览器启动参数
    """
    registry = get_browser_registry()

    # 生成浏览器ID
    browser_id = f"browser_{len(registry._browsers) + 1}"

    # 在后台启动浏览器，避免HTTP超时
    async def start_browser_async():
        try:
            await registry.create_browser(
                profile_name=profile,
                browser_id=browser_id,
                headless=headless,
                no_sandbox=no_sandbox,
                args=args,
            )
        except Exception as e:
            print(f"[ERROR] Failed to start browser {browser_id}: {e}")

    # 启动后台任务
    import asyncio

    asyncio.create_task(start_browser_async())

    return GenericResponse(
        ok=True,
        success=True,
        data={"browserId": browser_id, "profile": profile or "default", "status": "starting"},
    )


@router.post("/stop", response_model=GenericResponse)
async def stop_browser():
    """停止所有浏览器（兼容旧版API）"""
    registry = get_browser_registry()

    try:
        await registry.close_all()
        return GenericResponse(
            ok=True,
            success=True,
            data={"stopped": True},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset", response_model=GenericResponse)
async def reset_browser():
    """重置所有浏览器"""
    registry = get_browser_registry()

    try:
        # 获取所有运行的浏览器
        browsers_to_restart = []
        for bid, instance in list(registry._browsers.items()):
            if instance.manager.is_running:
                browsers_to_restart.append((bid, instance.profile_name))
                await instance.manager.stop()

        # 重新启动
        restarted = []
        for bid, profile_name in browsers_to_restart:
            new_bid = await registry.create_browser(profile_name, bid)
            restarted.append(new_bid)

        return GenericResponse(
            ok=True,
            success=True,
            data={"restarted": restarted},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
