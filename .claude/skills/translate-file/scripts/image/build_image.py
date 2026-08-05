#!/usr/bin/env python3
"""
build_image.py — Overlay translated text on original image using Pillow + KMeans.

Reads image_blocks.json (written by extract_image.py save-blocks) and produces
output.jpg / output.png with translated text overlaid in-place.

Strategy per block:
  1. Scale polygon outward 8% to absorb anti-alias halo → mask with bg color.
  2. KMeans-cluster polygon region → bg_color, fg_color (WCAG contrast-checked).
  3. Binary-search font size + per-language wrap until text fits bbox.
  4. If still overflowing at min 10pt → expand bbox downward (reported in
     build_image_report.json, skipped if expansion would overlap next block).
  5. Draw wrapped text centered in the (possibly expanded) bbox.

Usage:
    python3 build_image.py <temp_dir>
"""
import os
import sys
import json
import argparse


def build_image(temp_dir):
    from PIL import Image, ImageDraw
    import numpy as np
    from image_render import (
        find_font_path, polygon_to_bbox, scale_polygon,
        get_bg_fg_color, fit_text_to_box,
    )

    blocks_path = os.path.join(temp_dir, "image_blocks.json")
    if not os.path.exists(blocks_path):
        print(f"Error: image_blocks.json not found in {temp_dir}", file=sys.stderr)
        return False

    with open(blocks_path, encoding="utf-8") as f:
        data = json.load(f)

    source_path = data["source_path"]
    fmt = data.get("format", "PNG").upper()
    target_lang = data.get("target_lang", "vi")
    blocks = data.get("blocks", [])

    if not os.path.exists(source_path):
        print(f"Error: source image not found: {source_path}", file=sys.stderr)
        return False

    img = Image.open(source_path)
    img_rgb = img.convert("RGB")
    img_w, img_h = img_rgb.size
    img_np = np.array(img_rgb)

    draw = ImageDraw.Draw(img_rgb)
    font_path = find_font_path(target_lang)

    # Sort top-to-bottom for expansion overlap check
    sorted_blocks = sorted(blocks, key=lambda b: polygon_to_bbox(b.get("polygon") or [[0,0]])[1])

    report = {
        "blocks_total": len(blocks),
        "blocks_rendered": 0,
        "blocks_expanded": [],
        "blocks_skipped": [],
    }

    for i, block in enumerate(sorted_blocks):
        bid = block.get("id")
        polygon = block.get("polygon")
        translated = (block.get("translated_text") or "").strip()

        if not polygon or not translated:
            report["blocks_skipped"].append({"id": bid, "reason": "empty_translation"})
            continue

        bx, by, bw, bh = polygon_to_bbox(polygon)
        if bw < 8 or bh < 8:
            report["blocks_skipped"].append({"id": bid, "reason": "bbox_too_small"})
            continue

        # Sample bg/fg from original pixels before any masking
        bg, fg = get_bg_fg_color(img_np, polygon, img_w, img_h)

        # Mask with scaled polygon (covers anti-alias halo)
        scaled_poly = scale_polygon(polygon, img_w, img_h, factor=1.08)
        draw.polygon(scaled_poly, fill=bg)

        # Fit text into bbox
        font, lines, total_h, expanded_h = fit_text_to_box(
            translated, int(bw), int(bh), draw, font_path, target_lang
        )

        render_bh = int(bh)

        if expanded_h > 0:
            extra = expanded_h + 6
            # Expansion safe only if there is room before the next block
            next_top = None
            if i + 1 < len(sorted_blocks):
                _, ny, _, _ = polygon_to_bbox(sorted_blocks[i + 1].get("polygon") or [[0,0]])
                next_top = ny

            if next_top is None or (by + bh + extra) <= next_top - 2:
                exp_y1 = int(by + bh)
                exp_y2 = min(img_h - 1, int(by + bh + extra))
                # Re-sample expansion strip to pick the correct bg color there
                strip = img_np[exp_y1:exp_y2, max(0, int(bx)):min(img_w, int(bx + bw))]
                exp_bg = tuple(int(v) for v in strip.reshape(-1, 3).mean(axis=0)) if strip.size > 0 else bg
                draw.rectangle([int(bx), exp_y1, int(bx + bw), exp_y2], fill=exp_bg)
                render_bh = int(bh + extra)
                report["blocks_expanded"].append({"id": bid, "extra_h_px": extra, "reason": "min_font_overflow"})
                # Re-fit with the extra height
                font, lines, total_h, _ = fit_text_to_box(
                    translated, int(bw), render_bh, draw, font_path, target_lang
                )

        # Draw text: vertically centered, each line horizontally centered
        lhts = [draw.textbbox((0, 0), l, font=font)[3] - draw.textbbox((0, 0), l, font=font)[1] for l in lines]
        line_gap = 2
        actual_h = sum(lhts) + max(0, len(lines) - 1) * line_gap
        cur_y = int(by + (render_bh - actual_h) / 2)

        for line, lh in zip(lines, lhts):
            lw = draw.textbbox((0, 0), line, font=font)[2]
            sx = int(bx + (bw - lw) / 2)
            draw.text((sx, cur_y), line, fill=fg, font=font)
            cur_y += lh + line_gap

        report["blocks_rendered"] += 1

    # Save output in matching format
    ext = os.path.splitext(source_path)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        ext = ".jpg" if fmt in ("JPEG", "JPG") else ".png"
    output_path = os.path.join(temp_dir, "output" + ext)

    if fmt in ("JPEG", "JPG") or ext in (".jpg", ".jpeg"):
        img_rgb.save(output_path, format="JPEG", quality=92)
    else:
        img_rgb.save(output_path, format="PNG")

    print(f"Image output: {output_path} ({os.path.getsize(output_path):,} bytes)")
    print(
        f"Rendered: {report['blocks_rendered']}/{report['blocks_total']} blocks | "
        f"{len(report['blocks_expanded'])} expanded | {len(report['blocks_skipped'])} skipped"
    )

    # Write build report
    report_path = os.path.join(temp_dir, "build_image_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Overlay translated text on image")
    parser.add_argument("temp_dir")
    args = parser.parse_args()

    try:
        success = build_image(args.temp_dir)
    except ImportError as e:
        print(f"Missing dependency: {e}\nRun: pip install Pillow numpy scikit-learn", file=sys.stderr)
        success = False

    sys.exit(0 if success else 1)
