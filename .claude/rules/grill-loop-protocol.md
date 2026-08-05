# Grill Loop Protocol

The relentless interview. When a skill runs with `--grill`, it does not gather requirements
in one batched pass — it walks the decision tree one question at a time, each question shaped
by the last answer, until the design is genuinely understood or the user calls it.

This file is the **single source of truth** for that loop. Skills load it; they never restate
the algorithm. A skill supplies only two things: the **topic/commission** and the **sink**
(where crystallized decisions get recorded — a report section, a `## Validation Log`, etc.).

## When this applies

- ONLY when the consuming skill was invoked with the `--grill` flag.
- `AskUserQuestion` runs in the **main thread only** → grill is inherently single-thread and
  interactive. Never run the grill loop inside a parallel/background sub-agent (e.g. board
  members, fan-out researchers). If the skill also fans out work, grill the commission first
  in the main thread, then hand the resolved decisions to the parallel stage.

## The loop

```
1. SCOUT-FIRST GATE
   If a question is answerable by reading the codebase/docs, READ it — do NOT ask the user.
   (Reuse the skill's existing scout step, e.g. tkm:scan-codebase. Ask only what code can't answer.)

2. BUILD the decision tree
   Seed root nodes from the topic/commission + scout findings. Each node = one open decision.

3. LOOP:
   a. SELECT the next OPEN node whose dependencies (parent answers) are all resolved.
      Walk the tree depth-first along the highest-leverage branch — the decision that most
      constrains everything downstream goes first.
   b. ASK exactly ONE question via AskUserQuestion:
        - 2–4 concrete options
        - mark one "(Recommended)" with a one-line reason
        - the "Other" free-text path is always available
      Asking multiple questions at once is bewildering — never batch under grill.
   c. RECORD the answer immediately to the sink (incremental — see below).
   d. EXPAND: derive the child nodes this answer newly unlocks; prune nodes it made moot.
   e. RE-EVALUATE the stop conditions.
```

## Stop conditions

Stop when **any** of these holds:

| # | Condition | Action on stop |
|---|-----------|----------------|
| a | User signals proceed ("đủ rồi", "build", "proceed", "go", "that's enough") | Stop immediately, honor the user |
| b | No OPEN dependency-ready nodes remain (tree exhausted) | Summarize, confirm proceed |
| c | `grill.diminishingStreak` consecutive answers all took "(Recommended)" | Offer to wrap: "Looks settled — keep grilling or proceed?" |
| d | Questions asked `>= grill.questionCap` | Summarize what's resolved + what's still open, ask to proceed or raise the cap |

On stop via (b), (c), or (d): present the crystallized decisions and explicitly ask the user
to confirm before moving on. Never silently transition from interview to output.

## `--grill` overrides the injected question bound

The `## Plan Context` section injects `questions={min}-{max}` (e.g. `3-8`). That range governs
**batched** validation only. **When `--grill` is active, IGNORE that range and ignore any
"N per tool call" batching.** Grill is one-question-at-a-time and unbounded up to
`grill.questionCap`.

## Incremental recording contract (the "with docs" behaviour)

Record each decision **the moment it crystallizes**, not at the end of the session. The consuming
skill names the sink:

- it appends ONE entry per resolved decision, immediately after the user answers;
- entry carries: the question, the options shown, the chosen answer (verbatim if "Other"),
  and a one-line rationale (why it matters / what it constrains downstream);
- reuse the skill's existing record format — do not invent a parallel one. For create-plan's
  validate flow, that is the `## Validation Log` format in
  `../skills/create-plan/references/validate-question-framework.md`.

This keeps the agreed design written down as it forms, so review at the end is confirmation,
not reconstruction.

## Config

Prose defaults (no runtime parser reads these — they guide the agent; a user may override any
of them inline, e.g. "grill cap 40", and the agent honors it):

| Field | Default | Meaning |
|-------|---------|---------|
| `grill.questionCap` | `25` | Hard safety cap on total questions (stop condition d) |
| `grill.diminishingStreak` | `4` | Consecutive "(Recommended)" answers that trigger the wrap offer (stop condition c) |

## Question format (parity)

One question per `AskUserQuestion` call · 2–4 options · one option tagged "(Recommended)" with a
one-line why · "Other" free-text always available. This mirrors the option format used across
the kit's interviews — keep it consistent with
`../skills/create-plan/references/validate-question-framework.md`.
