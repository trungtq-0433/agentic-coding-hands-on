# Evidence Artifacts — the Takumi Quality Gate

A craftsman does not say *"it is done."* He shows the grain, the joint, the
finish under light. Takumi's Deliver/ship/fix-bug flows make "done" mean
**evidence, not a promise**: each stage leaves a structured artifact, and a
deterministic validator reads those artifacts before any commit or push.

This document is the **contract** for the three artifacts. It is descriptive —
the **single source of truth is the validator code** at
`claude/hooks/lib/evidence-validator.cjs`. There is no `ajv`, no standalone
`.json` schema file, nothing to drift out of sync. If the doc and the code ever
disagree, the code wins, and the doc is the bug.

## Where the artifacts live

Every artifact is written into the **plan's own evidence directory**:

```
{plan}/evidence/
├── study-context.json        # what we set out to build (the brief)
├── temper-results.json       # what survived the fire (commands + outcomes)
└── inspection-verdict.json   # the master's inspection (review + adversarial)
```

The calling skill already knows `{plan}` from its plan context. It resolves the
absolute `{plan}/evidence/` path **once** and passes it explicitly to every
subagent. Nothing re-resolves a plan from the session or the branch — there is
no resolution to bypass, and no two subagents can race to a different directory.

When stages run in parallel, each instance writes a per-instance file
(`temper-results-<label>.json`); the validator aggregates every
`temper-results*.json` it finds.

---

## `study-context.json` — the brief

**Emitter:** the gated skill, at its scoping step (takumi `Study`; ship/fix-bug
at the equivalent "what am I changing and why" point), once the work is scoped.

```json
{
  "task": "Add a code-enforced evidence gate to takumi Deliver",
  "mode": "auto",
  "acceptanceCriteria": [
    "gate blocks a faked-evidence ship",
    "gate passes a real SEALED ship"
  ],
  "touchpoints": [
    "claude/hooks/lib/evidence-validator.cjs",
    "claude/skills/takumi/SKILL.md"
  ],
  "blastRadius": ["takumi Deliver", "ship pre-push", "fix-bug commit"],
  "contracts": [
    "node claude/skills/_shared/lib/evidence-gate.cjs --evidence-dir <abs> --stage hard"
  ]
}
```

| Field | Anti-faking intent |
|-------|--------------------|
| `task` | One sentence of what is being built. An empty brief = nothing to inspect against. |
| `mode` | The workflow mode (`auto`, `interactive`, …) — records how much human gating applied. |
| `acceptanceCriteria` | The list the inspection must later prove **covered**. Empty ⇒ "done" is unfalsifiable ⇒ rejected. |
| `touchpoints` | The files actually touched. Grounds the regression check in real blast radius. |
| `blastRadius` | The behaviors that could break — the reviewer must walk these. |
| `contracts` | Public surfaces (commands, signatures, schemas) that must stay stable unless called out. |

---

## `temper-results.json` — what survived the fire

**Emitter:** the `tester` subagent supplies **raw command runs** (the command,
its real exit code, a one-line summary) into the evidence dir. The **validator
code** (`buildTemperResults`) assembles the strict JSON — a small model is never
asked to hand-write schema-valid JSON, so `exitCode` is always a real integer,
never a string the agent typed.

```json
{
  "commands": [
    {
      "command": "node --test claude/hooks/lib/__tests__/evidence-validator.test.cjs",
      "exitCode": 0,
      "status": "pass",
      "summary": "evidence-validator matrix green",
      "ts": "2026-06-16T05:00:00.000Z"
    }
  ]
}
```

| Field | Anti-faking intent |
|-------|--------------------|
| `command` | The exact command run. No command ⇒ no proof a test was run at all. |
| `exitCode` | Must be a real **integer**. A string `"0"` is the classic fake — the validator blocks it (the code that constructs the file guarantees an int). |
| `status` | `pass` \| `fail` \| `skipped`. Any `fail` at a hard stage blocks — you cannot ship over a red test. |
| `summary` | A one-line human-readable outcome. Empty/missing ⇒ blocks (a blank summary hides a failure). |
| `ts` | ISO timestamp of the run — records *when* the fire was lit. |

A hard stage requires **at least one** command with `status: "pass"`. An empty
`commands` array is not "all green" — it is "nothing was tempered" ⇒ block.

---

## `inspection-verdict.json` — the master's inspection

**Emitter:** the `reviewer` subagent (and the `review-code` skill) — a **single
writer**. It merges the ordinary review dimension and the adversarial dimension
into one verdict. A partial write is rejected.

```json
{
  "score": 9,
  "criticalCount": 0,
  "decision": "SEALED",
  "acceptanceCovered": ["gate blocks faked ship", "gate passes SEALED ship"],
  "regressionChecked": ["takumi Deliver unaffected", "hook suite green"],
  "contractStatus": "OK",
  "refuted": [],
  "unproven": [],
  "reachableRegressions": [],
  "findings": [
    {
      "severity": "Critical",
      "category": "Security",
      "location": "claude/hooks/lib/evidence-validator.cjs:143",
      "summary": "extra-key check runs before the null-artifact guard",
      "disposition": "Reject"
    }
  ]
}
```

| Field | Anti-faking intent |
|-------|--------------------|
| `score` | Advisory only. A high score **never** seals by itself — `decision` does. Score 10 + `decision: BLOCKED` still blocks. |
| `criticalCount` | Open critical issues. `SEALED` requires this to be `0`. |
| `decision` | `SEALED` \| `REWORK` \| `BLOCKED`. Only `SEALED` passes a hard stage. |
| `acceptanceCovered` | Which acceptance criteria the inspection actually proved. Must be non-empty at a hard stage, and must **cover every criterion in the brief** — each `study-context.json` `acceptanceCriteria` entry has to be echoed (its text contained) by some `acceptanceCovered` entry, or the gate blocks and names the uncovered criterion. |
| `regressionChecked` | The blast-radius items the reviewer walked. Must be non-empty at a hard stage — empty means nothing was verified, and blocks. |
| `contractStatus` | `OK` \| `CHANGED` \| `BROKEN` \| `UNKNOWN`. `UNKNOWN` at a hard stage blocks — an unexamined contract is not a passed one. |
| `refuted` | Claims the adversarial pass **disproved**. Non-empty ⇒ block. |
| `unproven` | Claims asserted but not demonstrated. Non-empty at a hard stage ⇒ block. |
| `reachableRegressions` | Regressions shown to be reachable. Non-empty ⇒ block. |
| `findings` | Optional. Per-finding detail from the adversarial pass — see "`findings[]` — the machine-checked location" below. |

`SEALED` is earned only when `criticalCount == 0` **and** `refuted`, `unproven`,
`reachableRegressions` are all empty **and** `contractStatus != UNKNOWN` **and**
`acceptanceCovered` and `regressionChecked` are both non-empty (something was
actually proven and the blast radius was actually walked).

### `findings[]` — the machine-checked location

A prose checklist saying "cite `file:line`" is not enforcement — nothing stops
a reviewer from writing "see above" and moving on. `findings[]` turns that
checklist item into a field the validator can actually check.

**Schema version, by presence, not a counter:** a verdict with no `findings[]`
key at all is the pre-existing (v1) shape — every field this document already
described above. A verdict that includes `findings[]` opts into v2: the
location rule below becomes machine-enforced. There is no `schemaVersion`
integer to bump; the array's presence *is* the version signal, which is why
omitting it never breaks an old verdict.

Each entry:

```json
{
  "severity": "Critical",
  "category": "Security",
  "location": "src/api/upload.ts:88",
  "summary": "one-line description of the finding",
  "disposition": "Accept"
}
```

| Field | Rule |
|-------|------|
| `severity` | Free-text severity label (e.g. `Critical`, `Medium`, `Low`) — descriptive, not machine-gated. |
| `category` | Free-text attack category (e.g. `Security`, `Assumption`, `Race`) — descriptive, not machine-gated. |
| `location` | **Machine-gated.** Must match `path:NNN` or `path:NN-MM` (an ascending line range) when `disposition` is `Accept`. |
| `summary` | One line describing the finding — descriptive, not machine-gated. |
| `disposition` | Must be `Accept` \| `Reject` \| `Defer` — anything else blocks. Only `Accept` (the "must fix" verdict from adversarial review) requires a valid `location`; `Reject` and `Defer` findings may omit it. |

**Worked example — this blocks:**

```json
{ "severity": "Critical", "category": "Security", "location": "see above",
  "summary": "SQL injection via string interpolation", "disposition": "Accept" }
```

`"see above"` does not match `path:NNN` — the gate rejects the verdict with
`inspection-verdict findings[0] is Accept but has no valid location`.

**Worked example — this passes:**

```json
{ "severity": "Critical", "category": "Security", "location": "src/db/query-builder.ts:214",
  "summary": "SQL injection via string interpolation", "disposition": "Accept" }
```

An unknown key on a finding, or a `location` range written backwards
(`file.ts:50-10`), also blocks — same anti-faking posture as every other
artifact in this document.

**Legacy verdicts stay advisory.** A verdict written before this field
existed has no `findings` key at all. The gate does not punish that: it
surfaces one advisory warning (`inspection-verdict has no findings[]...`)
and never blocks on it, even at a hard stage. This is the transition path —
once `review-code`/`reviewer` consistently emit `findings[]`, this warning
simply stops appearing.

### `riskGate` — the high-risk auto-stop

Some changes are too consequential to let an autonomous run wave through on
its own — the reviewer must still write `SEALED`, but a human has to look at
it before the pipeline finalizes. `riskGate` is that circuit breaker.

**Schema version, by presence, not a counter** — same pattern as `findings[]`
above: a verdict with no `riskGate` key at all is treated as low-risk/legacy
and never blocks. Opting in means adding the object:

```json
{
  "riskGate": {
    "touchesSensitiveArea": true,
    "signoffRequired": true,
    "humanSignedOff": false
  }
}
```

| Field | Rule |
|-------|------|
| `touchesSensitiveArea` | Descriptive only — whether the reviewer judged the change to land in a sensitive area. |
| `signoffRequired` | **Machine-gated.** `true` means an autonomous `--auto`/hard-stage finalize must not proceed without a human looking at it. |
| `humanSignedOff` | **Machine-gated.** Must be `true` to clear a `signoffRequired: true` gate. Anything else (`false`, missing) leaves the gate shut. |

**The rule:** at a hard stage, `riskGate.signoffRequired === true` with
`riskGate.humanSignedOff !== true` blocks — the same anti-faking posture as
every other check in this document: a claim without proof does not pass.
Once a human sets `humanSignedOff: true` (after actually reviewing the
change), the gate clears regardless of `signoffRequired`.

**High-risk trigger list** (the reviewer sets `touchesSensitiveArea`/
`signoffRequired` when a change touches any of these):

- **Auth** — login, session handling, token issuance/validation, permission
  checks, RBAC/ACL logic.
- **Secrets** — anything that reads, writes, rotates, or transmits API keys,
  credentials, private keys, or env files holding them.
- **Deploy** — CI/CD pipeline definitions, deployment scripts, infra-as-code
  (Terraform/Helm/K8s manifests), release/publish automation.
- **DB migrations** — schema changes, data backfills, anything that alters
  or destroys persisted data shape.

Anything outside this list is low-risk by default; the reviewer is free to
set `touchesSensitiveArea: true` on judgment for other genuinely consequential
changes, but the four categories above are the floor — never optional.

**Backward-compatible.** A verdict with no `riskGate` key (every verdict
written before this field existed) is treated as low-risk and never blocks —
same transition path as `findings[]`.

**Naming note (de-copy):** this schema restores the risk-gate behavior noted
as cut below, but does not reuse the reference model's `highRisk`/`autoStopRequired`/
`humanApproved` trio — see the de-copy policy section for why.

---

## Coverage — every review dimension has a takumi home

Takumi merges a five-dimension review model into **three** artifacts. This
table proves nothing was dropped in the merge (it is also why the de-copy check
below is about *originality of authorship*, not pretending the work covers less):

| Review dimension (reference only) | Takumi artifact | Takumi field(s) |
|--------------------------------------|-----------------|-----------------|
| context / brief | `study-context.json` | `task`, `acceptanceCriteria`, `touchpoints`, `blastRadius`, `contracts` |
| command verification | `temper-results.json` | `commands[].{command,exitCode,status,summary,ts}` |
| review decision | `inspection-verdict.json` | `score`, `criticalCount`, `decision`, `acceptanceCovered`, `regressionChecked`, `contractStatus` |
| adversarial validation | `inspection-verdict.json` | `refuted`, `unproven`, `reachableRegressions` |
| risk gate | `inspection-verdict.json` | `riskGate.{touchesSensitiveArea,signoffRequired,humanSignedOff}` — restored as a high-risk auto-stop; see "`riskGate` — the high-risk auto-stop" above |

---

## De-copy policy (takumi is self-authored)

Takumi's gate is **self-authored** — own schema, own validator logic, own voice.
The de-copy check (Phase 1 step 2 / Phase 6 step 3) greps the takumi artifacts
against the reference model and asserts **0 shared distinctive
identifiers**, and **fails loud** if the reference is absent (a missing
reference must not pass the check vacuously).

"Distinctive identifier" means a reference-model-specific name — its **file names**
(`context-snippets`, `risk-gate`, `verification`, `review-decision`,
`adversarial-validation`) and its **structurally-distinctive fields**
(`scoutSummary`, `publicContracts`, `highRisk`, `autoStopRequired`,
`humanApproved`, `largeDiff`, `beforeAfter`, `acceptanceCoverage`,
`regressionProof`, `blockingReasons`, `disprovenClaims`, `unverifiedClaims`,
`missingProof`). Takumi shares none of these — it deliberately chose
`acceptanceCovered`/`regressionChecked`/`refuted`/`unproven` and the
`SEALED`/`REWORK`/`BLOCKED` vocabulary instead. When the high-risk auto-stop
was restored (the `riskGate` object above), the same rule applied: it carries
`touchesSensitiveArea`/`signoffRequired`/`humanSignedOff`, not the reference model's
`highRisk`/`autoStopRequired`/`humanApproved` trio — same behavior, own words.

**Generic JSON primitives are allowed and not counted as copying** — you cannot
author a command-result artifact without them, and they carry no authorship:
`command`, `exitCode`, `status`, `summary`, `score`, `decision`, `task`, `mode`,
`ts`, `criticalCount`, `contractStatus`, `reachableRegressions`,
`acceptanceCriteria`, `touchpoints`, `blastRadius`, `findings`, `severity`,
`category`, `location`, `disposition`. These are conventional field names found
across countless tools; sharing them with the reference model is coincidence of
convention, not copied work.

---

## Single source of truth

The validator code at `claude/hooks/lib/evidence-validator.cjs` is authoritative.
No `ajv`. No standalone `.json` schema files. This document follows the code; the
code does not follow this document.
