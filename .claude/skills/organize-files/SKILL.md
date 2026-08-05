---
name: tkm:organize-files
description: Organize files, directories, and content structure in any project — keep things tidy, consistent, and navigable. Use when creating files, determining output paths, organizing existing assets, or standardizing project layout.
argument-hint: "[directories or files to organize]"
metadata:
  author: takumi-agent-kit
  version: "2.0.0"
module: project-context-management
triggers: ["organize files", "where to put this", "naming convention", "file structure"]
---

# Ordering the Workshop

A craftsman who cannot find their tools is not working — they are searching. Order is not decoration; it is the condition that makes the work possible. Every file belongs somewhere specific, every name carries its own meaning, and the discipline of placement is the same discipline that shows in the finished piece.

This skill settles the recurring questions — where a file goes, what to call it, how the directory tree is shaped, and what a given kind of markdown should contain — and answers them the same way every time, in any kind of project.

## When to Use

- Creating any file and needing one settled place for it to land
- Tidying up project files and folders that already exist
- Working out where plans, reports, docs, assets, or tests should be saved
- Holding a consistent naming convention across the whole project
- Giving markdown content (plans, journals, reports, docs) a predictable shape

## Modes

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Advisory** | Other skills/agents reference this skill | Return correct path + naming for requested file type |
| **Organize** | User invokes directly with dirs/files | Scan → propose changes → execute after confirm |

## Core Rules

### Rule 1 — Directory Categories

Every file in a project sorts into one of these top-level homes:

| Category | Path | Purpose |
|----------|------|---------|
| Source code | `src/` or project root | Application code (language-specific, not managed here) |
| Documentation | `docs/` | Human & AI readable docs, guides, specs |
| Plans | `plans/` | Implementation plans, research, agent reports |
| Tests | `tests/` or `test/` | Test suites (unit, integration, e2e) |
| Scripts | `scripts/` | Build, deploy, utility scripts |
| Assets | `assets/{type}/` | Media, branding, designs, generated content |
| Config | Root or `.config/` | dotfiles, config files, env files |
| Guides | `guide/` or `guides/` | User-facing reference docs, tutorials |

**How the categories break down further:**

```
docs/
├── journals/                  # Technical diary, session reflections
├── decisions/                 # ADRs (Architecture Decision Records)
└── *.md                       # Evergreen docs (architecture, standards, roadmap)

plans/
├── {date-slug}/               # Timestamped plan folders
│   ├── plan.md                # Overview
│   ├── phase-{NN}-{name}.md   # Phase details
│   ├── research/              # Research materials for this plan
│   └── reports/               # Agent reports scoped to this plan
├── reports/                   # Standalone agent reports (not plan-scoped)
├── templates/                 # Reusable plan templates
└── visuals/                   # Generated diagrams, previews

assets/
├── images/                    # Static images, screenshots
├── videos/                    # Video files
├── designs/                   # UI/UX designs, mockups
├── branding/                  # Logos, brand assets
├── generated/                 # AI-generated content
└── {custom-type}/             # Project-specific asset categories
```

### Rule 2 — Naming Patterns

Filenames are **kebab-case** and say what they are without being opened.

**Pick one of three modes, depending on whether the content goes stale:**

| Mode | Pattern | When to use | Examples |
|------|---------|-------------|---------|
| **Timestamped** | `{YYMMDD-HHmm}-{slug}` | Time-sensitive: plans, reports, journals, sessions | `260304-1530-auth-plan` |
| **Evergreen** | `{slug}` | Stable docs, configs, guides | `system-architecture.md` |
| **Variant** | `{slug}-{variant}.{ext}` | Multiple versions of same asset | `logo-dark.svg`, `hero-1920x1080.png` |

**What makes a good slug:**
- Lowercase, hyphens as the only separator — no underscores, spaces, or punctuation
- Capped at 50 chars, cut on a word boundary
- Legible on its own, before anyone opens the file
- Never starts or ends on a hyphen

**Date format:** read `$TKM_PLAN_DATE_FORMAT` if it is set; otherwise fall back to `YYMMDD-HHmm`.

```bash
date +%y%m%d-%H%M   # Bash
```

**Code files:** hand naming off to the `descriptive-name` hook — kebab-case for JS/TS/Python/Shell, PascalCase for C#/Java/Swift, snake_case for Go/Rust.

### Rule 3 — Nesting Logic

Whether a thing is a lone file or a folder comes down to how many files it produces:

| Scenario | Pattern | Example |
|----------|---------|---------|
| Single file output | Flat file in category dir | `docs/journals/260304-session-review.md` |
| Multi-file output | Self-contained subdirectory | `plans/260304-auth-impl/plan.md` + `phase-01-*.md` |
| Scoped to parent | Nested under parent context | `plans/260304-auth-impl/reports/scout-report.md` |
| Platform-specific | Platform subdirectory | `assets/posts/twitter/`, `assets/posts/linkedin/` |
| Variant-based | Flat with variant suffix | `assets/branding/logo-light.svg`, `logo-dark.svg` |

**Empty directories:** drop in a `.gitkeep` so git keeps the folder around.

### Rule 4 — Markdown Body Standards

A markdown file's structure is dictated by its type — and it MUST follow that type's shape.

**What holds true for every markdown file:**
- Open with a single `# Title` (H1)
- Add frontmatter (`---`) for metadata whenever a tool will read the file
- Run the sections in order: context → content → next steps
- Tables carry structured data; lists carry sequences
- Trade grammar for concision

**At a glance — the sections each type owes:**

| Type | Key sections |
|------|-------------|
| **Plan** | frontmatter → overview → phases with status → dependencies → success criteria |
| **Phase** | context links → overview → requirements → architecture → impl steps → todo checklist → risks |
| **Report** | frontmatter → summary → findings → recommendations → unresolved questions |
| **Journal** | frontmatter → context → what happened → reflection → decisions → next |
| **Doc** | title → overview → content sections → references |
| **ADR** | status → context → decision → consequences → alternatives considered |
| **Changelog** | version blocks → categories (added/changed/fixed/removed/deprecated) |
| **README** | name → badges → description → quick start → usage → contributing → license |
| **Guide** | title → prerequisites → step-by-step → troubleshooting → FAQ |
| **Spec** | overview → requirements → constraints → API/interface → acceptance criteria |

For the full templates, load `references/markdown-body-templates.md`.

### Rule 5 — Path Resolution Decision Tree

Placing a new file? Walk it down this tree until one branch claims it:

```
1. Is it source code?
   → YES: src/ or project root (follow language conventions)
   → NO: continue

2. Is it a test?
   → YES: tests/ (mirror source structure)
   → NO: continue

3. Is it an implementation plan or agent output?
   → Plan: plans/{date-slug}/
   → Agent report (plan-scoped): plans/{date-slug}/reports/
   → Agent report (standalone): plans/reports/
   → Research: plans/{date-slug}/research/ or plans/research/
   → NO: continue

4. Is it documentation for humans/AI?
   → Technical journal: docs/journals/{date-slug}.md
   → Architecture decision: docs/decisions/{date-slug}.md
   → Evergreen doc: docs/{slug}.md
   → NO: continue

5. Is it a media/design/brand asset?
   → assets/{type}/{naming-per-rule-2}
   → NO: continue

6. Is it a utility script?
   → scripts/{slug}.{ext}
   → NO: continue

7. Is it configuration?
   → Root or .config/ (follow ecosystem conventions)
```

## Organize Mode Actions

Called straight on with `/tkm:organize-files [targets]`, the skill runs this sequence:

1. **Scan** — sweep the target directories and bucket every file by type
2. **Analyze** — flag the naming breaches, the files in the wrong place, the inconsistencies
3. **Propose** — lay out the moves (from → to) in a table
4. **Confirm** — wait for the user's go-ahead before anything moves
5. **Execute** — rename and relocate, opening any directories that are missing
6. **Verify** — print the resulting tree and call out whatever still looks off

**Guardrails:**
- An existing file is never clobbered — a conflict prompts first
- `.git/`, `node_modules/`, and `.env` files stay untouched
- Renames are recoverable (git is the safety net)
- `.gitignore` patterns are honored

## File Type Reference

For per-category detail, load `references/directory-patterns.md`.
For slug generation, date formats, and variant naming, load `references/naming-conventions.md`.

## Integration

This skill is the **one authority** on file organization.
When other skills need to know where their output belongs, they defer to it:

- `plan` / `brainstorm` → plans/ structure
- `journal` → docs/journals/
- `takumi` / `fix` → source code paths (defer to language conventions)
- `test` → tests/ structure
- `docs` / `doc-writer` → docs/ structure
- `scout` / `research` → plans/reports/ or plans/{plan}/research/
- `tkm:review-code` → plans/reports/
- `tkm:manage-project` → docs/ + plans/
- `ui-ux-designer` / `tkm:design-to-code` → assets/designs/
- `git` → respects all naming conventions
- `descriptive-name` hook → code file naming (JS/TS/Python/Shell = kebab-case)

## Pre-Output Checklist

Run this before a single file hits disk:
1. Name the category → that gives the base path (Rule 1)
2. Pick the naming mode → timestamped, evergreen, or variant (Rule 2)
3. Settle the nesting → flat file or its own subdirectory (Rule 3)
4. If it's markdown, fit it to the body template (Rule 4)
5. Look before you write → don't overwrite an existing file or folder
6. Open the directory structure if it isn't there yet
