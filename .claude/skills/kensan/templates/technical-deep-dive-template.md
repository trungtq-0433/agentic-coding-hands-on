# 研鑽 Deep Dive — {{topic}} — {{date}}

<!--
  This is a TECHNICAL REPORT, not a summary. A teammate should finish it able to
  explain the thing on a whiteboard AND try it — not just recognise the headline.

  Fill rules:
  - Every claim carries a link. No source → drop the claim. NEVER invent numbers,
    APIs, or quotes; if a primary doesn't state it, say "not stated".
  - "How it works" MUST come from PRIMARY sources you actually read deeply (the
    paper's method section, the repo's core code + README, the official blog),
    not from headlines or recaps. Explain the MECHANISM, step by step.
  - Show, don't assert: include a diagram, a worked example/trace, and real
    code/commands/config copied from the primary (with its link).
  - Quotes are verbatim + attributed to a public handle + linked. Mark X / Reddit
    "best-effort".
  - Go deep, do NOT pad. If a section's signal is genuinely thin, say so in one
    line ("no independent benchmark yet") rather than filling it with fluff.
  - Length follows substance: a real mechanism needs several paragraphs, not bullets.
-->

## TL;DR
- **What it is:** {{one line}}
- **Why it matters now:** {{the shift it represents / what it unblocks}}
- **The mechanism in one sentence:** {{the core idea, technically}}
- **Most useful takeaway:** {{what you'd actually do with this}}

## Context — why this, why now
{{2–4 sentences: the problem it solves, what came before, what changed to make it
matter this week. Link the trigger (release/paper/thread).}}

## How it works (the core — go deep here)

### The mechanism, step by step
{{The heart of the report. Walk through HOW it works in order, as if teaching it.
Several paragraphs. Define each non-obvious term the first time. For an algorithm:
inputs → each transformation → output, and WHY each step exists. For a system:
the request/data path end to end. Cite the primary for each non-obvious claim.}}

### Architecture / data flow
```
{{ASCII or mermaid diagram of the components and how data/control flows between
them. A reader should grasp the shape at a glance. Label the parts referenced above.}}
```

### Worked example / trace
{{One concrete end-to-end example: a real input, the steps it goes through, the
output. Use actual values/commands from the primary where possible. This is what
turns "I read about it" into "I understand it".}}

### Key parameters & design choices
- {{parameter/knob}}: {{what it controls, default, when to change}} — [{{src}}]({{url}})
- **Why built this way:** {{the design rationale / tradeoff the authors chose, in their words where possible}}

- Primary sources read (deeply): [{{paper §method / repo file / blog}}]({{url}}) · [{{…}}]({{url}})

## Using it / reproducing
{{The minimum to actually run or apply it: install/setup, the key command(s) or
code snippet (copied from the primary, linked), expected output. If it's a paper
with no code, give the recipe to reproduce the core result or apply the idea.}}
```
{{real commands / code / config — attributed}}
```

## Evidence, benchmarks & methodology
- **Claimed:** {{result}} — measured how: {{benchmark/dataset/setup}} — [{{source}}]({{url}})
- **Numbers:** {{the actual figures, not "improved a lot"}} — [{{source}}]({{url}})
- **vs {{alternative}}:** {{dimension-by-dimension tradeoff}} — [{{source}}]({{url}})
- **Hype check:** {{what is claimed vs what is actually measured; sample size, cherry-picking, list-price-vs-real-cost, etc.}}

## Limitations, gotchas & failure modes
- {{where it breaks / what it can't do / known issues from the primary or issues tracker}} — [{{src}}]({{url}})
- {{operational gotcha a practitioner would hit}} — [{{src}}]({{url}})

## Community pulse
### Consensus
- {{shared view}} — "{{verbatim quote}}" — [{{@handle / HN / repo#}}]({{url}})

### Debate / skepticism
- {{contested point}}: {{side A}} vs {{side B}} — [{{quote+link}}]({{url}}) / [{{quote+link}}]({{url}})

### Per-platform
- **HN:** {{1-line gist}} · **GitHub:** {{gist}} · **Reddit (best-effort):** {{gist}} · **X (best-effort):** {{gist}}

## What to learn / try
- **Read:** [{{primary doc/paper §}}]({{url}}) — {{why, and which section}}
- **Try:** [{{repo / snippet}}]({{url}}) — {{the concrete thing you'll run and what you'll learn}}
- **Team exercise:** {{a concrete applied task tied to our work}}

## Open questions
- {{unresolved technical/operational question worth tracking next run}}

## Sources
- Primary (read deeply): {{links + which section/file}}
- Discussion: {{links}}
