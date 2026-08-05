# Full Pipeline: Context → Transcribe → Revise

## Phase 1: Extract Context from Documents

For each file in `CONTEXT_DOCS`:

1. Read the file using the `Read` tool (PDF, TXT, MD all supported via `Read`).
2. Scan for domain signal — extract these categories:
   - **Proper nouns**: product names, tool names, project names, company names, person names
   - **Technical terms**: acronyms, domain vocabulary, API names, command names
   - **Exact spellings**: capitalization and punctuation that differ from common usage (e.g. "MoMo" not "momo", "VS Code" not "vscode")
   - **Topic context**: one-sentence summary of what the document is about

3. Synthesize into three outputs:
   - `TERMS_SUMMARY`: comma-separated key terms (max 200 chars) — passed as `--hints` to atcli
   - `DOMAIN_KNOWLEDGE`: internal notes (bullets) kept in context for the revision phase
   - `CONTEXT_JSON`: Soniox-format context object (see step 4)

4. Build and save Soniox context JSON:

   Use `templates/soniox-context.json` as the base shape. Fill in:
   - `general`: key-value pairs for setting, topic, language, speaker role, and any other relevant metadata extracted from the docs
   - `terms`: flat list of every proper noun and technical term (exact spelling)
   - `text`: 3–5 sentence natural-language paragraph describing the recording domain — who is speaking, what they are discussing, typical vocabulary used

   Write to `<audio_stem>_context.json` alongside the audio file.
   Use `Bash` (not the `Write` tool) — audio files are often outside the project directory and the `Write` tool may be blocked by privacy hooks for external paths:
   ```bash
   cat > "<CONTEXT_JSON_PATH>" << 'EOF'
   { ... json content ... }
   EOF
   ```
   Store the path as `CONTEXT_JSON_PATH`.

If no context docs provided but `--hints` given:
- Treat hints text as `TERMS_SUMMARY` directly
- Build a minimal context JSON with `terms` populated from the hints string (split on commas) and `text` set to the hints string
- Still save `<audio_stem>_context.json`

---

## Phase 2: Transcribe

Run the CLI with the saved context JSON:

```
atcli transcribe "<AUDIO_FILE>" --context-json "<CONTEXT_JSON_PATH>" --language "<LANG_HINTS>" --no-view [--output "<OUTPUT_SRT>"]
```

`--context-json` loads the Soniox context JSON directly (skips PDF extraction).
For future runs on the same domain, reuse the same `<audio_stem>_context.json` file.

Wait for completion. Confirm the output SRT path from CLI stdout.

**Note on key types:**
- Demo key (`temp:...`, auto-fetched): parallel WebSocket mode, ~27× real-time, stt-rt-v4 model
- Paid key (`SONIOX_API_KEY`): async full-file, stt-async-v4 model (higher base accuracy)

If transcription fails: read the error, diagnose (missing ffmpeg? audio format issue? network?), fix, retry once.

---

## Phase 3: Revise the SRT

Read the output SRT file with the `Read` tool.

### Load correction context

Before revising, activate the domain knowledge from Phase 1:

1. Read `CONTEXT_JSON_PATH` (the `<audio_stem>_context.json` saved in Phase 1).
2. Extract the correction dictionary:
   - `context.terms` → exact spellings of all proper nouns and technical terms
   - `context.text` → natural-language domain description (use to infer correct homophones)
   - `context.general` → setting/topic/speaker metadata (use to resolve ambiguous words)
3. Apply these as the **primary correction authority** — terms in this list override any STT output.

### What to correct

| Priority | Error type | Example | Fix |
|----------|------------|---------|-----|
| 1 (highest) | Term from `context.terms` mis-transcribed | `momos CLI` → `MoMorph CLI` | Use exact spelling from terms list |
| 1 | Product/tool name homophone | `mom 1`, `Momo`, `momop` → `MoMorph` | Match closest term phonetically |
| 2 | Common STT confusion pair | `Cloud record` → `Claude` | Use domain knowledge + topic |
| 2 | Wrong homophone in context | `sinh ra được thuốc` → `sinh ra được code` | Infer from `context.text` topic |
| 3 | Split-word BPE artifact | `Th ì` → `Thì`, `p icker` → `picker` | Merge the split |
| 3 | Duplicate word artifact | `về về` → `về`, `cái cái` → `cái` | Remove duplicate |
| 4 | Trailing/leading noise token | `, thì` → `thì` | Clean up |
| 4 | Wrong mid-sentence capitalization | `Bắt đầu thì` → `bắt đầu thì` | Fix case |

### Sentence coherence check

After applying term corrections, re-read each changed cue:
- Does the sentence still make sense in context of surrounding cues?
- If a term replacement makes the sentence unintelligible, flag it and prefer the closest sensible alternative.
- Do NOT force a term from the list into a context where it breaks meaning — only correct when phonetic similarity is strong AND the topic context supports it.

### What to preserve

- **All timestamps** — bit-for-bit identical, never touch these
- **All index numbers** — never renumber entries
- **Natural speech markers** — fillers (ờ, uh, hmm, à), hesitations, genuine repetitions
- **Foreign-language segments** — if speaker switches language, keep it
- **Background speech** — noise-only cues are fine to keep

### What NOT to do

- Do not rewrite sentences to be grammatically "cleaner"
- Do not translate between languages
- Do not remove or add entries
- Do not change speaker's sentence structure
- Do not correct a word simply because it sounds informal — only fix actual mis-transcriptions

### Revision execution

Work through the SRT block by block. For blocks with no issues, leave them unchanged.
Build the full corrected SRT text in memory, then write it in one operation using `Bash` (not the `Write` tool — same privacy-hook reason as above):

```bash
cat > "<REVISED_SRT_PATH>" << 'EOF'
<full corrected SRT content>
EOF
```

- If `--output` was specified: write to that path
- Otherwise: write to `<stem>_revised.srt` alongside the original

---

## Phase 4: Report and Open Viewer

After writing the revised SRT:

1. Report a summary:
   - Number of corrections made (approximate count by category)
   - Notable fixes (e.g. "MoMo corrected 12×, CLI fixed 3×, split words merged 5×")
   - Any uncertain corrections flagged

2. Open viewer:
   ```
   atcli view "<REVISED_SRT_PATH>"
   ```
