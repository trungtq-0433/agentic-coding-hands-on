# Question Routing

Map the asker's natural question to the right evidence and answer mode. The asker should never
need to know which artifact holds the answer — that is this file's job. Reads the evidence
inventory from [`artifact-discovery.md`](./artifact-discovery.md); hands the selection to
[`answer-synthesis.md`](./answer-synthesis.md).

## Routing Matrix

> **Path authority (DRY).** [`_shared/docs-canonical-mapping.md`](../../_shared/docs-canonical-mapping.md)
> is the **single source of truth** for Specs/Docs artifact paths. The concrete paths in this matrix
> are **operational hints by topic** — when they and canonical-mapping disagree, **canonical-mapping
> wins**; do not treat this table as authoritative. (A few rebuild-spec artifacts — `screen-flow.md`,
> `screen-list.md`, `behavior-logic.md` — are not yet in canonical-mapping; those paths are carried
> here until that file lists them.)
>
> **Docs root is mode-aware** — see [`_shared/docs-canonical-mapping.md` § Language Layout](../../_shared/docs-canonical-mapping.md#language-layout) (single-lang → `docs/` root; per-lang → `docs/<primary>/`). In single-lang mode (the common case) all `docs/{generated,system,features,flows}/...` paths below are correct as-is.

<!-- layout-exempt: routing matrix paths are topic hints (single-lang docs/ root); mode-aware pointer added above -->
| Intent | Trigger semantics (not exact strings) | Primary evidence (topic → path hint) | Secondary | Answer mode | Lens |
|---|---|---|---|---|---|
| **Feature list / "what does it do"** | "what does this product do", "list/what features", "overview" | `docs/generated/feature-list.md`, `docs/system/overview.md` | `docs/generated/user-stories.md`, `docs/project-overview-pdr.md` | structured list + 1-para summary | Product/Domain |
| **System architecture / "draw it"** | "architecture", "how is it built", "draw/diagram the system", "components" | `docs/system/architecture.md`, `docs/generated/entities.md`, `docs/generated/route-list.md`, `docs/generated/screen-flow.md` | codebase scan | **Mermaid diagram** + prose | Systems Designer |
| **Feature detail / wireframe** | "detail/spec for feature X", "how does X work", "wireframe for X" | `docs/features/{slug}/technical-spec.md`, `docs/generated/screen-list.md` | `docs/features/{slug}/screens.md`, `plans/<active>/artifacts/screens/SCR###*/spec.md` | spec walkthrough (+ wireframe description) | Systems Designer |
| **Impact analysis** | "if I change X what's affected", "blast radius", "what depends on X", "ripple" | feature `technical-spec.md` + `docs/generated/entities.md` + `docs/generated/route-list.md` + `docs/generated/behavior-logic.md` + `docs/generated/api-map.md` | existing graph via `_shared/graphify-code-graph.md`, then grep/code refs via `tkm:scan-codebase` | impact three-tier breakdown | Risk Analyst |
| **Upsale opportunities** | "upsale", "improvement proposal", "what can we sell/optimize", "tech debt to pitch" | `plans/upsale/**` proposals | `feature-list.md`, `docs/project-roadmap.md` | opportunity list w/ rationale | Tech Strategist + Product |
| **Open-ended / other** | anything not matching above | broadest PRESENT layer(s) | codebase | adaptive | all 5 lenses |

> **Spec paths resolve under the detected `specsRoot`** (see `artifact-discovery.md` § 1a). The
> `docs/{generated,system,features}/...` paths above are the rebuild-spec v4 layout. In **SDD / spec-kit** repos the Specs
> layer lives in `specs/NNN-name/` with no `feature-list.md` — there the feature list = the set of
> spec folders, feature detail = `specs/NNN-name/spec.md`, and impact evidence = that folder's
> `data-model.md` + `contracts/` + `tasks.md`. Route the same intents to whichever layout is present.

## Trigger Keyword Hints (semantic, not literal matching)

Match on **intent and verbs**, not exact phrases. Keyword clusters help, but a paraphrase routes the
same way.

- Feature list: *what / does / do / feature / capability / functionality / overview / scope*
- Architecture: *architecture / system / built / structure / components / draw / diagram / stack / design*
- Feature detail: *detail / spec / specification / screen / wireframe / how does <feature> / flow of <feature>*
- Impact analysis: *change / modify / remove / affect / impact / break / depend / ripple / blast radius / if I*
- Upsale: *upsale / upsell / opportunity / improvement / proposal / optimize / sell / pitch / monetize / tech debt*

## Multi-Match Tie-Break

When a question matches multiple intents, pick the **most specific**:

1. **Impact analysis wins** when change/affect verbs are present (`change`, `modify`, `remove`,
   `affect`, `break`) — even if a feature name also appears (which would otherwise look like
   feature-detail).
2. **Feature detail beats feature list** when a specific feature/screen is named.
3. **Architecture beats feature list** when "draw / diagram / structure / components" appear.
4. Otherwise default to the broader intent, and if still ambiguous use the **open-ended lane**.

## Absent-Layer Fallback (per intent)

If the primary evidence layer is ABSENT (per discovery), degrade — never dead-end:

| Intent | Primary absent → fallback |
|---|---|
| Feature list | scan-codebase to enumerate routes/modules → list + advise `/tkm:rebuild-spec` |
| Architecture | existing graph if present, else scan-codebase for dirs/entrypoints → infer + describe diagram, flag INFERRED + advise `/tkm:rebuild-spec` |
| Feature detail | grep the named symbol/route in code → summarize behavior + advise `/tkm:rebuild-spec --features F###` |
| Impact analysis | existing graph `affected/path/query` if present, then grep references of the symbol across code → three-tier from verified usages + advise `/tkm:rebuild-spec` |
| Upsale | no `plans/upsale/` → quick heuristic scan (tests, deps, TODOs) + advise `/tkm:upsale` |

Fallback details and exact advisory strings live in
[`answer-synthesis.md`](./answer-synthesis.md) § "Degradation Ladder" and
[`artifact-discovery.md`](./artifact-discovery.md) § "Absent-Layer Advisory".

## Present-but-Insufficient (docs-first escalation)

Distinct from the absent-layer case above: the primary layer is **PRESENT** but does not actually
answer the question (e.g. an implementation-level "how *exactly*…" against a spec that only states
intent). The **sufficiency gate** in [`retrieval-strategy.md`](./retrieval-strategy.md) decides this
after Gather. On `INSUFFICIENT`, escalate to a **targeted** code search on the named symbol — grep,
then read the enclosing block — not a full-tree scan. This is the docs-first → code-fallback path.

`--high` / `--max` raise the level: `--high` always reaches source (noting code refs + verify);
`--max` forces a full source scan plus multi-subagent fan-out to cross-verify every claim. `--low`
does the opposite — it stays in docs and never escalates. See
[`retrieval-strategy.md`](./retrieval-strategy.md) § Processing Levels.

## Open-Ended Lane

<!-- layout-exempt: top-of-funnel paths use docs/ root (single-lang); mode-aware pointer in routing matrix above -->
For questions matching no specific intent: gather top-of-funnel evidence — `docs/system/overview.md` +
`docs/generated/feature-list.md` + the active plan's `plan.md` (whichever are PRESENT) — and answer adaptively with
all five lenses. Still emit the `## Sources` citation block. This lane guarantees the engine never
refuses a project question.
