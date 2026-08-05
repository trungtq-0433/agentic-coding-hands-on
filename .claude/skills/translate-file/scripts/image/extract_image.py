#!/usr/bin/env python3
"""
extract_image.py — Save Vision OCR+translate result to image_blocks.json.

The Vision sub-agent calls this after returning polygon + source_text + translated_text
for each text region. This script validates the blocks, reads image dimensions from
Pillow (no need to pass them manually), and writes:

  {temp_dir}/image_blocks.json  — block data used by build_image.py
  {temp_dir}/config.txt         — pipeline metadata (conversion_method=image_native)

Usage:
    python3 extract_image.py save-blocks <temp_dir> <image_path> <target_lang> \\
        --blocks-json '[{"id":0,"polygon":[[x1,y1],[x2,y2],[x3,y3],[x4,y4]],
                         "source_text":"...","translated_text":"...",
                         "role":"paragraph","confidence":"high"}]'
"""
import os
import sys
import json
import argparse


def save_blocks(temp_dir, image_path, target_lang, blocks):
    """Validate blocks, auto-read image dims, write image_blocks.json + config.txt."""
    from PIL import Image

    # --- Validate blocks -------------------------------------------------------
    seen_ids = set()
    errors = []
    for i, block in enumerate(blocks):
        bid = block.get("id")
        if bid is None:
            errors.append(f"Block {i}: missing 'id'")
        elif bid in seen_ids:
            errors.append(f"Block {i}: duplicate id {bid!r}")
        else:
            seen_ids.add(bid)

        poly = block.get("polygon")
        if not poly or len(poly) != 4:
            errors.append(f"Block {i} (id={bid}): polygon must be exactly 4 points, got {poly!r}")

        if not (block.get("source_text") or "").strip():
            errors.append(f"Block {i} (id={bid}): source_text is empty")
        if not (block.get("translated_text") or "").strip():
            errors.append(f"Block {i} (id={bid}): translated_text is empty")

    if errors:
        for e in errors:
            print(f"Validation error: {e}", file=sys.stderr)
        return False

    # --- Read image metadata from Pillow ----------------------------------------
    abs_path = os.path.abspath(image_path)
    try:
        with Image.open(abs_path) as img:
            width, height = img.size
            fmt = (img.format or os.path.splitext(abs_path)[1].lstrip(".")).upper()
    except Exception as e:
        print(f"Error opening image {abs_path}: {e}", file=sys.stderr)
        return False

    os.makedirs(temp_dir, exist_ok=True)

    # --- Write image_blocks.json atomically -------------------------------------
    data = {
        "source_path": abs_path,
        "format": fmt,
        "width": width,
        "height": height,
        "target_lang": target_lang,
        "blocks": blocks,
    }
    blocks_path = os.path.join(temp_dir, "image_blocks.json")
    tmp_path = blocks_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, blocks_path)
    print(f"Saved image_blocks.json: {len(blocks)} block(s) | {width}x{height} {fmt}")

    # --- Write config.txt -------------------------------------------------------
    title = os.path.splitext(os.path.basename(abs_path))[0]
    config_path = os.path.join(temp_dir, "config.txt")
    lines = [
        "conversion_method=image_native",
        "pipeline_version=2",
        f"input_file={abs_path}",
        f"output_lang={target_lang}",
        f"original_title={title}",
    ]
    with open(config_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Written config.txt (pipeline_version=2)")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image translation pipeline helper")
    sub = parser.add_subparsers(dest="cmd")

    p_save = sub.add_parser("save-blocks", help="Save Vision OCR+translate result")
    p_save.add_argument("temp_dir")
    p_save.add_argument("image_path")
    p_save.add_argument("target_lang")
    p_save.add_argument(
        "--blocks-json", required=True,
        help='JSON array: [{"id":0,"polygon":[[x,y],...],"source_text":"...",\n'
             '"translated_text":"...","role":"paragraph","confidence":"high"}]',
    )

    args = parser.parse_args()

    if args.cmd == "save-blocks":
        try:
            blocks = json.loads(args.blocks_json)
        except json.JSONDecodeError as e:
            print(f"Invalid --blocks-json: {e}", file=sys.stderr)
            sys.exit(1)
        success = save_blocks(args.temp_dir, args.image_path, args.target_lang, blocks)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)
