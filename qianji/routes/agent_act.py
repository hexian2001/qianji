"""
操作路由 - 增强版
点击、输入、填充、按键、选择
操作后自动返回最新快照，减少 LLM 调用步骤
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core import get_pw_client, get_snapshot_cache
from ..models.responses import GenericResponse
from .basic import ensure_browser_manager

logger = logging.getLogger("qianji.routes.act")
router = APIRouter()


class ClickRequest(BaseModel):
    ref: str
    browserId: str | None = None
    targetId: str | None = None
    doubleClick: bool = False


class TypeRequest(BaseModel):
    ref: str
    text: str
    browserId: str | None = None
    targetId: str | None = None
    submit: bool = False
    slowly: bool = False


class FillRequest(BaseModel):
    ref: str
    text: str
    browserId: str | None = None
    targetId: str | None = None


class PressRequest(BaseModel):
    key: str
    browserId: str | None = None
    targetId: str | None = None


class HoverRequest(BaseModel):
    ref: str
    browserId: str | None = None
    targetId: str | None = None


class SelectRequest(BaseModel):
    ref: str
    values: list[str]
    browserId: str | None = None
    targetId: str | None = None


class FillFormField(BaseModel):
    ref: str
    text: str


class FillFormRequest(BaseModel):
    """批量填写表单"""

    fields: list[FillFormField]
    submitRef: str | None = None
    browserId: str | None = None
    targetId: str | None = None


class EvaluateRequest(BaseModel):
    script: str
    browserId: str | None = None
    targetId: str | None = None


class WaitForElementRequest(BaseModel):
    selector: str
    browserId: str | None = None
    targetId: str | None = None
    timeout: int = 30000


class UploadFileRequest(BaseModel):
    """文件上传"""

    ref: str
    filePaths: list[str]
    browserId: str | None = None
    targetId: str | None = None


async def _get_snapshot_for_action(browser_id: str, manager, target_id=None):
    """获取操作用的快照（优先缓存，无缓存则新建）"""
    pw_client = get_pw_client()
    cache = get_snapshot_cache()
    tab = await manager.tab_manager.ensure_tab_available(target_id)

    snapshot = cache.get(browser_id, tab.target_id)
    if not snapshot:
        snapshot = await pw_client.create_snapshot(tab.page)
        cache.put(browser_id, tab.target_id, snapshot)

    return tab, snapshot


async def _post_action_snapshot(browser_id: str, tab):
    """操作后创建新快照并缓存（自动返回给 LLM）"""
    pw_client = get_pw_client()
    cache = get_snapshot_cache()

    # 操作后等待短暂时间让页面响应
    await pw_client.wait_for_timeout(tab.page, 300)

    new_snapshot = await pw_client.create_snapshot(tab.page)
    cache.put(browser_id, tab.target_id, new_snapshot)
    return new_snapshot


@router.post("/click")
async def click(request: ClickRequest):
    """点击元素 - 操作后自动返回最新快照"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()

    try:
        tab, snapshot = await _get_snapshot_for_action(browser_id, manager, request.targetId)

        await pw_client.click_by_ref(
            tab.page,
            request.ref,
            snapshot,
            double_click=request.doubleClick,
        )

        # 操作后自动返回快照
        new_snapshot = await _post_action_snapshot(browser_id, tab)

        return {
            "ok": True,
            "success": True,
            "targetId": tab.target_id,
            "clicked": request.ref,
            "snapshot": {
                "url": new_snapshot.url,
                "title": new_snapshot.title,
                "interactive": new_snapshot.to_interactive_text(),
                "summary": new_snapshot.get_summary(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/type")
async def type_text(request: TypeRequest):
    """输入文本 - 操作后自动返回最新快照"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()

    try:
        tab, snapshot = await _get_snapshot_for_action(browser_id, manager, request.targetId)

        await pw_client.type_by_ref(
            tab.page,
            request.ref,
            request.text,
            snapshot,
            submit=request.submit,
        )

        new_snapshot = await _post_action_snapshot(browser_id, tab)

        return {
            "ok": True,
            "success": True,
            "targetId": tab.target_id,
            "typed": request.ref,
            "snapshot": {
                "url": new_snapshot.url,
                "title": new_snapshot.title,
                "interactive": new_snapshot.to_interactive_text(),
                "summary": new_snapshot.get_summary(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fill")
async def fill(request: FillRequest):
    """填充表单字段 - 操作后自动返回最新快照"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()

    try:
        tab, snapshot = await _get_snapshot_for_action(browser_id, manager, request.targetId)

        await pw_client.fill_by_ref(
            tab.page,
            request.ref,
            request.text,
            snapshot,
        )

        new_snapshot = await _post_action_snapshot(browser_id, tab)

        return {
            "ok": True,
            "success": True,
            "targetId": tab.target_id,
            "filled": request.ref,
            "snapshot": {
                "url": new_snapshot.url,
                "title": new_snapshot.title,
                "interactive": new_snapshot.to_interactive_text(),
                "summary": new_snapshot.get_summary(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/press")
async def press_key(request: PressRequest):
    """按键"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        await tab.page.keyboard.press(request.key)

        new_snapshot = await _post_action_snapshot(browser_id, tab)

        return {
            "ok": True,
            "success": True,
            "targetId": tab.target_id,
            "key": request.key,
            "snapshot": {
                "url": new_snapshot.url,
                "title": new_snapshot.title,
                "interactive": new_snapshot.to_interactive_text(),
                "summary": new_snapshot.get_summary(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hover")
async def hover(request: HoverRequest):
    """悬停元素"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()

    try:
        tab, snapshot = await _get_snapshot_for_action(browser_id, manager, request.targetId)
        await pw_client.hover_by_ref(tab.page, request.ref, snapshot)

        new_snapshot = await _post_action_snapshot(browser_id, tab)

        return {
            "ok": True,
            "success": True,
            "targetId": tab.target_id,
            "hovered": request.ref,
            "snapshot": {
                "url": new_snapshot.url,
                "title": new_snapshot.title,
                "interactive": new_snapshot.to_interactive_text(),
                "summary": new_snapshot.get_summary(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/select")
async def select_option(request: SelectRequest):
    """下拉选择 - 操作后自动返回快照"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()

    try:
        tab, snapshot = await _get_snapshot_for_action(browser_id, manager, request.targetId)
        await pw_client.select_by_ref(tab.page, request.ref, request.values, snapshot)

        new_snapshot = await _post_action_snapshot(browser_id, tab)

        return {
            "ok": True,
            "success": True,
            "targetId": tab.target_id,
            "selected": request.values,
            "snapshot": {
                "url": new_snapshot.url,
                "title": new_snapshot.title,
                "interactive": new_snapshot.to_interactive_text(),
                "summary": new_snapshot.get_summary(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fill_form")
async def fill_form(request: FillFormRequest):
    """批量填写表单 - 减少 LLM 调用步骤"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()

    try:
        tab, snapshot = await _get_snapshot_for_action(browser_id, manager, request.targetId)

        fields_data = [{"ref": f.ref, "text": f.text} for f in request.fields]
        await pw_client.fill_form(
            tab.page,
            fields_data,
            snapshot,
            submit_ref=request.submitRef,
        )

        new_snapshot = await _post_action_snapshot(browser_id, tab)

        return {
            "ok": True,
            "success": True,
            "targetId": tab.target_id,
            "fieldsFilled": len(request.fields),
            "submitted": request.submitRef is not None,
            "snapshot": {
                "url": new_snapshot.url,
                "title": new_snapshot.title,
                "interactive": new_snapshot.to_interactive_text(),
                "summary": new_snapshot.get_summary(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate")
async def evaluate(request: EvaluateRequest):
    """执行 JavaScript"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        result = await pw_client.evaluate(tab.page, request.script)

        # V3: 自动生成新快照
        new_snapshot = await pw_client.create_snapshot(tab.page)
        cache = get_snapshot_cache()
        cache.put(browser_id, tab.target_id, new_snapshot)

        # We need _build_snapshot_response here, but it's in agent_snapshot.py.
        # Let's just manually build the dict or import it if possible.
        # Actually agent_act.py has _post_action_snapshot which does exactly this.

        new_snapshot_data = await _post_action_snapshot(browser_id, tab)

        return GenericResponse(
            ok=True,
            success=True,
            targetId=tab.target_id,
            data={"result": result},
            snapshot={
                "url": new_snapshot_data.url,
                "title": new_snapshot_data.title,
                "interactive": new_snapshot_data.to_interactive_text(),
                "summary": new_snapshot_data.get_summary(),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wait_for_element")
async def wait_for_element(request: WaitForElementRequest):
    """等待元素出现"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()
    cache = get_snapshot_cache()

    try:
        tab = await manager.tab_manager.ensure_tab_available(request.targetId)
        found = await pw_client.wait_for_selector(
            tab.page, request.selector, timeout=request.timeout
        )

        # 等待后使旧快照失效
        cache.invalidate(browser_id, tab.target_id)

        return {
            "ok": True,
            "success": True,
            "targetId": tab.target_id,
            "found": found,
            "selector": request.selector,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_file(request: UploadFileRequest):
    """文件上传"""
    browser_id, manager = await ensure_browser_manager(request.browserId, profile_name=None)
    pw_client = get_pw_client()

    try:
        tab, snapshot = await _get_snapshot_for_action(browser_id, manager, request.targetId)
        await pw_client.upload_file(tab.page, request.ref, request.filePaths, snapshot)

        new_snapshot = await _post_action_snapshot(browser_id, tab)

        return {
            "ok": True,
            "success": True,
            "targetId": tab.target_id,
            "uploaded": request.ref,
            "files": request.filePaths,
            "snapshot": {
                "url": new_snapshot.url,
                "title": new_snapshot.title,
                "interactive": new_snapshot.to_interactive_text(),
                "summary": new_snapshot.get_summary(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/downloads")
async def get_downloads():
    """获取下载列表"""
    pw_client = get_pw_client()
    downloads = pw_client.get_downloads()
    return {
        "downloads": downloads,
        "count": len(downloads),
    }
