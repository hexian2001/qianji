"""
API 响应模型 - 对应 OpenClaw 的响应格式
"""

from typing import Any

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
    pid: int | None = None
    cdpPort: int | None = None
    cdpUrl: str | None = None
    chosenBrowser: str | None = None
    detectedBrowser: str | None = None
    detectedExecutablePath: str | None = None
    detectError: str | None = None
    userDataDir: str | None = None
    color: str = "#FF4500"
    headless: bool = True
    noSandbox: bool = False
    executablePath: str | None = None
    attachOnly: bool = False


class NavigateResponse(BaseModel):
    """导航响应"""

    ok: bool = True
    success: bool = True
    targetId: str
    url: str
    title: str | None = None
    snapshot: dict[str, Any] | None = None


class SnapshotElementData(BaseModel):
    """快照元素数据"""

    ref: str
    type: str
    name: str | None = None
    role: str | None = None
    text: str | None = None
    selector: str | None = None
    ariaLabel: str | None = None
    placeholder: str | None = None
    value: str | None = None
    checked: bool | None = None
    disabled: bool | None = None
    bbox: dict[str, float] | None = None


class SnapshotResponse(BaseModel):
    """快照响应"""

    ok: bool = True
    success: bool = True
    targetId: str
    url: str
    title: str
    text: str
    summary: str
    interactive: str
    domHash: str | None = None
    totalElements: int | None = None
    elements: dict[str, SnapshotElementData]
    viewport: dict[str, int]
    scroll: dict[str, int]
    metadata: dict[str, Any] | None = None


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
    targetId: str | None = None
    url: str | None = None
    snapshot: dict[str, Any] | None = None
    data: dict[str, Any] | None = None
