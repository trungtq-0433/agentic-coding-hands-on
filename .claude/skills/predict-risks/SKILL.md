---
name: tkm:predict-risks
description: "Five voices examine the plan before the first cut — expert personas debate architectural, security, performance, and UX risks in proposed changes. Use before major features or anything that cannot easily be undone."
argument-hint: "<change> [--level low|medium|high|max] [--files <glob>]"
metadata:
  author: takumi-agent-kit
  attribution: "Multi-persona prediction pattern adapted from autoresearch by Udit Goenka (MIT)"
  license: MIT
  version: "1.0.0"
module: testing-code-quality
triggers: ["risks", "what could go wrong", "before major change", "predict failure", "expert review of plan"]
---

# Reading the Grain

Before the craftsman cuts, they read the wood.
They run a hand along the surface, feel where the grain runs true and where it twists,
where a cut would split cleanly and where it would shatter.

The material does not announce its weaknesses — it conceals them.
Only careful examination before the first cut reveals what failure is hiding inside the proposal.

## When to Read the Grain

- A feature that is large, or where a wrong cut costs dearly, before it goes in
- A refactor or architecture shift big enough to leave a mark
- Two or more technical routes on the table, none yet chosen
- A design whose assumptions deserve to be leaned on before they bear weight

## When Not to Use This Skill

- Small, low-stakes changes (send bugs to `tkm:debug-code`, settled tasks to `tkm:create-plan`)
- Work already signed off with no design questions left open
- Dependency bumps that leave the API untouched

---

## Processing Level

Accepts `--level low|medium|high|max` (default: `medium`).
See `_shared/processing-levels.md` for global semantics.

| Level | Voices | Depth | Sub-agents | Output |
|-------|--------|-------|-----------|--------|
| `low` | 3 (Arch, Sec, Devil) | Quick | None | Condensed |
| `medium` *(default)* | All 5 | Standard | None | Full report |
| `high` | All 5 | Deep + code evidence | None | Full + confidence tags |
| `max` | All 5 | Deep | Parallel | Full + parallel debate |

> `--level low` drops the Performance and UX voices (least critical for quick spot checks) and keeps Architect, Security, Devil's Advocate.

## Five Voices

Five trades gather at the bench, each sizing up the same proposal through the lens of their own craft.
They keep their counsel to themselves while they work — the debate is only worth holding because each voice arrives at its verdict alone.

| Voice | Domain | What They Ask |
|---------|-------|----------------|
| **Architect** | System design, scalability, coupling | Does this fit the architecture? Will it scale? What new coupling does it introduce? |
| **Security** | Attack surface, data protection, auth | What can be abused? Where is data exposed? Are auth boundaries respected? |
| **Performance** | Latency, memory, queries, bundle size | What is the latency impact? N+1 queries? Memory leaks? Bundle bloat? |
| **UX** | User experience, accessibility, error states | Is this intuitive? What does the error state look like? Accessible on mobile? |
| **Devil's Advocate** | Hidden assumptions, simpler alternatives | Why not do nothing? What is the simplest alternative? Which assumption could be wrong? |

---

## The Debate Protocol

1. **Take in the proposal** — the change or feature as the argument describes it
2. **Open the affected code** when paths are given (grep toward the areas it touches)
3. **Each voice forms its own verdict** — sealed off from the others while this stage runs
4. **Find the common ground** — where every voice, or four of five, lands in the same place
5. **Find the fault lines** — where the voices genuinely pull against each other
6. **Settle each fault line** — judge which concern carries more weight and rule on it
7. **Deliver the call** — GO / CAUTION / STOP, each paired with what to do about it

---

## Report Format

```
## Grain Reading: [proposal title]

## Verdict: GO | CAUTION | STOP

### Where All Voices Agree
- [Point 1 — what they all agree on]
- [Point 2]

### Conflicts & Resolutions

| Topic | Architect | Security | Performance | UX | Devil's Advocate | Resolution |
|-------|-----------|----------|-------------|-----|-----------------|------------|
| [Issue] | [View] | [View] | [View] | [View] | [View] | [Recommendation] |

### Risk Summary

| Risk | Severity | Mitigation |
|------|----------|------------|
| [Risk description] | Critical/High/Medium/Low | [Concrete action] |

### Recommendations
1. [Action item — rationale]
2. [Action item — rationale]
3. [Action item — rationale]
```

---

## Verdict Levels

| Verdict | Meaning |
|---------|---------|
| **GO** | All voices aligned, no critical risks, proceed with confidence |
| **CAUTION** | Concerns exist but are manageable — mitigations identified, proceed carefully |
| **STOP** | Critical unresolved issue found — needs redesign or more information before proceeding |

### What Forces a STOP (any one is sufficient)
- Security voice identifies auth bypass or data exposure with no viable mitigation
- Architect identifies fundamental design incompatibility requiring significant rework
- Performance voice identifies unacceptable latency or query explosion with no workaround
- Devil's Advocate exposes a false assumption that invalidates the entire approach

---

## How This Connects to Other Skills

| Next Step | Skill | How |
|---------------|-------|-----|
| Create implementation blueprint | `tkm:create-plan` | Attach Recommendations as constraints to planner |
| High-risk feature forging | `tkm:takumi` | Reference CAUTION/STOP items as acceptance gates |

---

## Example Invocations

```
/tkm:predict-risks "Add WebSocket support for real-time notifications"
/tkm:predict-risks "Migrate authentication from JWT to session cookies"
/tkm:predict-risks "Add multi-tenancy to the database layer"
/tkm:predict-risks "Replace REST API with GraphQL" --files src/api/**/*.ts
```
