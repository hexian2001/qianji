"""
存储路由 - 对应 OpenClaw browser/routes/agent.storage.js
提供 Cookie 和 Storage 管理
"""

from typing import Optional, List, Dict, Any, Literal
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel

from ..models.responses import GenericResponse
from .basic import get_browser_manager

router = APIRouter()


class GetCookiesRequest(BaseModel):
    targetId: Optional[str] = None
    urls: Optional[List[str]] = None


class SetCookieRequest(BaseModel):
    name: str
    value: str
    url: Optional[str] = None
    domain: Optional[str] = None
    path: Optional[str] = None
    expires: Optional[float] = None
    httpOnly: Optional[bool] = None
    secure: Optional[bool] = None
    sameSite: Optional[Literal["Strict", "Lax", "None"]] = None


class DeleteCookiesRequest(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    domain: Optional[str] = None
    path: Optional[str] = None


class StorageRequest(BaseModel):
    kind: Literal["localStorage", "sessionStorage"]
    targetId: Optional[str] = None


class StorageSetRequest(BaseModel):
    kind: Literal["localStorage", "sessionStorage"]
    key: str
    value: str
    targetId: Optional[str] = None


class StorageRemoveRequest(BaseModel):
    kind: Literal["localStorage", "sessionStorage"]
    key: str
    targetId: Optional[str] = None


class StorageClearRequest(BaseModel):
    kind: Literal["localStorage", "sessionStorage"]
    targetId: Optional[str] = None


@router.post("/cookies", response_model=GenericResponse)
async def get_cookies(request: GetCookiesRequest):
    """获取 Cookie"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        
        # 获取所有 cookie 或指定 URL 的 cookie
        if request.urls:
            cookies = []
            for url in request.urls:
                url_cookies = await tab.page.context.cookies(url)
                cookies.extend(url_cookies)
        else:
            cookies = await tab.page.context.cookies()
        
        # 转换为标准格式
        result = [
            {
                "name": c.get("name"),
                "value": c.get("value"),
                "domain": c.get("domain"),
                "path": c.get("path"),
                "expires": c.get("expires"),
                "httpOnly": c.get("httpOnly"),
                "secure": c.get("secure"),
                "sameSite": c.get("sameSite"),
            }
            for c in cookies
        ]
        
        return GenericResponse(
            ok=True,
            success=True,
            data={"cookies": result}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cookies/set", response_model=GenericResponse)
async def set_cookie(request: SetCookieRequest):
    """设置 Cookie"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        
        cookie = {
            "name": request.name,
            "value": request.value,
        }
        
        if request.url:
            cookie["url"] = request.url
        if request.domain:
            cookie["domain"] = request.domain
        if request.path:
            cookie["path"] = request.path
        if request.expires:
            cookie["expires"] = request.expires
        if request.httpOnly is not None:
            cookie["httpOnly"] = request.httpOnly
        if request.secure is not None:
            cookie["secure"] = request.secure
        if request.sameSite:
            cookie["sameSite"] = request.sameSite
        
        await tab.page.context.add_cookies([cookie])
        
        return GenericResponse(
            ok=True,
            success=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cookies/clear", response_model=GenericResponse)
async def clear_cookies(request: DeleteCookiesRequest):
    """清除 Cookie"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        
        if request.name:
            # 删除特定 cookie
            await tab.page.context.clear_cookies()
        else:
            # 清除所有 cookie
            await tab.page.context.clear_cookies()
        
        return GenericResponse(
            ok=True,
            success=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/storage/get", response_model=GenericResponse)
async def get_storage(request: StorageRequest):
    """获取 Storage"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        
        script = f"""
        () => {{
            const storage = window.{request.kind};
            const result = {{}};
            for (let i = 0; i < storage.length; i++) {{
                const key = storage.key(i);
                result[key] = storage.getItem(key);
            }}
            return result;
        }}
        """
        
        data = await tab.page.evaluate(script)
        
        return GenericResponse(
            ok=True,
            success=True,
            data={"storage": data}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/storage/set", response_model=GenericResponse)
async def set_storage(request: StorageSetRequest):
    """设置 Storage"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        
        script = f"""
        () => {{
            window.{request.kind}.setItem({json.dumps(request.key)}, {json.dumps(request.value)});
        }}
        """
        
        await tab.page.evaluate(script)
        
        return GenericResponse(
            ok=True,
            success=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/storage/remove", response_model=GenericResponse)
async def remove_storage(request: StorageRemoveRequest):
    """删除 Storage 项"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        
        script = f"""
        () => {{
            window.{request.kind}.removeItem({json.dumps(request.key)});
        }}
        """
        
        await tab.page.evaluate(script)
        
        return GenericResponse(
            ok=True,
            success=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/storage/clear", response_model=GenericResponse)
async def clear_storage(request: StorageClearRequest):
    """清空 Storage"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        
        script = f"""
        () => {{
            window.{request.kind}.clear();
        }}
        """
        
        await tab.page.evaluate(script)
        
        return GenericResponse(
            ok=True,
            success=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


import json  # 用于 storage 路由
