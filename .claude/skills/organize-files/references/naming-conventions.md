# Naming Conventions

The complete naming ruleset across every file type. SKILL.md Rule 2 sketches it; this is the detail.

## Slug Generation

### Rules

- Lowercase the whole title or topic
- Turn spaces and punctuation into hyphens
- Leave numbers as they are
- Cap it at 50 characters, cutting on a word boundary
- No hyphen at the start or the end
- No two hyphens in a row

### Examples

| Title | Slug |
|-------|------|
| "User Authentication Flow" | `user-authentication-flow` |
| "Fix: API Rate Limiting Bug #42" | `fix-api-rate-limiting-bug-42` |
| "10 Tips for Better CI/CD" | `10-tips-for-better-ci-cd` |
| "AI & Automation: A Guide" | `ai-automation-a-guide` |

## Date Formats

Read `$TKM_PLAN_DATE_FORMAT` when it's set; otherwise the default is `YYMMDD-HHmm`.

| Format | Example | Use case |
|--------|---------|----------|
| `YYMMDD-HHmm` | `260304-1530` | Default for time-sensitive files |
| `YYMMDD` | `260304` | Date-only (ADRs, daily reports) |
| No date | `{slug}` | Evergreen content |

### Stamp the date when it's...

- A plan, report, journal, session, or brainstorm
- Generated or AI-produced content
- An asset tied to a specific campaign
- Anything that loses relevance as time passes

### Leave the date off when it's...

- A doc — architecture, standards, guides
- A config file
- Source code
- A template
- A brand asset — logos, styles

## Code File Naming

Hand language-specific naming to the `descriptive-name` hook:

| Language | Convention | Example |
|----------|-----------|---------|
| JS/TS/Python/Shell | kebab-case | `user-auth-service.ts` |
| C#/Java/Kotlin/Swift | PascalCase | `UserAuthService.cs` |
| Go/Rust | snake_case | `user_auth_service.go` |
| CSS/SCSS | kebab-case | `auth-form-styles.scss` |

**The trade-off:** clarity beats brevity. A long name that explains itself wins over a short one that doesn't.

## File Extensions

| Type | Extensions |
|------|-----------|
| Images | `.png`, `.jpg`, `.webp`, `.svg`, `.gif` |
| Videos | `.mp4`, `.mov`, `.webm` |
| Audio | `.mp3`, `.wav`, `.m4a` |
| Documents | `.md`, `.txt`, `.pdf` |
| Data | `.json`, `.yaml`, `.yml`, `.csv`, `.xml` |
| Config | `.json`, `.yaml`, `.toml`, `.ini`, `.env` |

## Variant Naming

### Size variants

Pattern: `{name}-{width}x{height}.{ext}`

- `hero-1920x1080.png`
- `thumbnail-300x200.jpg`
- `banner-mobile-640x100.png`

### Platform variants

Pattern: `{name}-{platform}.{ext}`

- `cover-youtube.png`
- `post-instagram.png`
- `ad-linkedin.jpg`

### Theme/style variants

Pattern: `{name}-{variant}.{ext}`

- `logo-dark.svg`
- `logo-light.svg`
- `banner-alt.png`

### Version variants

Pattern: `{name}-v{N}.{ext}`

- `mockup-v2.png`
- `proposal-v3.pdf`

## Directory Naming

- Kebab-case, every time
- Plural when it's a collection: `tests/`, `scripts/`, `assets/`
- Singular when it's one thing: `src/auth/`, `docs/`
- Spell it out — `configurations/`, not `configs/` (the well-worn exceptions like `docs/` and `src/` stand)

## Report File Naming

Pattern: `{agent-type}-{YYMMDD-HHmm}-{slug}.md`

Examples:
- `scout-260304-1530-auth-module-analysis.md`
- `researcher-260304-1545-oauth2-comparison.md`
- `brainstorm-260304-1600-caching-strategy.md`
- `reviewer-260304-1700-api-endpoints.md`

## Plan Folder Naming

Pattern: `{YYMMDD-HHmm}-{slug}/`

Examples:
- `260304-1530-implement-user-authentication/`
- `260305-0900-migrate-database-to-postgres/`
- `260306-1400-redesign-dashboard-layout/`

## Scene/Sequence Naming

Pattern: `scene-{NN}-{position}.{ext}` or `step-{NN}-{name}.{ext}`

- `scene-01-start.png`, `scene-01-end.png`
- `step-01-install.md`, `step-02-configure.md`

Zero-pad the numbers so they sort in the right order.
