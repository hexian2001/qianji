"""
快照系统 - 对应 OpenClaw browser/pw-role-snapshot.js
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import json


@dataclass
class SnapshotElement:
    """快照中的单个元素"""
    ref: str
    element_type: str  # button, link, textbox, etc.
    name: Optional[str] = None
    role: Optional[str] = None
    text: Optional[str] = None
    selector: Optional[str] = None
    aria_label: Optional[str] = None
    aria_labelled_by: Optional[str] = None
    placeholder: Optional[str] = None
    value: Optional[str] = None
    checked: Optional[bool] = None
    disabled: Optional[bool] = None
    required: Optional[bool] = None
    bbox: Optional[Dict[str, float]] = None  # x, y, width, height
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "ref": self.ref,
            "type": self.element_type,
        }
        if self.name:
            result["name"] = self.name
        if self.role:
            result["role"] = self.role
        if self.text:
            result["text"] = self.text[:100]  # 限制长度
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
        return result
    
    def to_line(self) -> str:
        """转换为单行文本表示"""
        parts = [f"[{self.ref}]"]
        parts.append(self.element_type)
        
        # 优先显示名称
        display = self.name or self.aria_label or self.placeholder or self.text
        if display:
            display = display.replace("\n", " ").replace("\r", "")[:50]
            parts.append(f": {display}")
        
        return " ".join(parts)


@dataclass
class Snapshot:
    """页面快照 - 对应 OpenClaw 的 snapshot"""
    url: str
    title: str
    text: str
    elements: Dict[str, SnapshotElement] = field(default_factory=dict)
    refs: List[str] = field(default_factory=list)
    
    # 元数据
    viewport_width: int = 1280
    viewport_height: int = 720
    scroll_x: int = 0
    scroll_y: int = 0
    
    def get_element(self, ref: str) -> Optional[SnapshotElement]:
        """通过 ref 获取元素"""
        return self.elements.get(ref)
    
    def get_interactive_elements(self) -> List[SnapshotElement]:
        """获取所有可交互元素"""
        interactive_types = {
            "button", "link", "textbox", "checkbox", "radio", 
            "combobox", "menuitem", "tab", "treeitem"
        }
        return [
            e for e in self.elements.values()
            if e.element_type in interactive_types or e.role in interactive_types
        ]
    
    def to_interactive_text(self) -> str:
        """生成可交互元素文本列表"""
        elements = self.get_interactive_elements()
        lines = [e.to_line() for e in elements if e.ref]
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "url": self.url,
            "title": self.title,
            "text": self.text[:5000] if self.text else "",  # 限制长度
            "interactive": self.to_interactive_text(),
            "elements": {
                ref: elem.to_dict()
                for ref, elem in self.elements.items()
            },
            "viewport": {
                "width": self.viewport_width,
                "height": self.viewport_height,
            },
            "scroll": {
                "x": self.scroll_x,
                "y": self.scroll_y,
            },
        }
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class ElementRef:
    """元素引用 - 用于操作元素"""
    ref: str
    snapshot_id: Optional[str] = None
    
    def __str__(self) -> str:
        return self.ref
