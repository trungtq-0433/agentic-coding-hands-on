# Vision Sub-Agent Prompt — Image OCR + Translate

This file is the single source of truth for the Vision sub-agent prompt used in the
image translation flow. Referenced by `SKILL.md` Step 2 ("Image Files — Dedicated Flow").

---

## Prompt Template

(Replace `{file_path}`, `{target_lang}`, `{temp_dir}`, `{baseDir}` at dispatch time.)

---

Read the image at `{file_path}`.

For every visible text region:

1. Draw a tight 4-point polygon in **absolute pixel coordinates** around the region
   (top-left → top-right → bottom-right → bottom-left).
   **Group multi-line paragraphs into one polygon** — do NOT emit one polygon per line.
   Use the image's actual pixel dimensions to estimate coordinates.

2. Return the `source_text` exactly as it appears in the image.

3. Return `translated_text` in **{target_lang}**.
   Keep the translation **concise enough to fit roughly the same physical area** as the source.
   Prefer shorter synonyms; drop filler words; avoid expanding abbreviations.
   Do NOT pad or add explanations.

4. Label the `role`: `heading`, `paragraph`, `caption`, or `label`.

5. Assign a `confidence`: `high` (text clearly legible), `medium` (partially legible),
   or `low` (best guess from stylized/blurred text).

6. **Skip** pure numbers, standalone dates, bullet glyphs (•, ─, etc.), and decorative symbols.

Output **JSON only** — no prose, no markdown fences:

```
[
  {
    "id": 0,
    "polygon": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]],
    "source_text": "...",
    "translated_text": "...",
    "role": "heading|paragraph|caption|label",
    "confidence": "high|medium|low"
  },
  ...
]
```

After producing the JSON array, run these commands sequentially:

```bash
{baseDir}/../.venv/bin/python3 {baseDir}/scripts/image/extract_image.py save-blocks \
  "{temp_dir}" "{file_path}" "{target_lang}" --blocks-json '<json_array>'
```

Where `<json_array>` is the JSON you just produced (single-line, properly escaped for shell).

---

## Notes for the sub-agent

- If the image contains no readable text at all, output `[]` (empty array) — do NOT invent blocks.
- Polygon coordinates are estimates; ±10 px accuracy is acceptable.
- For dense layouts (e.g. slide with many text boxes), emit one block per distinct logical text unit.
- Do not translate content inside code fences, URLs, or mathematical formulae — leave `translated_text` equal to `source_text` for those.
