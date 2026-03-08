"""
弹窗/对话框路由 - V3
处理 alert/confirm/prompt 弹窗
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core import get_pw_client

logger = logging.getLogger("qianji.routes.dialog")
router = APIRouter()


class DialogModeRequest(BaseModel):
    """设置弹窗处理策略"""

    mode: str = "accept"  # accept / dismiss / custom
    customText: str | None = None


class DialogRespondRequest(BaseModel):
    """手动响应当前弹窗"""

    action: str = "accept"
    text: str | None = None


@router.post("/dialog/handle")
async def set_dialog_mode(request: DialogModeRequest):
    """设置弹窗处理策略

    - accept: 自动接受所有弹窗（默认）
    - dismiss: 自动关闭所有弹窗
    - custom: 用自定义文本接受 prompt 弹窗
    """
    pw = get_pw_client()

    if request.mode not in ("accept", "dismiss", "custom"):
        raise HTTPException(status_code=400, detail=f"Invalid mode: {request.mode}")

    pw.set_dialog_mode(request.mode, request.customText)

    return {
        "mode": request.mode,
        "customText": request.customText,
    }


@router.get("/dialog/history")
async def get_dialog_history():
    """获取弹窗历史记录"""
    pw = get_pw_client()
    history = pw.get_dialog_history()
    return {
        "dialogs": history,
        "count": len(history),
    }
