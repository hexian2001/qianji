"""API 路由"""

from fastapi import APIRouter

from .basic import router as basic_router
from .agent_act import router as agent_act_router
from .agent_snapshot import router as agent_snapshot_router
from .agent_storage import router as agent_storage_router
from .agent_debug import router as agent_debug_router
from .tabs import router as tabs_router


def create_api_router() -> APIRouter:
    """创建 API 路由"""
    api_router = APIRouter()
    
    # 基础路由 (/, /start, /stop, /reset)
    api_router.include_router(basic_router, tags=["basic"])
    
    # Agent 路由
    api_router.include_router(agent_snapshot_router, prefix="", tags=["snapshot"])
    api_router.include_router(agent_act_router, prefix="/act", tags=["act"])
    api_router.include_router(agent_storage_router, prefix="/storage", tags=["storage"])
    api_router.include_router(agent_debug_router, prefix="/debug", tags=["debug"])
    api_router.include_router(tabs_router, prefix="/tabs", tags=["tabs"])
    
    return api_router
