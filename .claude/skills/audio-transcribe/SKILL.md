---
name: tkm:audio-transcribe
description: "Transcribe audio/video to SRT subtitles then revise with Claude's own intelligence — no external LLM API required. Reads context documents to extract domain terms, runs atcli transcribe, then Claude directly corrects mis-transcriptions. Use for meetings, demos, lectures, interviews; especially effective with domain PDFs (product specs, slide decks, terminology glossaries)."
argument-hint: "<file> [--lang vi,en,ja] [--context <docs>] [--output out.srt]"
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
  cli-package: "audio-transcribe-cli"
  cli-pypi: "https://pypi.org/project/audio-transcribe-cli/"
  cli-repo: "https://github.com/sun-asterisk-research/audio-transcribe-cli"
module: specialized-output
triggers: ["transcribe", "subtitles", "SRT", "audio to text", "video captions"]
---

# Audio Transcribe + Revise

A transcript without correction is a first draft — useful but incomplete.
The craftsman who understands the domain knows when the machine wrote the wrong word.
Context documents are the domain knowledge. Claude is the editor.

**Principles:** YAGNI, KISS | Claude as the revision LLM — no external API | Context-first correction

## When to Use

- Transcribing meeting recordings, demos, lectures, interviews
- Audio/video with domain-specific vocabulary (product names, technical terms, proper nouns)
- Multilingual content (Vietnamese + English + Japanese common in Sun Asterisk context)
- When base transcription quality is acceptable but proper nouns are wrong

## When Not to Use

| Situation | Better Tool |
|-----------|-------------|
| Need real-time captions | Use Soniox web interface |
| No `atcli` installed | `pip install audio-transcribe-cli` then re-run |
| Already have clean SRT, no revision needed | `atcli view <file.srt>` directly |
| Context-free revision (no docs, no hints) | Run with `--no-revise` flag |

## Modes

Parse `$ARGUMENTS` to detect mode:

| Argument pattern | Mode |
|-----------------|------|
| Audio/video file + context docs | Full pipeline: context → transcribe → revise |
| Audio/video file only | Transcribe + lightweight revision (language + common patterns) |
| `--no-revise` | Transcribe only, skip revision |
| SRT file path (no audio) | Revision only — skip transcription |

## Pipeline

Load the appropriate workflow reference:

- Full pipeline → `references/full-pipeline.md`
- Revision only → `references/revision-only.md`

## Argument Parsing

Extract from user message:

| Field | Source | Notes |
|-------|--------|-------|
| `AUDIO_FILE` | Positional arg or file path in message | Required (unless revision-only mode) |
| `CONTEXT_DOCS` | `--context` paths or PDF files mentioned | Optional — PDF, TXT, MD supported |
| `CONTEXT_JSON` | `--context-json` path or `*_context.json` file mentioned | Optional — pre-built Soniox context JSON, overrides `CONTEXT_DOCS` for CLI and revision |
| `LANG_HINTS` | `--lang` or language mentioned | Default: `vi,en,ja` |
| `HINTS` | `--hints "..."` or domain context in message | Optional free text |
| `OUTPUT_SRT` | `--output` | Default: `<audio_stem>.srt` |
| `REVISE` | absence of `--no-revise` | Default: true |

If `AUDIO_FILE` missing and no SRT path detected → ask once via `AskUserQuestion`.

## Mesh Connections

This skill composes with the Takumi mesh:

| Need | Route to |
|------|----------|
| Research domain terminology before revision | `/tkm:research <domain>` |

## Requirements

| Requirement | Notes |
|-------------|-------|
| Python 3.11+ | |
| `ffmpeg` on `PATH` | Video input only — `brew install ffmpeg` / `apt install ffmpeg` |
| `SONIOX_API_KEY` | Optional — demo key auto-fetched if absent; paid key gives higher quality |

## Setup Check

`audio-transcribe-cli` is installed automatically by the Takumi kit's `install.sh`
(via `scripts/requirements.txt`). To install manually:

```bash
pip install audio-transcribe-cli
```

Verify:
```bash
atcli --help
```

Optional: set paid Soniox key for `stt-async-v4` quality:
```bash
export SONIOX_API_KEY="your-key"  # or add to .env
```

## References

- `references/full-pipeline.md` — Context extraction → transcribe → revise workflow
- `references/revision-only.md` — Revision-only workflow for existing SRT files
- `references/templates/soniox-context.json` — Template for Soniox context JSON output
