# Directory Patterns

The full layout for each top-level category. SKILL.md Rule 1 has the bird's-eye view; this file zooms in.

## Documentation (`docs/`)

The project's standing documentation — written to last, read by people and agents alike.

```text
docs/
├── project-overview-pdr.md          # Product/project requirements
├── system-architecture.md           # Architecture & components
├── code-standards.md                # Coding conventions
├── codebase-summary.md              # Auto-generated structure overview
├── project-roadmap.md               # Milestones & progress
├── project-changelog.md             # Version history
├── design-guidelines.md             # UI/UX standards
├── deployment-guide.md              # Deploy procedures
├── journals/                        # Technical diary
│   └── {YYMMDD-HHmm}-{slug}.md     # Session reflections, decisions
└── decisions/                       # Architecture Decision Records
    └── {YYMMDD}-{slug}.md           # ADR documents
```

**Rules:**
- Evergreen docs carry no date — the slug alone names them
- Journals are always timestamped, one to a session or event
- ADRs take a date prefix; sequential numbering is optional
- Hold a doc under 200 lines, and break it into subsections when it grows past that

## Plans (`plans/`)

Where implementation plans, research, and agent back-and-forth live.

```text
plans/
├── {YYMMDD-HHmm}-{slug}/           # Timestamped plan folders
│   ├── plan.md                      # Overview (<80 lines)
│   ├── phase-{NN}-{name}.md         # Phase details
│   ├── research/                    # Research for this plan
│   │   └── researcher-{NN}-{topic}.md
│   └── reports/                     # Agent reports scoped to plan
│       ├── scout-report.md
│       ├── reviewer-report.md
│       └── tester-report.md
├── reports/                         # Standalone agent reports
│   └── {type}-{YYMMDD-HHmm}-{slug}.md
├── research/                        # Standalone research
│   └── researcher-{YYMMDD-HHmm}-{topic}.md
├── templates/                       # Reusable plan templates
│   └── {type}-template.md
└── visuals/                         # Generated diagrams/previews
    └── {slug}.{ext}
```

**Report type prefixes:** `scout-`, `researcher-`, `brainstorm-`, `reviewer-`, `tester-`, `debugger-`, `planner-`

**Rules:**
- Every plan folder gets a timestamp
- Phase files read `phase-{NN}-{name}.md`, numbers zero-padded (01, 02...)
- A report tied to one plan stays inside that plan's folder
- A report tied to nothing in particular goes in `plans/reports/`
- plan.md stays high-level — under 80 lines, linking out to the phase files

## Tests (`tests/`)

Test suites that trace the shape of the source.

```text
tests/
├── unit/                            # Unit tests
│   └── {module}.test.{ext}
├── integration/                     # Integration tests
│   └── {feature}.integration.{ext}
├── e2e/                             # End-to-end tests
│   └── {flow}.e2e.{ext}
├── fixtures/                        # Test data/fixtures
│   └── {name}.{ext}
└── helpers/                         # Shared test utilities
    └── {name}.{ext}
```

**Rules:**
- Echo the source directory layout wherever it's reasonable
- Tag files with `.test.`, `.spec.`, `.integration.`, or `.e2e.`
- Fixtures get descriptive names and no dates
- If the project already has a test convention, follow it rather than this one

## Scripts (`scripts/`)

Build, deploy, and odd-job utility scripts.

```text
scripts/
├── {action}-{target}.{ext}          # e.g., prepare-release-assets.cjs
├── {category}/                      # Group if 5+ scripts
│   └── {action}-{target}.{ext}
```

**Rules:**
- Kebab-case, lead with the verb: `generate-manifest.cjs`, `send-notification.py`
- Reach for a subdirectory only once a category holds 5 or more scripts
- Shell scripts start with a shebang
- No date prefixes — git carries the version history

## Assets (`assets/`)

Media, branding, designs, and anything generated.

```text
assets/
├── images/                          # Static images, screenshots
│   └── {slug}.{ext}
├── videos/                          # Video files
│   ├── {slug}/                      # Multi-file: self-contained folder
│   │   ├── master.mp4
│   │   ├── scene-{NN}.mp4
│   │   └── captions.srt
│   └── {slug}.mp4                   # Single file: flat
├── designs/                         # UI/UX designs, mockups
│   └── {project}/
│       ├── mockup-{variant}.{ext}
│       └── exports/
├── branding/                        # Logos, brand assets
│   └── {name}-{variant}.{ext}       # logo-dark.svg, logo-icon.png
├── generated/                       # AI-generated content
│   └── {type}/                      # images/, audio/, text/
│       └── {YYMMDD-HHmm}-{slug}.{ext}
└── {custom-type}/                   # Project-specific categories
    └── ...
```

**Rules:**
- One file → lay it flat in the category directory
- Several files → wrap them in their own subdirectory
- Variants ride a `-{variant}` suffix rather than splitting into folders
- Size variants: `{name}-{width}x{height}.{ext}`
- Platform variants: `{name}-{platform}.{ext}`
- Generated content always carries a timestamp
- Invent custom categories when a project genuinely needs them

## Configuration (Root / `.config/`)

```text
project-root/
├── .env                             # Environment variables (gitignored)
├── .env.example                     # Env template (committed)
├── .gitignore
├── .eslintrc.*                      # Linter config
├── tsconfig.json                    # TypeScript config
├── package.json                     # Node.js manifest
└── .config/                         # Optional: grouped configs
    └── {tool}.{ext}
```

**Rules:**
- Defer to ecosystem convention — `package.json` belongs at the root, not in `.config/`
- Commit only `.example` templates of `.env`; the real secrets never go in git
- Move things into `.config/` only when the ecosystem actually reads them there

## Guides (`guide/` or `guides/`)

Reference docs and tutorials written for the people using the project.

```text
guide/
├── {topic}.md                       # Reference docs
├── {topic}.yaml                     # Structured data
└── {category}/                      # Group by category if 5+ files
    └── {topic}.md
```

**Rules:**
- Evergreen naming — leave the dates off
- Keep it flat until 5 or more files make categories worth the trouble
- Names that explain themselves: `SKILLS.md`, `COMMANDS.md`, `ENVIRONMENT_RESOLVER.md`
