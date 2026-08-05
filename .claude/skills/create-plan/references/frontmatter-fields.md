# plan.md Frontmatter Fields (Spec Provenance)

The Work-Type & Spec Gate (step 1d) and the planner record one — at most one — spec-provenance field
into `plan.md` YAML frontmatter. These four fields are **mutually exclusive**: a plan.md carries AT
MOST ONE of `spec_draft:` / `spec:` / `spec_waived:` / (`work_type: deliverable` with none).
`work_type:` is orthogonal and may accompany any of them.

## `spec_draft:`

Set when a spec DRAFT was authored to the plan dir (step 1d choice a, or takumi Stage 1.5):

```yaml
spec_draft: plans/260615-0859-my-feature/spec/my-feature/   # plan-local draft, not yet in docs/
```

- **Producer:** step 1d gate choice (a); takumi Stage 1.5 / fast.
- **Consumer:** takumi code-discipline Stage 0 Promote — copies the draft to `docs/features/`, <!-- layout-exempt: docs/ root is single-lang default; mode-aware pointer below in spec: section -->
  registers it, then REPOINTS this field to `spec:`. After promote, `spec_draft:` is gone and `spec:`
  holds the docs/ path.

## `spec:`

The PROMOTED spec path. Written ONLY by takumi's promote step (Stage 0), which repoints `spec_draft:`
→ `spec:` once the draft is copied into `docs/`. The planner may also set it directly when a promoted
spec already exists in `docs/features/` and is NOT being revised. <!-- layout-exempt: docs/ root single-lang; mode-aware pointer below -->

> **Docs root is mode-aware** — see [`_shared/docs-canonical-mapping.md` § Language Layout](../../_shared/docs-canonical-mapping.md#language-layout) (single-lang → `docs/` root; per-lang → `docs/<primary>/`). In single-lang mode (the common case) the path below is correct as-is.

```yaml
spec: docs/features/F###_slug/   # relative path, within docs/ tree — no absolute/traversal paths  # layout-exempt: schema example; mode-aware pointer above
```

- **Producer:** takumi promote step (repoint); planner (only for an already-promoted, unrevised spec).
- **Consumer:** Stage 6 doc-writer / promote-cleanup (reads `spec:` to locate the promoted spec).
  Doc-writer tolerates an absent field; cleanup simply does not fire.
- **Set ONLY when** the spec is actually promoted in `docs/` — never to a guessed or inferred path.

## `work_type:`

Optional field set by the Work-Type & Spec Gate (step 1d) or takumi Stage 0:

```yaml
work_type: feature      # or: deliverable
```

- **Producer:** step 1d gate (this skill) and takumi Stage 0 work-type classification
  (classified BEFORE discipline routing and before any `F###` reservation).
- **Consumers:** Stage 6 doc-writer (skips spec reconciliation for `deliverable`); takumi
  code-discipline — do NOT re-classify when field is already present.
- **Values:** `feature` | `deliverable`. `ambiguous` is never written — it always resolves
  to one of the two before any file is created.

## `spec_waived:`

Optional field set when the user explicitly chose to waive spec authoring (gate choice b):

```yaml
spec_waived: "user's exact words quoted verbatim"
```

- **Producer:** step 1d gate, choice (b) — value is the user's exact words (audit trail).
- **Consumers:** Stage 6 doc-writer — no spec reconciliation; takumi code-discipline —
  do NOT re-ask or re-classify.
