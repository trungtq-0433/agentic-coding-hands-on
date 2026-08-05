"""Data models for DOCX raw-XML translation engine."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class TextAttr:
    text: str = ""
    font_size: float | None = None
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    font_name: str | None = None
    font_color: str | None = None  # hex string e.g. "FF0000" or None
    hyperlink: str | None = None  # run hyperlink URL (PPTX); None for DOCX

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "font_size": self.font_size,
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "font_name": self.font_name,
            "font_color": self.font_color,
            "hyperlink": self.hyperlink,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TextAttr":
        fc = d.get("font_color")
        if isinstance(fc, list):
            # Convert RGB list to hex string (from XLSX model compat)
            try:
                fc = "{:02X}{:02X}{:02X}".format(int(fc[0]), int(fc[1]), int(fc[2]))
            except Exception:
                fc = None
        elif fc is not None:
            fc = str(fc)
        return cls(
            text=str(d.get("text", "")),
            font_size=_to_float(d.get("font_size")),
            bold=_to_bool(d.get("bold")),
            italic=_to_bool(d.get("italic")),
            underline=_to_bool(d.get("underline")),
            font_name=d.get("font_name") or None,
            font_color=fc,
            hyperlink=d.get("hyperlink") or None,
        )


@dataclass
class TranslateElement:
    id: str
    general_text: str = ""
    components: list = field(default_factory=list)  # list[TextAttr]
    part: str = ""  # XML part name e.g. "word/document.xml"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "general_text": self.general_text,
            "components": [c.to_dict() if isinstance(c, TextAttr) else c for c in self.components],
            "part": self.part,
        }


def _to_float(v) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_bool(v) -> bool | None:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() not in ("false", "0", "none", "null", "")
    return bool(v)
