"""
API 响应模型 - 对应 OpenClaw 的响应格式
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    success: bool = False


class TabInfo(BaseModel):
    """标签页信息"""
    targetId: str
    url: str
    title: str
    active: bool = False


class StatusResponse(BaseModel):
    """状态响应"""
    enabled: bool
    profile: str
    running: bool
    cdpReady: bool
    cdpHttp: bool
    pid: Optional[int] = None
    cdpPort: Optional[int] = None
    cdpUrl: Optional[str] = None
    chosenBrowser: Optional[str] = None
    detectedBrowser: Optional[str] = None
    detectedExecutablePath: Optional[str] = None
    detectError: Optional[str] = None
    userDataDir: Optional[str] = None
    color: str = "#FF4500"
    headless: bool = True
    noSandbox: bool = False
    executablePath: Optional[str] = None
    attachOnly: bool = False


class NavigateResponse(BaseModel):
    """导航响应"""
    ok: bool = True
    success: bool = True
    targetId: str
    url: str
    title: Optional[str] = None


class SnapshotElementData(BaseModel):
    """快照元素数据"""
    ref: str
    type: str
    name: Optional[str] = None
    role: Optional[str] = None
    text: Optional[str] = None
    selector: Optional[str] = None
    ariaLabel: Optional[str] = None
    placeholder: Optional[str] = None
    value: Optional[str] = None
    checked: Optional[bool] = None
    disabled: Optional[bool] = None
    bbox: Optional[Dict[str, float]] = None


class SnapshotResponse(BaseModel):
    """快照响应"""
    ok: bool = True
    success: bool = True
    targetId: str
    url: str
    title: str
    text: str
    interactive: str
    elements: Dict[str, SnapshotElementData]
    viewport: Dict[str, int]
    scroll: Dict[str, int]


class ClickResponse(BaseModel):
    """点击响应"""
    ok: bool = True
    success: bool = True
    targetId: str
    url: str


class TypeResponse(BaseModel):
    """输入响应"""
    ok: bool = True
    success: bool = True
    targetId: str


class ScreenshotResponse(BaseModel):
    """截图响应"""
    ok: bool = True
    success: bool = True
    path: str
    targetId: str
    url: str


class PDFResponse(BaseModel):
    """PDF响应"""
    ok: bool = True
    success: bool = True
    path: str
    targetId: str
    url: str


class GenericResponse(BaseModel):
    """通用响应"""
    ok: bool = True
    success: bool = True
    targetId: Optional[str] = None
    url: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
