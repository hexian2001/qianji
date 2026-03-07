"""
标签页路由 - 对应 OpenClaw browser/routes/tabs.js
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models.responses import GenericResponse, TabInfo
from .basic import get_browser_manager

router = APIRouter()


class OpenTabRequest(BaseModel):
    url: Optional[str] = "about:blank"


@router.get("", response_model=List[TabInfo])
async def list_tabs():
    """列出所有标签页"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tabs = manager.tab_manager.list_tabs()
        return [TabInfo(**tab) for tab in tabs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/open", response_model=GenericResponse)
async def open_tab(request: OpenTabRequest):
    """打开新标签页"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
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
async def close_tab(targetId: str):
    """关闭标签页"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        closed = await manager.tab_manager.close_tab(targetId)
        
        if not closed:
            raise HTTPException(status_code=404, detail=f"Tab not found: {targetId}")
        
        return GenericResponse(
            ok=True,
            success=True,
            data={"closed": True}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/focus", response_model=GenericResponse)
async def focus_tab(targetId: str):
    """聚焦标签页"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        focused = await manager.tab_manager.focus_tab(targetId)
        
        if not focused:
            raise HTTPException(status_code=404, detail=f"Tab not found: {targetId}")
        
        tab = manager.tab_manager.get_tab(targetId)
        
        return GenericResponse(
            ok=True,
            success=True,
            targetId=targetId,
            url=tab.url if tab else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
