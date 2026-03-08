"""
快照系统 - V3
支持 snapshot_id 绑定、CSS selector、iframe 标注、DOM hash、viewport 分组裁剪
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SnapshotElement:
    """快照元素 - 支持 iframe 和多策略定位"""

    ref: str
    element_type: str  # button, link, textbox, etc.
    name: str | None = None
    role: str | None = None
    text: str | None = None
    selector: str | None = None  # 唯一 CSS selector
    xpath: str | None = None  # XPath 备用
    aria_label: str | None = None
    aria_labelled_by: str | None = None
    placeholder: str | None = None
    value: str | None = None
    checked: bool | None = None
    disabled: bool | None = None
    required: bool | None = None
    bbox: dict[str, float] | None = None  # x, y, width, height
    visible: bool = True
    in_viewport: bool = True
    # V3: iframe 信息
    frame_id: str | None = None  # None = 主 frame
    frame_name: str | None = None  # iframe 名称或 src

    def to_dict(self) -> dict[str, Any]:
        result = {
            "ref": self.ref,
            "type": self.element_type,
        }
        if self.name:
            result["name"] = self.name
        if self.role:
            result["role"] = self.role
        if self.text:
            result["text"] = self.text[:100]
        if self.selector:
            result["selector"] = self.selector
        if self.aria_label:
            result["ariaLabel"] = self.aria_label
        if self.placeholder:
            result["placeholder"] = self.placeholder
        if self.value is not None:
            result["value"] = self.value
        if self.checked is not None:
            result["checked"] = self.checked
        if self.disabled is not None:
            result["disabled"] = self.disabled
        if self.bbox:
            result["bbox"] = self.bbox
        if self.frame_id:
            result["frameId"] = self.frame_id
        return result

    def to_line(self) -> str:
        parts = [f"[{self.ref}]"]
        parts.append(self.element_type)

        display = self.name or self.aria_label or self.placeholder or self.text
        if display:
            display = display.replace("\n", " ").replace("\r", "")[:50]
            parts.append(f": {display}")

        flags = []
        if self.disabled:
            flags.append("disabled")
        if self.checked is True:
            flags.append("checked")
        if self.value and self.element_type in ("textbox", "searchbox", "spinbutton"):
            val_display = self.value[:20]
            flags.append(f'value="{val_display}"')
        if self.frame_id:
            frame_label = self.frame_name or self.frame_id
            flags.append(f"in iframe: {frame_label}")
        if flags:
            parts.append(f" ({', '.join(flags)})")

        return " ".join(parts)


@dataclass
class Snapshot:
    """页面快照 - V3: dom_hash、viewport 分组、裁剪统计"""

    url: str
    title: str
    text: str
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: float = field(default_factory=time.time)
    elements: dict[str, SnapshotElement] = field(default_factory=dict)
    refs: list[str] = field(default_factory=list)

    # 视口
    viewport_width: int = 1280
    viewport_height: int = 720
    scroll_x: int = 0
    scroll_y: int = 0

    # V3: DOM hash (用于变化检测)
    dom_hash: str = ""

    # V3: 裁剪统计
    total_elements_found: int = 0  # 页面上实际找到的总元素数
    max_elements: int = 150  # 截断上限

    def get_element(self, ref: str) -> SnapshotElement | None:
        return self.elements.get(ref)

    def get_interactive_elements(self) -> list[SnapshotElement]:
        interactive_types = {
            "button",
            "link",
            "textbox",
            "checkbox",
            "radio",
            "combobox",
            "menuitem",
            "tab",
            "treeitem",
            "searchbox",
            "spinbutton",
            "switch",
            "slider",
            "option",
            "listbox",
        }
        return [
            e
            for e in self.elements.values()
            if e.element_type in interactive_types or e.role in interactive_types
        ]

    def get_frame_ids(self) -> list[str]:
        """获取所有 frame ID（不含主 frame）"""
        return list(set(e.frame_id for e in self.elements.values() if e.frame_id is not None))

    def to_interactive_text(self) -> str:
        """生成可交互元素文本 — V3: viewport 分组 + iframe 分组"""
        elements = self.get_interactive_elements()
        if not elements:
            return ""

        lines = []

        # 主 frame viewport 内元素
        main_viewport = [e for e in elements if not e.frame_id and e.in_viewport]
        main_offscreen = [e for e in elements if not e.frame_id and not e.in_viewport]

        if main_viewport:
            for e in main_viewport:
                lines.append(e.to_line())

        if main_offscreen:
            lines.append("--- below viewport ---")
            for e in main_offscreen:
                lines.append(e.to_line())

        # iframe 内元素按 frame 分组
        frame_ids = sorted(set(e.frame_id for e in elements if e.frame_id))
        for fid in frame_ids:
            frame_els = [e for e in elements if e.frame_id == fid]
            if frame_els:
                frame_label = frame_els[0].frame_name or fid
                lines.append(f"--- iframe: {frame_label} ---")
                for e in frame_els:
                    lines.append(e.to_line())

        # 裁剪提示
        if self.total_elements_found > len(self.elements):
            lines.append(
                f"--- showing {len(self.elements)}/{self.total_elements_found} elements "
                f"(use maxElements to see more) ---"
            )

        return "\n".join(lines)

    def get_summary(self) -> str:
        interactive = self.get_interactive_elements()
        type_counts: dict[str, int] = {}
        for e in interactive:
            t = e.element_type
            type_counts[t] = type_counts.get(t, 0) + 1

        parts = []
        for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            parts.append(f"{count} {t}{'s' if count > 1 else ''}")

        summary = f"Page has {', '.join(parts)}" if parts else "No interactive elements found"

        # iframe 统计
        frame_ids = self.get_frame_ids()
        if frame_ids:
            summary += f" across {len(frame_ids) + 1} frames"

        # 裁剪提示
        if self.total_elements_found > len(self.elements):
            summary += f" (truncated from {self.total_elements_found})"

        return summary

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshotId": self.snapshot_id,
            "url": self.url,
            "title": self.title,
            "text": self.text[:5000] if self.text else "",
            "interactive": self.to_interactive_text(),
            "summary": self.get_summary(),
            "domHash": self.dom_hash,
            "elements": {ref: elem.to_dict() for ref, elem in self.elements.items()},
            "viewport": {
                "width": self.viewport_width,
                "height": self.viewport_height,
            },
            "scroll": {
                "x": self.scroll_x,
                "y": self.scroll_y,
            },
            "totalElements": self.total_elements_found,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def is_stale(self, max_age: float = 30.0) -> bool:
        return (time.time() - self.created_at) > max_age


@dataclass
class ElementRef:
    """元素引用 - 用于操作元素"""

    ref: str
    snapshot_id: str | None = None

    def __str__(self) -> str:
        return self.ref
