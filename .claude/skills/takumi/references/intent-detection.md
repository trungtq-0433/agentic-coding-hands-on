# Reading the Material

The craftsman examines what is brought to the workshop before choosing a discipline.
This is the first act of mastery — understanding the work before touching it.

## Detection Algorithm

```
FUNCTION readMaterial(input):
  # Priority 1: Explicit discipline flags (override all)
  IF input contains "--fast": RETURN "fast"
  IF input contains "--parallel": RETURN "parallel"
  IF input contains "--auto": RETURN "auto"
  IF input contains "--no-test": RETURN "no-test"

  # Priority 2: Blueprint path detection
  IF input matches path pattern (./plans/*, plan.md, phase-*.md):
    RETURN "code"

  # Priority 3: Keyword detection (case-insensitive)
  keywords = lowercase(input)

  IF keywords contains ["fast", "quick", "rapidly", "asap"]:
    RETURN "fast"

  IF keywords contains ["trust me", "auto", "yolo", "just do it"]:
    RETURN "auto"

  IF keywords contains ["no test", "skip test", "without test"]:
    RETURN "no-test"

  # Priority 4: Complexity detection
  features = extractFeatures(input)  # comma-separated or "and"-joined items
  IF count(features) >= 3 OR keywords contains "parallel":
    RETURN "parallel"

  # Default: full craft, full control
  RETURN "interactive"
```

## Feature Extraction

Detect multiple distinct pieces from natural language:

```
"implement auth, payments, and notifications" → ["auth", "payments", "notifications"]
"add login + signup + password reset"         → ["login", "signup", "password reset"]
"create dashboard with charts and tables"     → single piece (dashboard)
```

**Parallel trigger:** 3+ distinct features = parallel discipline

## Work-Type Detection

Classify the work **before** discipline routing and **before** any `F###` reservation claim.

| Type | Meaning |
|------|---------|
| `feature` | Product or system behavior: code that ships, a screen, an API, a data model, a persistent change to the system. Stage 1.5 runs normally. |
| `deliverable` | One-off artifact handed to the user: an Excel/CSV/report/slide/document, an ad-hoc analysis, a one-shot script **not committed to the repo**. Skip Stage 1.5 entirely — no `F###`, no reservation. |
| `ambiguous` | No clear cue on either side. Block immediately via `AskUserQuestion` (ONE question: "product feature or one-off deliverable?"). BLOCKING in ALL disciplines including `--auto`. |

### Classification Cues

**Deliverable cues** — artifact is handed to the user and NOT committed to the repo:
- Phrasing: "tạo/làm cho tôi 1 file …", "generate/export a report/slide/excel/document", "write me a script to …" with no mention of integrating into the app.
- Output is a file or document artifact: excel, csv, pdf, slide deck, report, analysis output.
- No reference to app behavior, user flows, screens, APIs, database persistence, or the codebase.

**Feature cues** — any of these signals → `feature`, no ask:
- Names app behavior, screens, user flows, API endpoints, database models, or persistence.
- Phrasing: "thêm tính năng", "add", "implement", "integrate", "build a page", "create an endpoint".
- The artifact is committed to the repo (a script, config, or source file that lives in the codebase = part of the system; docs-prose excluded — see Committed-to-repo rule).
- Refactoring, restructuring, renaming, or deleting committed source code — changes to the codebase itself are feature-class work regardless of whether user-visible behavior changes.

**Tie-break rule (feature precedence):** ANY feature cue present → classify `feature`. No ask.
`ambiguous` = NO clear cue on EITHER side.

**Committed-to-repo rule:** A script, config, or SOURCE file that gets committed to the repo is a
feature cue — it lives in the system. A documentation/prose file committed to `docs/` is NOT a
feature cue on its own (no app behavior changes — writing user guides into `docs/` stays
`deliverable` unless another feature cue fires). `deliverable` = handed-to-user artifact, not
committed (excel/slide/report/analysis).

**Mixed task:** Feature + attached deliverable in one request → classify `feature`. The deliverable is produced during Forge as a plan output; no separate `F###`.

### Rule

Classification runs at Stage 0, BEFORE discipline routing's effects on Stage 1.5, BEFORE any reservation claim.
`ambiguous` → `AskUserQuestion` is BLOCKING in all disciplines including `--auto`
(cite F13 precedent: scope-category gaps block even in auto; classification defines scope).

## Discipline Behaviors

| Discipline | Skip Study | Skip Temper | Rest Points | Auto-Approve | Parallel Forge |
|------------|------------|-------------|-------------|--------------|----------------|
| interactive | ✗ | ✗ | **Yes (pauses)** | ✗ | ✗ |
| auto | ✗ | ✗ | **No (continuous)** | ✓ (score≥9.5) | ✓ (all stages) |
| fast | ✓ | ✗ | Yes (pauses) | ✗ | ✗ |
| parallel | Optional | ✗ | Yes (pauses) | ✗ | ✓ |
| no-test | ✗ | ✓ | Yes (pauses) | ✗ | ✗ |
| code | ✓ | ✗ | Yes (pauses) | Per blueprint | Per blueprint |

**Rest Points:** Human approval checkpoints between major stages (see `workflow-steps.md`).
- All disciplines EXCEPT `auto` pause at rest points for human approval.
- `auto` is the only discipline that runs continuously without stopping.

## Examples

```
"/tkm:takumi implement user auth"
→ Discipline: interactive (default, pauses at rest points)

"/tkm:takumi plans/260120-auth/phase-02-api.md"
→ Discipline: code (blueprint path detected, pauses at rest points)

"/tkm:takumi quick fix for the login bug"
→ Discipline: fast ("quick" keyword, pauses at rest points)

"/tkm:takumi implement auth, payments, notifications, shipping"
→ Discipline: parallel (4 features, pauses at rest points)

"/tkm:takumi implement dashboard --fast"
→ Discipline: fast (explicit flag, pauses at rest points)

"/tkm:takumi implement everything --auto"
→ Discipline: auto (NO PAUSES, all stages continuous)

"/tkm:takumi implement dashboard trust me"
→ Discipline: auto ("trust me" keyword, NO PAUSES)
```

**Note:** Only `--auto` flag or "trust me"/"auto"/"yolo" keywords enable continuous execution.

## Conflict Resolution

When multiple signals are detected, priority order:
1. Explicit flags (`--fast`, `--auto`, etc.)
2. Blueprint path detection
3. Keywords in the input
4. Feature count analysis
5. Default (interactive)
