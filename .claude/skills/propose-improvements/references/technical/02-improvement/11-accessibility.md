# Improvement Aspect — Accessibility

**Track:** technical · **Aspect:** 11 of 14 · **Slug:** `accessibility`
**Read first:** `references/technical/02-improvement.md` — Shared rules, Ownership map, Entry format, and Value rubric apply unconditionally.
**Output:** `plans/improvement-proposal/technical/02-improvement/11-accessibility.md`
**Template:** `templates/technical/02-improvement/11-accessibility.md`

## Goal
Enumerate accessibility improvement opportunities: WCAG compliance gaps, keyboard navigation, screen-reader labels, color contrast, focus management, ARIA roles, form labeling.

## Use-context overrides
**UI-presence gate (MANDATORY — check first):** Read `plans/improvement-proposal/technical/01-discovery/07-product-surface.md`. If it reports `UI presence: no`, emit a single entry:

```markdown
- Status: clean — no UI detected per discovery §7
- Category: accessibility
```

Then stop — do not enumerate any further entries for this aspect.

If `UI presence: yes` (or not explicitly stated as `no`), proceed with the full aspect.

Status values for this aspect include: `opportunity | clean — no current gap | clean — no UI detected per discovery §7 | needs-more-discovery`.
