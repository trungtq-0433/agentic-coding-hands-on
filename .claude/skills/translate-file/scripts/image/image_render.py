#!/usr/bin/env python3
"""
image_render.py — Rendering helpers for image translation.

Ported and extended from file-trans-poc/file_trans/domain/parser/image_parser/:
  - KMeans bg/fg color detection (image_processing.py)
  - Per-language text wrapping (image_parser.py)
  - Binary-search font sizing (image_parser.py)

New: per-language font selection, box expansion path.
"""
import os
import numpy as np
from PIL import ImageFont

_CJK_LANGS = {"ja", "zh", "ko", "zh-cn", "zh-tw"}

_FONTS_CJK = [
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]

_FONTS_LATIN = [
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",       # full diacritic coverage (VI/FR/etc)
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def find_font_path(target_lang: str) -> str | None:
    """Return the best available font for the target language."""
    lang = target_lang.lower().split("-")[0]
    candidates = (_FONTS_CJK + _FONTS_LATIN) if lang in _CJK_LANGS else _FONTS_LATIN
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def polygon_to_bbox(polygon):
    """Return (x, y, w, h) axis-aligned bbox from a list of polygon points."""
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    x, y = min(xs), min(ys)
    return x, y, max(xs) - x, max(ys) - y


def scale_polygon(polygon, img_w, img_h, factor=1.08):
    """Scale polygon outward from its centroid to cover anti-alias halo, clamped to image."""
    arr = np.array(polygon, dtype=float)
    center = arr.mean(axis=0)
    scaled = center + factor * (arr - center)
    scaled[:, 0] = scaled[:, 0].clip(0, img_w - 1)
    scaled[:, 1] = scaled[:, 1].clip(0, img_h - 1)
    return [tuple(int(v) for v in pt) for pt in scaled]


def get_bg_fg_color(img_np, polygon, img_w, img_h):
    """KMeans 3-cluster on polygon bbox region → (bg_rgb, fg_rgb) tuples.

    Falls back to mean color when the region is too small or KMeans fails.
    """
    import warnings
    from sklearn.cluster import KMeans
    from sklearn.exceptions import ConvergenceWarning

    bx, by, bw, bh = polygon_to_bbox(polygon)
    x1, y1 = max(0, int(bx)), max(0, int(by))
    x2, y2 = min(img_w, int(bx + bw)), min(img_h, int(by + bh))

    def _lum(c):
        return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

    def _contrast(c1, c2):
        l1 = (_lum(c1) + 12.75) / 255
        l2 = (_lum(c2) + 12.75) / 255
        return max(l1, l2) / min(l1, l2)

    def _mean_fallback(pixels):
        bg = tuple(int(v) for v in pixels.mean(axis=0))
        fg = (0, 0, 0) if _lum(bg) > 128 else (255, 255, 255)
        return bg, fg

    if x2 <= x1 or y2 <= y1 or (x2 - x1) * (y2 - y1) < 400:
        region = img_np[y1:y2, x1:x2]
        pixels = region.reshape(-1, 3).astype(float) if region.size > 0 else np.array([[255., 255., 255.]])
        return _mean_fallback(pixels)

    region = img_np[y1:y2, x1:x2]
    pixels = region[:, :, :3].reshape(-1, 3).astype(float)

    warnings.filterwarnings("error", category=ConvergenceWarning)
    try:
        km = KMeans(n_clusters=3, random_state=42, n_init=5).fit(pixels)
    except ConvergenceWarning:
        try:
            km = KMeans(n_clusters=2, random_state=42, n_init=5).fit(pixels)
        except ConvergenceWarning:
            warnings.resetwarnings()
            return _mean_fallback(pixels)
    finally:
        warnings.resetwarnings()

    palette = km.cluster_centers_
    counts = np.bincount(km.labels_)
    order = np.argsort(counts)[::-1]
    bg = tuple(int(v) for v in palette[order[0]])
    fg_cand = tuple(int(v) for v in palette[order[1]])
    fg = fg_cand if _contrast(bg, fg_cand) >= 2.5 else (
        (0, 0, 0) if _lum(fg_cand) > 127 else (255, 255, 255)
    )
    return bg, fg


def wrap_text(text, font, max_width, draw, target_lang):
    """Word-based (Latin/VI) or char-based (CJK) wrapper. Returns list of non-empty lines."""
    lang = target_lang.lower().split("-")[0]
    is_cjk = lang in _CJK_LANGS
    tokens = list(text) if is_cjk else text.split()
    sep = "" if is_cjk else " "

    lines, current = [], []
    for token in tokens:
        test = sep.join(current + [token])
        w = draw.textbbox((0, 0), test, font=font)[2]
        if w <= max_width or not current:
            current.append(token)
        else:
            lines.append(sep.join(current).rstrip())
            current = [token]
    if current:
        lines.append(sep.join(current).rstrip())
    return [ln for ln in lines if ln]


def fit_text_to_box(text, bbox_w, bbox_h, draw, font_path, target_lang, min_size=10):
    """Binary-search font size until text wraps and fits bbox_w × bbox_h.

    Returns (font, lines, total_h, expanded_h).
    expanded_h > 0 means text needs bbox_h + expanded_h pixels to fit at min_size.
    """
    start_size = max(min_size, min(int(bbox_h * 0.85), 40))

    def _measure(size):
        try:
            f = ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()
        except Exception:
            f = ImageFont.load_default()
        ls = wrap_text(text, f, max(1, bbox_w - 4), draw, target_lang) or [text]
        lhts = [draw.textbbox((0, 0), l, font=f)[3] - draw.textbbox((0, 0), l, font=f)[1] for l in ls]
        th = sum(lhts) + max(0, len(ls) - 1) * 2
        mw = max(draw.textbbox((0, 0), l, font=f)[2] for l in ls)
        return f, ls, th, mw

    for size in range(start_size, min_size - 1, -1):
        font, lines, total_h, max_w = _measure(size)
        if total_h <= bbox_h and max_w <= bbox_w - 2:
            return font, lines, total_h, 0

    # At min_size, compute overflow
    font, lines, total_h, _ = _measure(min_size)
    return font, lines, total_h, max(0, total_h - bbox_h)
