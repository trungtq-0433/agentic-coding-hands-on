# Revision-Only Workflow

Triggered when the user provides an SRT file path (no audio/video) — or explicitly asks to revise an existing transcript.

## Inputs

- `SRT_FILE`: path to the existing SRT
- `CONTEXT_JSON`: optional path to a `_context.json` file (Soniox format, from Phase 1 of `full-pipeline.md`) — highest priority source
- `CONTEXT_DOCS`: optional PDF/text reference documents (used when no context JSON available)
- `HINTS`: optional free-text domain hints

## Steps

### Step 1: Gather domain context

**Priority order:**

1. If `CONTEXT_JSON` provided → read the JSON file, extract `context.terms`, `context.text`, `context.general` as `DOMAIN_KNOWLEDGE`. This is the most complete source.
2. If `CONTEXT_DOCS` provided (no JSON) → follow Phase 1 of `full-pipeline.md` to extract `DOMAIN_KNOWLEDGE` and optionally save a new context JSON.
3. If only `HINTS` provided → treat hints as the domain knowledge directly.
4. If none → proceed with Claude's general language knowledge only (still catches BPE artifacts, duplicate words, obvious homophones).

### Step 2: Read the SRT

Use `Read` tool on `SRT_FILE`. Note:
- Total entry count
- Dominant language(s)
- Any immediately obvious systematic errors (e.g. a product name appearing wrong repeatedly)

### Step 3: Revise

Apply the same correction rules as `full-pipeline.md § Phase 3` (including the **sentence coherence check**).

Focus areas for revision-only (no transcription hints were passed, so more corrections likely needed):
- Terms from `context.terms` — match phonetically against STT output, highest value fix
- Tool/product name normalization across all entries
- Split-word BPE artifacts (`Th ì`, `th thì`, `p icker`, etc.)
- Repeated word artifacts (`về về`, `cái cái cái`, `thì thì`)
- Homophones resolved using `context.text` topic description

### Step 4: Write output

Write revised SRT to `<stem>_revised.srt` alongside the original (or `--output` path if specified).
Use `Bash` (not the `Write` tool) — SRT files are often outside the project directory:
```bash
cat > "<REVISED_SRT_PATH>" << 'EOF'
<full corrected SRT content>
EOF
```

Open viewer:
```
atcli view "<REVISED_SRT_PATH>"
```

Report corrections made.
