"""
存储路由 - 对应 OpenClaw browser/routes/agent.storage.js
提供 Cookie 和 Storage 管理
支持多浏览器架构
"""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models.responses import GenericResponse
from .basic import ensure_browser_manager

router = APIRouter()


class GetCookiesRequest(BaseModel):
    browserId: str | None = None
    targetId: str | None = None
    urls: list[str] | None = None


class SetCookieRequest(BaseModel):
    name: str
    value: str
    url: str | None = None
    domain: str | None = None
    path: str | None = None
    expires: float | None = None
    httpOnly: bool | None = None
    secure: bool | None = None
    sameSite: Literal["Strict", "Lax", "None"] | None = None
    browserId: str | None = None
    targetId: str | None = None


class DeleteCookiesRequest(BaseModel):
    name: str | None = None
    url: str | None = None
    domain: str | None = None
    path: str | None = None
    browserId: str | None = None
    targetId: str | None = None


class StorageRequest(BaseModel):
    kind: Literal["localStorage", "sessionStorage"]
    browserId: str | None = None
    targetId: str | None = None


class StorageSetRequest(BaseModel):
    kind: Literal["localStorage", "sessionStorage"]
    key: str
    value: str
    browserId: str | None = None
    targetId: str | None = None


class StorageRemoveRequest(BaseModel):
    kind: Literal["localStorage", "sessionStorage"]
    key: str
    browserId: str | None = None
    targetId: str | None = None


class StorageClearRequest(BaseModel):
    kind: Literal["localStorage", "sessionStorage"]
    browserId: str | None = None
    targetId: str | None = None


import json  # 用于 storage 路由


@router.post("/cookies", response_model=GenericResponse)
async def get_cookies(request: GetCookiesRequest):
    """获取 Cookie"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)

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

        return GenericResponse(ok=True, success=True, data={"cookies": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cookies/set", response_model=GenericResponse)
async def set_cookie(request: SetCookieRequest):
    """设置 Cookie"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)

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
    """清除 Cookie - 修复: 支持按 name/domain/path 过滤"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)

        if request.name or request.domain or request.path:
            # 删除匹配条件的 cookie
            filter_kwargs = {}
            if request.name:
                filter_kwargs["name"] = request.name
            if request.domain:
                filter_kwargs["domain"] = request.domain
            if request.path:
                filter_kwargs["path"] = request.path
            await tab.page.context.clear_cookies(**filter_kwargs)
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
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)

        # 安全参数传递，避免 JS 注入
        storage_kind = request.kind  # Pydantic Literal 已校验
        data = await tab.page.evaluate(
            """(kind) => {
                const storage = kind === 'localStorage' ? window.localStorage : window.sessionStorage;
                const result = {};
                for (let i = 0; i < storage.length; i++) {
                    const key = storage.key(i);
                    result[key] = storage.getItem(key);
                }
                return result;
            }""",
            storage_kind,
        )

        return GenericResponse(ok=True, success=True, data={"storage": data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/storage/set", response_model=GenericResponse)
async def set_storage(request: StorageSetRequest):
    """设置 Storage"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)

        await tab.page.evaluate(
            """([kind, key, value]) => {
                const storage = kind === 'localStorage' ? window.localStorage : window.sessionStorage;
                storage.setItem(key, value);
            }""",
            [request.kind, request.key, request.value],
        )

        return GenericResponse(
            ok=True,
            success=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/storage/remove", response_model=GenericResponse)
async def remove_storage(request: StorageRemoveRequest):
    """删除 Storage 项"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)

        await tab.page.evaluate(
            """([kind, key]) => {
                const storage = kind === 'localStorage' ? window.localStorage : window.sessionStorage;
                storage.removeItem(key);
            }""",
            [request.kind, request.key],
        )

        return GenericResponse(
            ok=True,
            success=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/storage/clear", response_model=GenericResponse)
async def clear_storage(request: StorageClearRequest):
    """清空 Storage"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)

        await tab.page.evaluate(
            """(kind) => {
                const storage = kind === 'localStorage' ? window.localStorage : window.sessionStorage;
                storage.clear();
            }""",
            request.kind,
        )

        return GenericResponse(
            ok=True,
            success=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Cookies 会话保存/加载 ============

from pathlib import Path


class SaveCookiesRequest(BaseModel):
    """保存 Cookies 请求"""

    browserId: str | None = None
    targetId: str | None = None
    storage_name: str = "default"


class LoadCookiesRequest(BaseModel):
    """加载 Cookies 请求"""

    browserId: str | None = None
    targetId: str | None = None
    storage_name: str = "default"


def get_cookies_storage_dir() -> Path:
    """获取 cookies 存储目录"""
    storage_dir = Path.home() / ".qianji" / "cookies"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


@router.post("/save_cookies", response_model=GenericResponse)
async def save_cookies(request: SaveCookiesRequest):
    """保存当前页面的 cookies 到文件"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)

        # 获取所有 cookies
        cookies = await tab.page.context.cookies()

        # 准备存储数据
        storage_data = {
            "url": tab.page.url,
            "cookies": cookies,
            "timestamp": str(datetime.now()),
        }

        # 保存到文件
        storage_dir = get_cookies_storage_dir()
        file_path = storage_dir / f"{request.storage_name}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(storage_data, f, indent=2, ensure_ascii=False)

        return GenericResponse(
            ok=True,
            success=True,
            data={
                "path": str(file_path),
                "cookie_count": len(cookies),
                "storage_name": request.storage_name,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load_cookies", response_model=GenericResponse)
async def load_cookies(request: LoadCookiesRequest):
    """从文件加载 cookies 到当前页面"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)

        # 读取文件
        storage_dir = get_cookies_storage_dir()
        file_path = storage_dir / f"{request.storage_name}.json"

        if not file_path.exists():
            return GenericResponse(
                ok=False, success=False, error=f"Cookie session '{request.storage_name}' not found"
            )

        with open(file_path, encoding="utf-8") as f:
            storage_data = json.load(f)

        cookies = storage_data.get("cookies", [])

        # 添加 cookies 到浏览器上下文
        if cookies:
            await tab.page.context.add_cookies(cookies)

        return GenericResponse(
            ok=True,
            success=True,
            data={
                "cookie_count": len(cookies),
                "storage_name": request.storage_name,
                "original_url": storage_data.get("url", ""),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list_sessions", response_model=GenericResponse)
async def list_cookie_sessions():
    """列出所有保存的 cookie 会话"""
    try:
        storage_dir = get_cookies_storage_dir()
        sessions = []

        for file_path in storage_dir.glob("*.json"):
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append(
                    {
                        "name": file_path.stem,
                        "url": data.get("url", ""),
                        "timestamp": data.get("timestamp", ""),
                        "cookie_count": len(data.get("cookies", [])),
                    }
                )
            except:
                pass

        return GenericResponse(ok=True, success=True, data={"sessions": sessions})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
