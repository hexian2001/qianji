"""
操作路由 - 对应 OpenClaw browser/routes/agent.act.js
提供点击、输入、按键等操作
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel

from ..models.responses import ClickResponse, TypeResponse, GenericResponse
from ..core.pw_client import PlaywrightClient
from .basic import get_browser_manager

router = APIRouter()
pw_client = PlaywrightClient()


class ClickRequest(BaseModel):
    ref: str
    targetId: Optional[str] = None
    doubleClick: bool = False
    button: str = "left"  # "left", "right", "middle"
    modifiers: Optional[List[str]] = None  # "Alt", "Control", "Meta", "Shift"
    timeoutMs: Optional[int] = None


class TypeRequest(BaseModel):
    ref: str
    text: str
    targetId: Optional[str] = None
    submit: bool = False
    slowly: bool = False
    timeoutMs: Optional[int] = None


class PressRequest(BaseModel):
    key: str
    targetId: Optional[str] = None
    delayMs: Optional[int] = None


class FillRequest(BaseModel):
    ref: str
    text: str
    targetId: Optional[str] = None
    timeoutMs: Optional[int] = None


class HoverRequest(BaseModel):
    ref: str
    targetId: Optional[str] = None
    timeoutMs: Optional[int] = None


class SelectRequest(BaseModel):
    ref: str
    values: List[str]
    targetId: Optional[str] = None
    timeoutMs: Optional[int] = None


class DragRequest(BaseModel):
    startRef: str
    endRef: str
    targetId: Optional[str] = None
    timeoutMs: Optional[int] = None


class WaitRequest(BaseModel):
    selector: Optional[str] = None
    timeoutMs: int = 30000
    targetId: Optional[str] = None


@router.post("/click", response_model=ClickResponse)
async def click(request: ClickRequest):
    """点击元素"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        
        # 先创建快照以获取元素信息
        snapshot = await pw_client.create_snapshot(tab.page)
        
        # 点击
        await pw_client.click_by_ref(
            tab.page,
            request.ref,
            snapshot,
            double_click=request.doubleClick,
            timeout=request.timeoutMs or 5000
        )
        
        await tab.update_info()
        
        return ClickResponse(
            targetId=tab.target_id,
            url=tab.url,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/type", response_model=TypeResponse)
async def type_text(request: TypeRequest):
    """输入文本"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        
        # 创建快照
        snapshot = await pw_client.create_snapshot(tab.page)
        
        # 输入
        await pw_client.type_by_ref(
            tab.page,
            request.ref,
            request.text,
            snapshot,
            submit=request.submit,
            timeout=request.timeoutMs or 5000
        )
        
        return TypeResponse(
            targetId=tab.target_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fill", response_model=TypeResponse)
async def fill(request: FillRequest):
    """填充表单"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        
        # 创建快照
        snapshot = await pw_client.create_snapshot(tab.page)
        
        # 填充
        await pw_client.fill_by_ref(
            tab.page,
            request.ref,
            request.text,
            snapshot,
            timeout=request.timeoutMs or 5000
        )
        
        return TypeResponse(
            targetId=tab.target_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/press", response_model=GenericResponse)
async def press_key(request: PressRequest):
    """按键"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        
        await tab.page.press("body", request.key, delay=request.delayMs)
        
        return GenericResponse(
            ok=True,
            success=True,
            targetId=tab.target_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hover", response_model=GenericResponse)
async def hover(request: HoverRequest):
    """悬停"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        
        # 创建快照
        snapshot = await pw_client.create_snapshot(tab.page)
        element = snapshot.get_element(request.ref)
        
        if not element:
            raise HTTPException(status_code=404, detail=f"Element ref not found: {request.ref}")
        
        # 悬停
        if element.role and element.name:
            locator = tab.page.get_by_role(element.role, name=element.name, exact=False)
            await locator.hover(timeout=request.timeoutMs or 5000)
        
        return GenericResponse(
            ok=True,
            success=True,
            targetId=tab.target_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/select", response_model=GenericResponse)
async def select_option(request: SelectRequest):
    """选择选项"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        
        # 创建快照
        snapshot = await pw_client.create_snapshot(tab.page)
        element = snapshot.get_element(request.ref)
        
        if not element:
            raise HTTPException(status_code=404, detail=f"Element ref not found: {request.ref}")
        
        # 选择
        if element.role and element.name:
            locator = tab.page.get_by_role(element.role, name=element.name, exact=False)
            await locator.select_option(request.values, timeout=request.timeoutMs or 5000)
        
        return GenericResponse(
            ok=True,
            success=True,
            targetId=tab.target_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wait", response_model=GenericResponse)
async def wait(request: WaitRequest):
    """等待"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        if request.selector:
            tab = await manager.tab_manager.ensure_tab_available(request.targetId)
            await pw_client.wait_for_selector(tab.page, request.selector, request.timeoutMs)
        else:
            # 简单等待
            await asyncio.sleep(request.timeoutMs / 1000)
        
        return GenericResponse(
            ok=True,
            success=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 导入 asyncio 用于 wait 路由
import asyncio
