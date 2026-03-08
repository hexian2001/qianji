"""
调试路由 - 增强版
控制台日志、错误、网络请求
使用 deque 限制存储大小
"""

import logging
from collections import deque

from fastapi import APIRouter
from pydantic import BaseModel

from ..models.responses import GenericResponse

logger = logging.getLogger("qianji.routes.debug")
router = APIRouter()

# 全局日志存储 — 使用 deque 限制大小
MAX_LOG_SIZE = 500

_console_logs: dict[str, deque] = {}
_page_errors: dict[str, deque] = {}
_network_requests: dict[str, deque] = {}


def _get_log_key(browser_id: str, target_id: str) -> str:
    return f"{browser_id}:{target_id}"


def _get_logs(store: dict[str, deque], key: str) -> deque:
    if key not in store:
        store[key] = deque(maxlen=MAX_LOG_SIZE)
    return store[key]


def cleanup_logs(browser_id: str, target_id: str):
    """清理指定浏览器/标签页的日志"""
    key = _get_log_key(browser_id, target_id)
    _console_logs.pop(key, None)
    _page_errors.pop(key, None)
    _network_requests.pop(key, None)


def cleanup_browser_logs(browser_id: str):
    """清理指定浏览器的所有日志"""
    keys_to_remove = [k for k in _console_logs if k.startswith(f"{browser_id}:")]
    for key in keys_to_remove:
        _console_logs.pop(key, None)
        _page_errors.pop(key, None)
        _network_requests.pop(key, None)


class LogEntry(BaseModel):
    browserId: str | None = None
    targetId: str | None = None
    type: str = "log"
    text: str


class GetLogsRequest(BaseModel):
    browserId: str | None = None
    targetId: str | None = None
    limit: int = 50


class ClearLogsRequest(BaseModel):
    browserId: str | None = None
    targetId: str | None = None


@router.post("/console/log")
async def add_console_log(entry: LogEntry):
    """添加控制台日志"""
    browser_id = entry.browserId or "default"
    target_id = entry.targetId or "default"
    key = _get_log_key(browser_id, target_id)

    logs = _get_logs(_console_logs, key)
    logs.append(
        {
            "type": entry.type,
            "text": entry.text[:2000],  # 限制单条日志长度
        }
    )

    return GenericResponse(ok=True, success=True)


@router.post("/console/get", response_model=GenericResponse)
async def get_console_logs(request: GetLogsRequest):
    """获取控制台日志"""
    browser_id = request.browserId or "default"
    target_id = request.targetId or "default"
    key = _get_log_key(browser_id, target_id)

    logs = list(_get_logs(_console_logs, key))
    if request.limit:
        logs = logs[-request.limit :]

    return GenericResponse(
        ok=True,
        success=True,
        data={"logs": logs, "count": len(logs)},
    )


@router.post("/console/clear")
async def clear_console_logs(request: ClearLogsRequest):
    """清除控制台日志"""
    browser_id = request.browserId or "default"
    target_id = request.targetId or "default"
    cleanup_logs(browser_id, target_id)

    return GenericResponse(ok=True, success=True)


@router.post("/errors/get", response_model=GenericResponse)
async def get_page_errors(request: GetLogsRequest):
    """获取页面错误"""
    browser_id = request.browserId or "default"
    target_id = request.targetId or "default"
    key = _get_log_key(browser_id, target_id)

    errors = list(_get_logs(_page_errors, key))
    if request.limit:
        errors = errors[-request.limit :]

    return GenericResponse(
        ok=True,
        success=True,
        data={"errors": errors, "count": len(errors)},
    )


@router.post("/errors/clear")
async def clear_page_errors(request: ClearLogsRequest):
    """清除页面错误"""
    browser_id = request.browserId or "default"
    target_id = request.targetId or "default"
    cleanup_logs(browser_id, target_id)

    return GenericResponse(ok=True, success=True)


@router.post("/network/get", response_model=GenericResponse)
async def get_network_requests(request: GetLogsRequest):
    """获取网络请求"""
    browser_id = request.browserId or "default"
    target_id = request.targetId or "default"
    key = _get_log_key(browser_id, target_id)

    requests_log = list(_get_logs(_network_requests, key))
    if request.limit:
        requests_log = requests_log[-request.limit :]

    return GenericResponse(
        ok=True,
        success=True,
        data={"requests": requests_log, "count": len(requests_log)},
    )


@router.post("/network/clear")
async def clear_network_requests(request: ClearLogsRequest):
    """清除网络请求"""
    browser_id = request.browserId or "default"
    target_id = request.targetId or "default"
    cleanup_logs(browser_id, target_id)

    return GenericResponse(ok=True, success=True)


# ==== 日志注入 API（供 BrowserManager 使用）====


def inject_console_log(browser_id: str, target_id: str, log_type: str, text: str):
    """注入控制台日志（供其他模块调用）"""
    key = _get_log_key(browser_id, target_id)
    logs = _get_logs(_console_logs, key)
    logs.append({"type": log_type, "text": text[:2000]})


def inject_page_error(browser_id: str, target_id: str, error: str):
    """注入页面错误"""
    key = _get_log_key(browser_id, target_id)
    errors = _get_logs(_page_errors, key)
    errors.append({"error": error[:2000]})


def inject_network_request(browser_id: str, target_id: str, url: str, method: str, status: int):
    """注入网络请求（只记录关键信息，不记录 headers/body）"""
    key = _get_log_key(browser_id, target_id)
    requests_log = _get_logs(_network_requests, key)
    requests_log.append(
        {
            "url": url[:500],
            "method": method,
            "status": status,
        }
    )
