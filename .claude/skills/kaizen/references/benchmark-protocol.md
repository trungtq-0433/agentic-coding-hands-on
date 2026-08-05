# Benchmark Protocol — Blind A/B Skill Evaluation

How kaizen proves an improvement (or compares two skills) instead of asserting it.

## 1. Eval Cases

Location: `.claude/skills/<dir>/extensions/evals/cases.md` + `rubric.md` (user-owned, survives kit updates, reused across kaizen rounds).

- If both files exist → load and reuse. Users may add/edit cases freely.
- If missing → generate from the skill itself using `references/eval-templates.md`:
  - 3–5 cases; every documented mode/flag gets at least one case
  - Derive inputs from `description` triggers, `argument-hint`, and workflow phases
  - Each case = realistic user request the skill should handle, plus expected-behavior notes (which gates fire, what output shape, what must NOT happen)
- Persist generated files before running anything.

## 2. Cost Gate (MANDATORY)

Before spawning any subagent, present:

```
Benchmark estimate: {cases} cases × 2 variants × 1 run ≈ {cases*2} subagent runs
+ {cases} judge runs. Rough token cost: ~{(cases*3)*30}k tokens. Proceed?
```

- Interactive: `AskUserQuestion` (Run benchmark / Skip → static analysis only)
- `--auto`: proceed only if ≤ 5 cases (the default ceiling); above that, still ask
- `--fast`: never reaches this protocol

## 3. Variant Setup

- **Improve mode**: baseline = skill as-is. Candidate = skill + proposed extensions. Materialize candidate by including the proposed extension content inline in the candidate subagent's prompt (do NOT write extension files before the verdict).
- **Compare mode**: variant A = target skill, variant B = alternative implementation's SKILL.md content.

## 4. Run

For each case × variant, spawn a subagent with this shape:

```
Task: Act according to the following skill instructions, then handle the user request.
<skill-instructions>{SKILL.md content (+ candidate extensions if variant B/improve-candidate)}</skill-instructions>
<user-request>{case input}</user-request>
Constraints: DO NOT execute irreversible actions (no file writes outside /tmp, no git push,
no network mutations). If the skill calls for them, describe the exact action instead.
Return: your full response as the skill would produce it.
```

- Run variants in parallel where resources allow.
- Skills with write actions → require subagent worktree isolation.
- A variant run that errors → retry once; second failure → mark case `no-result`, continue.

## 5. Blind Judging

One judge subagent per case. The judge receives outputs labeled only **A** and **B** — randomize which variant is A per case, never reveal which is baseline.

```
Task: Score two responses to the same request against this rubric.
<rubric>{rubric.md content}</rubric>
<request>{case input}</request>
<expected>{case expected-behavior notes}</expected>
<response-A>{...}</response-A>
<response-B>{...}</response-B>
Return per dimension: score A (1-5), score B (1-5), one-line rationale. Then overall winner: A | B | tie.
```

## 6. Aggregate & Decide

| Outcome | Decision |
| --- | --- |
| Candidate wins majority of cases | Apply extension |
| Tie | Apply only if candidate is also cheaper (shorter injected content) |
| Baseline wins | Do NOT apply; record finding + judge rationales in report |
| ≥ half cases `no-result` | Benchmark inconclusive — fall back to static analysis, note in report |

Verdict table for the report:

```markdown
| Case | Baseline | Candidate | Winner | Note |
| --- | --- | --- | --- | --- |
Overall: candidate 3/4 wins → APPLY
```

## Failure Handling

- Judge returns unparseable output → re-ask once with stricter format; then mark case tie
- Eval generation produces < 3 usable cases → ask user to supply cases or accept reduced confidence
- Never let benchmark failure block Deliver of an analysis report — degrade gracefully
