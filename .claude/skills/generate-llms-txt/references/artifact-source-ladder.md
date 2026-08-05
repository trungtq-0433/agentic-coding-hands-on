# Content sources — the four-rung ladder

An llms.txt is only as good as the sources it reads. The skill climbs **docs-first**: higher rungs yield richer files; it drops to a lower rung only when the one above is empty. Never a dead-end — the bottom rung still produces a file, with an advisory to upgrade.

This is where the skill beats a scan-`./docs`-only approach: a project with thin docs still gets a usable file, not an empty index.

## The four rungs

| Rung | Source | Quality | Handled by |
|---|---|---|---|
| **T1** | rebuild-spec output: `docs/system/`, `docs/generated/`, `docs/features/`, `docs/flows/` | Highest — structured, has a feature-list, has architecture | script (skeleton) + LLM (descriptions) |
| **T2** | loose `docs/*.md` + `README` | Ordinary level | script + LLM |
| **T3** | OpenAPI / Swagger spec(s) | Strong for API products | script detects + LLM reads the spec |
| **T4** | codebase deep scan (`--deep` flag) | When T1–T3 are empty | **LLM parallel agents**, NOT the script |

The `build-llms-skeleton.py` script handles T1–T3 (reading static files) and returns `manifest.tier`. T4 is orchestrated by SKILL.md via agents — see the boundary below.

**OpenAPI is content-validated and folded in as supplemental, not just a fallback.** The script accepts a file only if its name starts with `openapi`/`swagger` (any case) **and** its head declares an `openapi: 3.x` / `swagger: 2.0` version — config files and directories are rejected. **Every** valid spec is kept (multi-service monorepos included), deduped by real path, and attached to the `## API` section on T1/T2 too — so an API contract is never dropped just because docs/README also exist. `manifest.openapi_count` reports how many were found. T1 is chosen only when the canonical dirs hold real non-empty markdown, so an empty `docs/system/` never mislabels loose docs as high-quality rebuild-spec output.

## Discovery — follow the ask-expert pattern, don't reinvent

File discovery reuses the spirit of `ask-expert/references/artifact-discovery.md`: probe each layer with sentinel globs, and **read canonical paths from [`_shared/docs-canonical-mapping.md`](../../_shared/docs-canonical-mapping.md)** — do NOT copy its mapping table here (duplication there is a declared breaking-change surface). The docs root is mode-aware: `docs/` (single-lang) or `docs/<lang>/` when `--lang` is given.

## Mapping rebuild-spec → llms.txt sections

On T1, group files into the Sun* internal standard sections (keep this order so every product comes out the same shape):

| llms.txt section | rebuild-spec source |
|---|---|
| H1 + blockquote | `docs/system/overview.md` |
| `## Overview` | `overview.md`, `architecture.md` |
| `## Features` | `docs/generated/feature-list.md`, `docs/features/*` |
| `## API` | `docs/generated/api-map.md`, `route-list.md` |
| `## Flows` | `docs/flows/*` |
| `## Documentation` | catch-all: loose `docs/*.md` not matching the groups above (mostly T2) |
| `## Optional` | changelog, ADR/`docs/decisions/`, deep specs, FAQ |

> The product name (H1 + the name inside the blockquote) comes from the `**Project**:` field in `docs/system/overview.md` — NOT that file's H1 (the rebuild-spec template hardcodes the H1 as `# System Overview`).

## Quality-floor gate

After the LLM fills descriptions, check before writing:

- [ ] Blockquote has no `<TODO>` left.
- [ ] Every link has a real description (no `<TODO desc>` left).
- [ ] No empty section.

**On failure** → either climb to the next source rung for more context, or (if already at T4) write the best-effort file and **append the advisory** — one line, never a dead-end:

```
> Docs are still thin. Run /tkm:rebuild-spec for a fuller, more accurate llms.txt.
```

## The T4 boundary (read carefully — easy to overstep)

Deep scan exists to **rescue** the no-docs case, NOT to replace rebuild-spec:

- T4 fires only when T1–T3 are empty **and** the user passes `--deep` (or confirms, since it is token-heavy).
- Agents deep-read modules → write rich descriptions → **output `llms.txt` directly**.
- **Never** generate spec artifacts (feature-list, entities, technical-spec, …) — that is rebuild-spec's territory. Crossing over duplicates roles and breaks rebuild-spec's contiguity.
- After T4, always append the advisory recommending a rebuild-spec run for a sturdier base next time.

## Why the ladder matters

A scan-`./docs`-only generator has no such ladder: thin docs → thin file, full stop. The T1–T4 ladder + gate guarantees a usable file **at every rung**, and produces a far richer one when rebuild-spec (T1) or OpenAPI (T3) is present — two sources a plain docs scan does not exploit.
