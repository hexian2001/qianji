"""数据模型"""

from .config import BrowserConfig, ProfileConfig
from .responses import (
    ClickResponse,
    ErrorResponse,
    NavigateResponse,
    PDFResponse,
    ScreenshotResponse,
    SnapshotResponse,
    StatusResponse,
    TabInfo,
    TypeResponse,
)
from .snapshot import ElementRef, Snapshot, SnapshotElement

__all__ = [
    "BrowserConfig",
    "ProfileConfig",
    "Snapshot",
    "ElementRef",
    "SnapshotElement",
    "NavigateResponse",
    "SnapshotResponse",
    "ClickResponse",
    "TypeResponse",
    "ScreenshotResponse",
    "PDFResponse",
    "StatusResponse",
    "TabInfo",
    "ErrorResponse",
]
