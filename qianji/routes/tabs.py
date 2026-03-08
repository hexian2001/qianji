"""
标签页路由 - 对应 OpenClaw browser/routes/tabs.js
支持多浏览器架构
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models.responses import GenericResponse, TabInfo
from .basic import ensure_browser_manager, get_browser_registry

router = APIRouter()


class OpenTabRequest(BaseModel):
    url: str | None = "about:blank"
    browserId: str | None = None


class CloseTabRequest(BaseModel):
    targetId: str
    browserId: str | None = None


class FocusTabRequest(BaseModel):
    targetId: str
    browserId: str | None = None


@router.get("", response_model=GenericResponse)
async def list_tabs(browserId: str | None = None):
    """列出所有标签页"""
    if browserId:
        # 列出指定浏览器的标签页
        registry = get_browser_registry()
        manager = await registry.get_browser(browserId)
        if not manager:
            raise HTTPException(status_code=404, detail=f"Browser not found: {browserId}")
        tabs = manager.tab_manager.list_tabs()
        return GenericResponse(
            ok=True,
            success=True,
            data={"browserId": browserId, "tabs": [TabInfo(**tab) for tab in tabs]},
        )
    else:
        # 列出所有浏览器的标签页
        registry = get_browser_registry()
        all_tabs = {}
        for bid, instance in registry._browsers.items():
            if instance.manager.is_running:
                tabs = instance.manager.tab_manager.list_tabs()
                all_tabs[bid] = [TabInfo(**tab) for tab in tabs]
        return GenericResponse(ok=True, success=True, data={"tabs": all_tabs})


@router.post("/open", response_model=GenericResponse)
async def open_tab(request: OpenTabRequest):
    """打开新标签页 - 如果浏览器未运行会自动启动"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)

    try:
        page = await manager.context.new_page()

        if request.url and request.url != "about:blank":
            await page.goto(request.url)

        tab = await manager.tab_manager.create_tab(page)

        return GenericResponse(
            ok=True,
            success=True,
            targetId=tab.target_id,
            url=tab.url,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/close", response_model=GenericResponse)
async def close_tab(request: CloseTabRequest):
    """关闭标签页"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)

    try:
        closed = await manager.tab_manager.close_tab(request.targetId)

        if not closed:
            raise HTTPException(status_code=404, detail=f"Tab not found: {request.targetId}")

        return GenericResponse(ok=True, success=True, data={"closed": True})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/focus", response_model=GenericResponse)
async def focus_tab(request: FocusTabRequest):
    """聚焦标签页"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)

    try:
        focused = await manager.tab_manager.focus_tab(request.targetId)

        if not focused:
            raise HTTPException(status_code=404, detail=f"Tab not found: {request.targetId}")

        tab = manager.tab_manager.get_tab(request.targetId)

        return GenericResponse(
            ok=True,
            success=True,
            targetId=tab.target_id,
            url=tab.url,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
