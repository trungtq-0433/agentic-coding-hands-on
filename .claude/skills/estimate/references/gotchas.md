# Gotchas & Error Recovery

## Parser Edge Cases

- **Unicode / Japanese filenames** → parser may fail with "File not found" on non-ASCII paths depending on OS locale. If this happens, check for an ASCII-named copy or rename the file before parsing. Common with Japanese PDF attachments.
- **Tesseract OCR dependency** → `--pdf-ocr` requires `tesseract` CLI with language packs. Check availability before attempting OCR:
  ```bash
  which tesseract && tesseract --list-langs || echo "NOT_INSTALLED"
  ```
  Install if missing: `sudo apt install tesseract-ocr tesseract-ocr-jpn` (Debian/Ubuntu)
  If tesseract is unavailable, skip OCR and go directly to multimodal fallback.
- **PDF scanned images** → fallback to OCR with `scripts/parse-document.py --ocr`
- **Excel merged cells** → handled automatically by ExcelParser (openpyxl); use `--merge` flag to combine multi-sheet output
- **Multi-document input** → content is merged, not processed separately
- **Empty/corrupted files** → parser returns `{"error": "..."}`, check before proceeding
- **Large Excel files (>50KB JSON output)** → Read tool will fail on full output. Extract in chunks:
  ```bash
  python3 scripts/parse-document.py <file> --pretty 2>&1 | python3 -c "
  import json, sys; data = json.load(sys.stdin)
  lines = data['files'][0]['content'].split('\n')
  print('\n'.join(lines[START:END]))
  "
  ```
  Process in ~150-line chunks. Do NOT attempt Read tool on parser output >25K tokens.
- **Image-heavy PDFs (PowerPoint exports, diagrams, scanned docs)** → parser extracts text layer only, missing visual content.
  Check `content_density` in parser output metadata. If `is_sparse: true` (< 50 words/page), use Read tool for visual reading:
  ```bash
  # Multimodal fallback — Claude reads pages visually
  Read tool: file.pdf pages="1-10"
  Read tool: file.pdf pages="11-20"
  ```
  Or use `--pdf-ocr` flag for automated OCR: `parse-document.py file.pdf --pdf-ocr --ocr-lang jpn`
  Combine visual/OCR extraction with parser text output for complete content.
- **GitHub URLs require `gh` CLI** → must be installed and authenticated (`gh auth login`)
- **Web URLs** → if `requests`/`html2text` not installed, parser returns stub → use WebFetch tool
- **Private repos** → GitHub parser respects `gh` CLI auth, can access private issues/discussions

## Error Recovery

If a step fails during the estimation workflow:

| Failure | Recovery |
|---------|----------|
| Parser returns `{"error": ...}` | Check file path/permissions. Try `--ocr` for PDFs. For Excel, try `--merge`. If still fails, ask user for alternative format. |
| Parser output too large for Read tool | Use chunked bash extraction (see above). Never force-read >25K tokens. |
| `render-estimate.py` fails | Validate JSON with `validate-estimate.py` first. Fix schema errors, then re-render. |
| HTML post-render check fails | Re-run `render-estimate.py -f html` alone. If persistent, deliver MD+Excel only, note HTML issue. |
| `gh` CLI not authenticated | Ask user to run `gh auth login`. Fall back to WebFetch for public URLs. |
| Missing Python dependencies | Use `pip install -e ".[parsers,output]"` to install all optional deps. |
