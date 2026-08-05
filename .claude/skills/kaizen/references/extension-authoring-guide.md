# Skill Extension Authoring Guide

**Single source of truth** for the Takumi skill extension format. The `skill-extension-loader.cjs` hook and `/tkm:kaizen` both conform to this spec — change it here first.

## What Extensions Are

User-owned markdown files that layer instructions on top of a shipped skill without editing it. They live outside the kit's release manifest, so the installer classifies them as user-owned: **they survive every `tkm update` untouched**, while the shipped SKILL.md keeps receiving upstream improvements.

Write one by hand, or let `/tkm:kaizen <skill>` produce one for you.

## Layout

```
.claude/skills/<skill-dir>/
├── SKILL.md              ← kit-owned. NEVER edit — update conflicts, lost work.
├── references/           ← kit-owned. Same rule.
└── extensions/           ← yours. The kit never touches this directory.
    ├── <slug>.md         ← one extension per concern, kebab-case slug
    └── evals/            ← benchmark data (cases.md, rubric.md) — not injected
```

## File Format

```markdown
---
extends: tkm:review-code
type: post
---

After the standard review completes, also check our team conventions:
...instructions...
```

| Field | Required | Values | Notes |
| --- | --- | --- | --- |
| `extends` | yes | skill's frontmatter `name` (`tkm:review-code`) or bare dir name (`review-code`) | Must match the activated skill or the file is skipped. Matching compares the part after the namespace prefix, so the bare dir name is the most robust canonical form |
| `type` | yes | `pre` \| `post` \| `override:<section-heading>` | See semantics below |

### Type Semantics

- **`pre`** — applied before the skill's workflow starts (setup context, team constraints, scope narrowing)
- **`post`** — applied after the skill's standard behavior (extra checks, output additions, follow-up steps)
- **`override:<section-heading>`** — replaces the named SKILL.md section's instructions. **Fragile**: kit updates may rename headings, silently orphaning the override. Prefer `pre`/`post`; re-validate overrides after each kit update (`/tkm:kaizen <skill>` Recon flags stale anchors).

### Injection Behavior (hook contract)

When a skill activates, the loader hook injects valid extensions in order `pre → override → post`. Invalid files (wrong `extends`, bad `type`, missing frontmatter) are skipped and named in a warning. Total payload over ~4KB degrades to file-path listings the model reads on demand — keep extensions short.

The loader resolves the local extensions dir by trying, in order, `$CLAUDE_PROJECT_DIR` → the current working dir → `$HOME` (global install). The first root whose `.claude/skills/<dir>/extensions/` exists wins.

## Local vs Shared (team) Extensions

Two sources feed the same skill, merged at load time:

| Source | Path | Tracked by git? | Use for |
| --- | --- | --- | --- |
| **Local** (personal) | `.claude/skills/<dir>/extensions/*.md` | No — `.claude/` is gitignored | Your own experiments and tuning |
| **Shared** (team) | `<sharedDir>/<dir>/*.md` | Yes — lives in a repo the team commits | Customizations the whole team should get |

- `sharedDir` comes from the `skillExtensions.sharedDir` config key (a per-machine pointer; the *content* it points at is what's shared via git). Set it with `tkm config set skillExtensions.sharedDir <path>`.
- **Layout mirrors local**: shared extensions live per-skill under `<sharedDir>/<skill-dir>/*.md`.
- **Precedence**: on filename collision, **local overrides shared** — personal tuning wins.
- **Multi-repo caveat**: a relative `sharedDir` must stay inside the project root (paths escaping via `../` are rejected). To point at a sibling repo, use an **absolute path**, or install takumi at the parent root so the target repo is a subfolder.

## Worked Example: team conventions for `tkm:review-code`

`.claude/skills/review-code/extensions/team-convention-checklist.md`:

```markdown
---
extends: tkm:review-code
type: post
---

## Team Convention Checklist (run after the standard review)

For every finding-free file, still verify:

1. **Error messages**: user-facing strings go through the i18n helper, never hardcoded
2. **API endpoints**: new routes registered in the route manifest, return envelope `{ data, error }`
3. **DB access**: queries go through the repository layer — no inline SQL in handlers
4. **Logging**: no `console.log` in production paths; use the project logger with level
5. **Feature flags**: new behavior behind a flag unless the PR says "no-flag" with a reason

Add violations to the findings list at severity `medium`, tagged `[team-convention]`.
```

Copy this file into your project, adjust the checklist to your team's rules, and `/tkm:review-code` picks it up on the next activation — no kit modification, no update conflicts.

## Rules of Thumb

- One concern per file; compose with multiple files rather than one mega-extension
- Extensions sharpen a skill; they must never contradict its hard gates or turn it into a different skill
- Found a genuine bug in a shipped skill? File a kit issue — patch locally with an extension meanwhile
- Validate after kit updates: `override:` anchors and assumptions can drift
