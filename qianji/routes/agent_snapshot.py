"""
快照路由 - 对应 OpenClaw browser/routes/agent.snapshot.js
提供导航、快照、截图、PDF 等功能
"""

import os
import tempfile
from typing import Optional
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel

from ..models.responses import (
    NavigateResponse, SnapshotResponse, ScreenshotResponse, 
    PDFResponse, GenericResponse, SnapshotElementData
)
from ..models.snapshot import Snapshot
from ..core.browser_manager import BrowserManager
from ..core.pw_client import PlaywrightClient
from .basic import get_browser_manager

router = APIRouter()
pw_client = PlaywrightClient()


class NavigateRequest(BaseModel):
    url: str
    targetId: Optional[str] = None
    timeout: int = 30000


class SnapshotRequest(BaseModel):
    targetId: Optional[str] = None
    refs: str = "role"  # "role" or "aria"
    mode: str = "efficient"  # "efficient" or "full"


class ScreenshotRequest(BaseModel):
    targetId: Optional[str] = None
    fullPage: bool = False
    ref: Optional[str] = None
    element: Optional[str] = None
    type: str = "png"  # "png" or "jpeg"


class PDFRequest(BaseModel):
    targetId: Optional[str] = None


@router.post("/navigate", response_model=NavigateResponse)
async def navigate(request: NavigateRequest):
    """导航到 URL"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        result = await pw_client.navigate(
            tab.page, 
            request.url, 
            timeout=request.timeout
        )
        await tab.update_info()
        
        return NavigateResponse(
            targetId=tab.target_id,
            url=result["url"],
            title=result.get("title"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/snapshot", response_model=SnapshotResponse)
async def create_snapshot(request: SnapshotRequest):
    """创建页面快照"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        snapshot = await pw_client.create_snapshot(tab.page, refs=request.refs)
        await tab.update_info()
        
        # 转换为响应格式
        elements_data = {
            ref: SnapshotElementData(**elem.to_dict())
            for ref, elem in snapshot.elements.items()
        }
        
        return SnapshotResponse(
            targetId=tab.target_id,
            url=snapshot.url,
            title=snapshot.title,
            text=snapshot.text[:5000],
            interactive=snapshot.to_interactive_text(),
            elements=elements_data,
            viewport={"width": snapshot.viewport_width, "height": snapshot.viewport_height},
            scroll={"x": snapshot.scroll_x, "y": snapshot.scroll_y},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/screenshot", response_model=ScreenshotResponse)
async def take_screenshot(request: ScreenshotRequest):
    """截图"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        
        # 生成临时文件路径
        suffix = ".jpg" if request.type == "jpeg" else ".png"
        fd, path = tempfile.mkstemp(suffix=suffix, prefix="qianji_screenshot_")
        os.close(fd)
        
        # 如果有 ref，需要获取快照
        snapshot = None
        if request.ref:
            snapshot = await pw_client.create_snapshot(tab.page)
        
        await pw_client.screenshot(
            tab.page,
            path=path,
            full_page=request.fullPage,
            ref=request.ref,
            snapshot=snapshot
        )
        
        return ScreenshotResponse(
            path=path,
            targetId=tab.target_id,
            url=tab.url,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pdf", response_model=PDFResponse)
async def generate_pdf(request: PDFRequest):
    """生成 PDF"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        
        # 生成临时文件路径
        fd, path = tempfile.mkstemp(suffix=".pdf", prefix="qianji_pdf_")
        os.close(fd)
        
        await pw_client.pdf(tab.page, path=path)
        
        return PDFResponse(
            path=path,
            targetId=tab.target_id,
            url=tab.url,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/go-back", response_model=GenericResponse)
async def go_back(targetId: Optional[str] = None):
    """后退"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(targetId)
        result = await pw_client.go_back(tab.page)
        await tab.update_info()
        
        return GenericResponse(
            ok=True,
            success=True,
            targetId=tab.target_id,
            url=result["url"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/go-forward", response_model=GenericResponse)
async def go_forward(targetId: Optional[str] = None):
    """前进"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(targetId)
        result = await pw_client.go_forward(tab.page)
        await tab.update_info()
        
        return GenericResponse(
            ok=True,
            success=True,
            targetId=tab.target_id,
            url=result["url"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload", response_model=GenericResponse)
async def reload(targetId: Optional[str] = None):
    """刷新"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(targetId)
        result = await pw_client.reload(tab.page)
        await tab.update_info()
        
        return GenericResponse(
            ok=True,
            success=True,
            targetId=tab.target_id,
            url=result["url"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
