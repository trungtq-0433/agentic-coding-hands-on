#!/usr/bin/env python3
"""
docx_profile.py - Scan DOCX zip to produce a per-file profile dict.

Emits docx_profile.json alongside docx_structure.json during extraction.
Flags gate which container classes are included and drive validation assertions.
"""

import re
import zipfile


# Byte signatures for quick document.xml scanning
_SIG_TEXTBOX = b'txbxContent'
_SIG_TRACKED_INS = b'<w:ins '
_SIG_TRACKED_DEL = b'<w:del '


def profile(docx_path):
    """Scan DOCX zip and return a profile dict.

    Returns dict with keys:
      has_textboxes, has_shapes, has_comments, has_smartart, has_charts,
      has_tracked_changes, translate_comments, sections
    """
    result = {
        "has_textboxes": False,
        "has_shapes": False,
        "has_comments": False,
        "has_smartart": False,
        "has_charts": False,
        "has_tracked_changes": False,
        "translate_comments": True,
        "sections": 1,
    }

    try:
        with zipfile.ZipFile(docx_path, "r") as zf:
            names = set(zf.namelist())

            # Presence checks from zip namelist
            result["has_comments"] = "word/comments.xml" in names
            result["has_smartart"] = any(n.startswith("word/diagrams/") for n in names)
            result["has_charts"] = any(n.startswith("word/charts/") for n in names)

            # Quick byte-scan of document.xml for textboxes + tracked changes
            if "word/document.xml" in names:
                raw = zf.read("word/document.xml")
                result["has_textboxes"] = _SIG_TEXTBOX in raw
                result["has_shapes"] = result["has_textboxes"]
                result["has_tracked_changes"] = (
                    _SIG_TRACKED_INS in raw or _SIG_TRACKED_DEL in raw
                )

            # Count distinct header/footer sections as a proxy for section count
            hdr_count = sum(
                1 for n in names if re.match(r"^word/header\d+\.xml$", n)
            )
            result["sections"] = max(1, hdr_count)

    except Exception:
        pass

    return result
