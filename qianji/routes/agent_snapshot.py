"""
快照路由 - 增强版
导航、快照、截图、PDF
支持快照缓存 + 自动快照
"""

import logging
import os
import tempfile

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core import get_pw_client, get_snapshot_cache
from ..models.responses import (
    GenericResponse,
    NavigateResponse,
    PDFResponse,
    ScreenshotResponse,
    SnapshotElementData,
    SnapshotResponse,
)
from ..models.snapshot import Snapshot
from .basic import ensure_browser_manager

logger = logging.getLogger("qianji.routes.snapshot")
router = APIRouter()


class NavigateRequest(BaseModel):
    url: str
    browserId: str | None = None
    targetId: str | None = None
    timeout: int = 30000
    waitUntil: str = "domcontentloaded"  # 新增: 可配置等待策略


class SnapshotRequest(BaseModel):
    browserId: str | None = None
    targetId: str | None = None
    refs: str = "role"
    maxElements: int = 150  # V3: 截断上限
    viewportOnly: bool = False  # V3: 仅可视区域


class ScreenshotRequest(BaseModel):
    browserId: str | None = None
    targetId: str | None = None
    fullPage: bool = False
    ref: str | None = None
    element: str | None = None
    type: str = "png"
    path: str | None = None
    annotate: bool = False  # V3: 是否标注元素


class PDFRequest(BaseModel):
    browserId: str | None = None
    targetId: str | None = None


class ScrollRequest(BaseModel):
    browserId: str | None = None
    targetId: str | None = None
    direction: str = "down"  # up, down, left, right
    amount: int = 500
    ref: str | None = None  # 滚动到指定元素


class NavigateAndSnapshotRequest(BaseModel):
    """复合操作: 导航 + 快照"""

    url: str
    browserId: str | None = None
    targetId: str | None = None
    timeout: int = 30000
    waitUntil: str = "domcontentloaded"


class GetTextRequest(BaseModel):
    ref: str
    browserId: str | None = None
    targetId: str | None = None


class GetAttributeRequest(BaseModel):
    ref: str
    attribute: str
    browserId: str | None = None
    targetId: str | None = None


def _build_snapshot_response(snapshot: Snapshot, target_id: str) -> SnapshotResponse:
    """构建快照响应（复用）"""
    elements_data = {
        ref: SnapshotElementData(**elem.to_dict()) for ref, elem in snapshot.elements.items()
    }
    return SnapshotResponse(
        targetId=target_id,
        url=snapshot.url,
        title=snapshot.title,
        text=snapshot.text[:5000],
        summary=snapshot.get_summary(),
        interactive=snapshot.to_interactive_text(),
        domHash=snapshot.dom_hash,
        totalElements=snapshot.total_elements_found,
        elements=elements_data,
        viewport={"width": snapshot.viewport_width, "height": snapshot.viewport_height},
        scroll={"x": snapshot.scroll_x, "y": snapshot.scroll_y},
    )


@router.post("/navigate", response_model=NavigateResponse)
async def navigate(request: NavigateRequest):
    """导航到 URL - 如果浏览器未运行会自动启动"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()
    cache = get_snapshot_cache()

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)

        # 导航后使快照失效
        cache.invalidate(browser_id, tab.target_id)

        result = await pw_client.navigate(
            tab.page,
            request.url,
            timeout=request.timeout,
            wait_until=request.waitUntil,
        )

        # 导航后立即注入反检测脚本
        try:
            await tab.page.evaluate("""
                (() => {
                    Object.defineProperty(Navigator.prototype, 'platform', {
                        get: () => 'Win32',
                        configurable: true,
                        enumerable: true
                    });
                    Object.defineProperty(Navigator.prototype, 'languages', {
                        get: () => ['zh-CN', 'zh', 'en-US', 'en'],
                        configurable: true
                    });
                })();
            """)
        except:
            pass

        await tab.update_info()

        return NavigateResponse(
            targetId=tab.target_id,
            url=result["url"],
            title=result.get("title"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/snapshot", response_model=SnapshotResponse)
async def create_snapshot(request: SnapshotRequest):
    """创建页面快照 - 如果浏览器未运行会自动启动"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()
    cache = get_snapshot_cache()

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)

        # 总是创建新快照（用户显式请求）
        snapshot = await pw_client.create_snapshot(
            tab.page,
            refs=request.refs,
            max_elements=request.maxElements,
            viewport_only=request.viewportOnly,
        )
        cache.put(browser_id, tab.target_id, snapshot)
        await tab.update_info()

        return _build_snapshot_response(snapshot, tab.target_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/navigate_and_snapshot", response_model=SnapshotResponse)
async def navigate_and_snapshot(request: NavigateAndSnapshotRequest):
    """复合操作: 导航到URL并立即返回快照（减少 LLM 调用步骤）"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()
    cache = get_snapshot_cache()

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)

        # 导航
        cache.invalidate(browser_id, tab.target_id)
        await pw_client.navigate(
            tab.page,
            request.url,
            timeout=request.timeout,
            wait_until=request.waitUntil,
        )

        # 立即快照
        snapshot = await pw_client.create_snapshot(tab.page)
        cache.put(browser_id, tab.target_id, snapshot)
        await tab.update_info()

        return _build_snapshot_response(snapshot, tab.target_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/screenshot", response_model=ScreenshotResponse)
async def take_screenshot(request: ScreenshotRequest):
    """截图 - 如果浏览器未运行会自动启动"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()
    cache = get_snapshot_cache()

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)

        # 确定输出路径
        if request.path:
            output_path = request.path
            os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
        else:
            suffix = ".jpg" if request.type == "jpeg" else ".png"
            fd, output_path = tempfile.mkstemp(suffix=suffix, prefix="qianji_screenshot_")
            os.close(fd)

        # 如果有 ref 或标注，从缓存获取快照或创建新的
        snapshot = None
        if request.ref or request.annotate:
            snapshot = cache.get(browser_id, tab.target_id)
            if not snapshot:
                snapshot = await pw_client.create_snapshot(tab.page)
                cache.put(browser_id, tab.target_id, snapshot)

        if request.annotate and snapshot:
            await pw_client.annotated_screenshot(tab.page, path=output_path, snapshot=snapshot)
        else:
            await pw_client.screenshot(
                tab.page,
                path=output_path,
                full_page=request.fullPage,
                ref=request.ref,
                snapshot=snapshot,
            )

        return ScreenshotResponse(
            path=output_path,
            targetId=tab.target_id,
            url=tab.url,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pdf", response_model=PDFResponse)
async def generate_pdf(request: PDFRequest):
    """生成 PDF - 如果浏览器未运行会自动启动"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)

        fd, path = tempfile.mkstemp(suffix=".pdf", prefix="qianji_pdf_")
        os.close(fd)

        await pw_client.pdf(tab.page, path=path)

        return PDFResponse(
            path=path,
            targetId=tab.target_id,
            url=tab.url,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/go-back", response_model=GenericResponse)
async def go_back(browserId: str | None = None, targetId: str | None = None):
    """后退 - 如果浏览器未运行会自动启动"""
    browser_id, manager = await ensure_browser_manager(browserId, profile_name=None)
    pw_client = get_pw_client()
    cache = get_snapshot_cache()

    try:
        tab = await manager.tab_manager.ensure_tab_available(targetId)
        cache.invalidate(browser_id, tab.target_id)
        result = await pw_client.go_back(tab.page)
        await tab.update_info()

        # V3: 自动生成新快照
        new_snapshot = await pw_client.create_snapshot(tab.page)
        cache.put(browser_id, tab.target_id, new_snapshot)
        snapshot_resp = _build_snapshot_response(new_snapshot, tab.target_id)

        return GenericResponse(
            ok=True,
            success=True,
            targetId=tab.target_id,
            url=result["url"],
            snapshot=snapshot_resp.model_dump(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/go-forward", response_model=GenericResponse)
async def go_forward(browserId: str | None = None, targetId: str | None = None):
    """前进 - 如果浏览器未运行会自动启动"""
    browser_id, manager = await ensure_browser_manager(browserId, profile_name=None)
    pw_client = get_pw_client()
    cache = get_snapshot_cache()

    try:
        tab = await manager.tab_manager.ensure_tab_available(targetId)
        cache.invalidate(browser_id, tab.target_id)
        result = await pw_client.go_forward(tab.page)
        await tab.update_info()

        # V3: 自动生成新快照
        new_snapshot = await pw_client.create_snapshot(tab.page)
        cache.put(browser_id, tab.target_id, new_snapshot)
        snapshot_resp = _build_snapshot_response(new_snapshot, tab.target_id)

        return GenericResponse(
            ok=True,
            success=True,
            targetId=tab.target_id,
            url=result["url"],
            snapshot=snapshot_resp.model_dump(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload", response_model=GenericResponse)
async def reload(browserId: str | None = None, targetId: str | None = None):
    """刷新 - 如果浏览器未运行会自动启动"""
    browser_id, manager = await ensure_browser_manager(browserId, profile_name=None)
    pw_client = get_pw_client()
    cache = get_snapshot_cache()

    try:
        tab = await manager.tab_manager.ensure_tab_available(targetId)
        cache.invalidate(browser_id, tab.target_id)

        result = await pw_client.reload(tab.page)
        await tab.update_info()

        # V3: 自动生成新快照
        new_snapshot = await pw_client.create_snapshot(tab.page)
        cache.put(browser_id, tab.target_id, new_snapshot)
        snapshot_resp = _build_snapshot_response(new_snapshot, tab.target_id)

        return GenericResponse(
            ok=True,
            success=True,
            targetId=tab.target_id,
            url=result["url"],
            snapshot=snapshot_resp.model_dump(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scroll", response_model=GenericResponse)
async def scroll_page(request: ScrollRequest):
    """滚动页面 - 支持方向滚动和滚动到指定元素"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()
    cache = get_snapshot_cache()

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)

        snapshot = None
        if request.ref:
            snapshot = cache.get(browser_id, tab.target_id)
            if not snapshot:
                snapshot = await pw_client.create_snapshot(tab.page)
                cache.put(browser_id, tab.target_id, snapshot)

        result = await pw_client.scroll(
            tab.page,
            direction=request.direction,
            amount=request.amount,
            ref=request.ref,
            snapshot=snapshot,
        )

        # 滚动后创建新快照（viewport 变了）
        new_snapshot = await pw_client.create_snapshot(tab.page)
        cache.put(browser_id, tab.target_id, new_snapshot)

        return GenericResponse(
            ok=True,
            success=True,
            targetId=tab.target_id,
            snapshot={
                "url": new_snapshot.url,
                "title": new_snapshot.title,
                "summary": new_snapshot.get_summary(),
                "interactive": new_snapshot.to_interactive_text(),
            },
            data=result,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get_text", response_model=GenericResponse)
async def get_element_text(request: GetTextRequest):
    """获取指定元素的文本内容"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()
    cache = get_snapshot_cache()

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)

        snapshot = cache.get(browser_id, tab.target_id)
        if not snapshot:
            snapshot = await pw_client.create_snapshot(tab.page)
            cache.put(browser_id, tab.target_id, snapshot)

        text = await pw_client.get_text_by_ref(tab.page, request.ref, snapshot)

        return GenericResponse(
            ok=True,
            success=True,
            targetId=tab.target_id,
            data={"text": text},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get_attribute", response_model=GenericResponse)
async def get_element_attribute(request: GetAttributeRequest):
    """获取指定元素的属性"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()
    cache = get_snapshot_cache()

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)

        snapshot = cache.get(browser_id, tab.target_id)
        if not snapshot:
            snapshot = await pw_client.create_snapshot(tab.page)
            cache.put(browser_id, tab.target_id, snapshot)

        value = await pw_client.get_attribute_by_ref(
            tab.page, request.ref, request.attribute, snapshot
        )

        return GenericResponse(
            ok=True,
            success=True,
            targetId=tab.target_id,
            data={"attribute": request.attribute, "value": value},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
