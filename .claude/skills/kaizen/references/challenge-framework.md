# Challenge Framework

Stress-test improvement findings before they become extensions. A plausible-sounding improvement that breaks a working skill is worse than no improvement.

## Universal Challenges

1. Necessity: is this weakness real in practice, or only theoretical? Has it produced a bad outcome?
2. Simpler alternative: can one sentence of clarification fix what you propose to restructure?
3. Existing coverage: does another section, gate, or reference already handle this case?
4. Compliance reality: will the model actually follow the new instruction under long context, or is it one more line to ignore?
5. Update survival: does the improvement reference section headings or structures the next kit release may rename? (`override:` anchors are fragile — prefer `pre`/`post`.)

## Extension-Specific Challenges

| Question | Red Flag | Green Flag |
| --- | --- | --- |
| Instruction conflict? | Extension contradicts a shipped hard gate | Adds on top, never contradicts |
| Scope creep? | Extension turns the skill into a different skill | Sharpens existing behavior |
| Token cost? | Adds eager-loaded prose to every activation | Short, or points to a file read on demand |
| Anchor fragility? | `override:` targeting a long, specific heading | `pre`/`post`, anchor-free |
| Team-specific vs universal? | Universal fix hidden in a local extension (should be a kit issue/PR instead) | Genuinely local convention |

If a finding is a genuine bug in the shipped skill (not a local customization need), recommend filing a kit issue in the report — an extension can patch it locally meanwhile, but the fix belongs upstream.

## Decision Matrix Template

```markdown
| # | Finding | Current | Proposed | Risk | Apply? |
| --- | --- | --- | --- | --- | --- |
| 1 | Vague step 3 | "test as needed" | pre-extension: explicit test command | low | yes |
```

## Risk Scoring

| Critical-risk findings applied | Risk | Action |
| --- | --- | --- |
| 0–2 | Low | Proceed to Benchmark |
| 3–4 | Medium | Benchmark mandatory, even if user offered to skip |
| 5+ | High | Split into multiple kaizen rounds; apply the top 2 first |

Treat a risk as critical when being wrong could make the skill skip a safety gate, produce destructive actions, or silently change its output contract.
