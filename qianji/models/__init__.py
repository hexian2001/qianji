"""数据模型"""

from .config import BrowserConfig, ProfileConfig
from .snapshot import Snapshot, ElementRef, SnapshotElement
from .responses import (
    NavigateResponse,
    SnapshotResponse,
    ClickResponse,
    TypeResponse,
    ScreenshotResponse,
    PDFResponse,
    StatusResponse,
    TabInfo,
    ErrorResponse,
)

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
