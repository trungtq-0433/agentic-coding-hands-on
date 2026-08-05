# DOCX Formatting MAP Prompt

You are provided with an input JSON array. Each object contains:
- `id`: element identifier
- `translated_general_text`: the already-translated sentence
- `components`: list of pre-translate runs, each with `text`, `bold`, `italic`, `underline`, `font_size`, `font_color`, `font_name`

Your task: generate a `mapped_components` list for EACH object and return the full array.

**RULES:**

1. **Text Matching (MOST IMPORTANT):**
   The concatenation of all `text` fields in `mapped_components` MUST exactly equal `translated_general_text`. Do not add, remove, or alter any characters.

2. **Attribute Preservation:**
   Preserve relevant attributes from the original `components` (bold, italic, underline, font_color, font_size, font_name). Carry the style that semantically corresponds to each portion of the translated text. Data types must remain unchanged (e.g., `null` stays `null`, boolean stays boolean).

3. **Component Flexibility:**
   You may create a different number of elements in `mapped_components` than in `components`. Group consecutive runs with identical attributes into one element. Distinct formatting (bold/italic/colored) must not bleed into adjacent plain text.

4. **Logical Grouping:**
   The new structure must reflect the same meaning as the original. Preserve emphasis on the correct translated words.

**OUTPUT FORMAT:**

Return a JSON array with one object per input element:
```json
[
  {
    "id": "<same id>",
    "mapped_components": [
      {"text": "...", "bold": true, "italic": null, "underline": null, "font_size": null, "font_color": null, "font_name": null},
      ...
    ]
  }
]
```

Write this array directly to the output file. No explanations, no markdown fences — just the raw JSON array.
