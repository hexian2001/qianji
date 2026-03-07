"""
调试路由 - 对应 OpenClaw browser/routes/agent.debug.js
提供控制台日志、错误、网络请求等功能
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel

from ..models.responses import GenericResponse
from .basic import get_browser_manager

router = APIRouter()

# 全局日志存储
_console_logs: List[Dict[str, Any]] = []
_page_errors: List[Dict[str, Any]] = []
_network_requests: List[Dict[str, Any]] = []


class ConsoleLogsRequest(BaseModel):
    targetId: Optional[str] = None
    clear: bool = False


class ErrorsRequest(BaseModel):
    targetId: Optional[str] = None
    clear: bool = False


class RequestsRequest(BaseModel):
    targetId: Optional[str] = None
    clear: bool = False


class EvaluateRequest(BaseModel):
    script: str
    arg: Optional[Any] = None
    targetId: Optional[str] = None


def setup_page_listeners(page):
    """设置页面事件监听器"""
    
    def handle_console(msg):
        _console_logs.append({
            "type": msg.type,
            "text": msg.text,
            "location": msg.location,
            "time": msg.timestamp if hasattr(msg, 'timestamp') else None,
        })
    
    def handle_error(error):
        _page_errors.append({
            "message": str(error),
            "time": error.timestamp if hasattr(error, 'timestamp') else None,
        })
    
    def handle_request(request):
        _network_requests.append({
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers) if request.headers else {},
            "time": request.timing if hasattr(request, 'timing') else None,
        })
    
    page.on("console", handle_console)
    page.on("pageerror", handle_error)
    page.on("request", handle_request)


@router.post("/console", response_model=GenericResponse)
async def get_console_logs(request: ConsoleLogsRequest):
    """获取控制台日志"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        # 返回日志副本
        logs = _console_logs.copy()
        
        if request.clear:
            _console_logs.clear()
        
        return GenericResponse(
            ok=True,
            success=True,
            data={"logs": logs}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/errors", response_model=GenericResponse)
async def get_page_errors(request: ErrorsRequest):
    """获取页面错误"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        errors = _page_errors.copy()
        
        if request.clear:
            _page_errors.clear()
        
        return GenericResponse(
            ok=True,
            success=True,
            data={"errors": errors}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/requests", response_model=GenericResponse)
async def get_network_requests(request: RequestsRequest):
    """获取网络请求"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        requests = _network_requests.copy()
        
        if request.clear:
            _network_requests.clear()
        
        return GenericResponse(
            ok=True,
            success=True,
            data={"requests": requests}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate", response_model=GenericResponse)
async def evaluate_script(request: EvaluateRequest):
    """执行 JavaScript"""
    manager = get_browser_manager()
    
    if not manager.is_running:
        raise HTTPException(status_code=503, detail="Browser not running")
    
    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        
        result = await tab.page.evaluate(request.script, request.arg)
        
        return GenericResponse(
            ok=True,
            success=True,
            data={"result": result}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
