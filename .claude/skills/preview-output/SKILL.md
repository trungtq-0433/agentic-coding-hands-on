---
name: tkm:preview-output
description: "Put a file or an idea on screen — read existing files in the browser, or turn a topic into a visual explanation, slide deck, or diagram as standalone HTML. Reach for it on 'show me', 'preview this', 'explain visually', 'make a diagram', or any request to view or render content."
argument-hint: "[path|topic] [--html] [--explain|--slides|--diagram|--ascii|--diff]"
metadata:
  author: takumi-agent-kit
  version: "1.1.0"
module: specialized-output
triggers: ["show me", "preview", "explain visually", "make a diagram", "render this"]
---

# Putting Work on Screen

A maker checks the work in its finished form before anyone else sees it — held up to the light, viewed as it will actually be read. That check is what this skill does: it renders a file you already have so you can read it cleanly, or it builds a fresh visual — explanation, deck, diagram — out of an idea.

## Default (No Arguments)

Called bare, with no argument, open `AskUserQuestion` and offer the operations below:

| Operation | Description |
|-----------|-------------|
| `(view)` | Open a file or directory for reading |
| `--explain` | Build a visual explanation |
| `--slides` | Build presentation slides |
| `--diagram` | Build an architecture diagram |
| `--ascii` | Diagram that reads cleanly in a terminal |
| `--stop` | Shut down the preview server |
| `--html --explain` | Standalone HTML explanation (opens in the browser) |
| `--html --diagram` | Standalone HTML diagram with zoom controls |
| `--html --slides` | Polished HTML slide deck |
| `--html --diff` | Visual diff review (HTML) |
| `--html --plan-review` | Plan-against-codebase comparison (HTML) |
| `--html --recap` | Snapshot of recent project context (HTML) |

Surface these through `AskUserQuestion` under the header "Preview Operation" and the prompt "What would you like to do?".

## Usage

### View Mode
- `/tkm:preview-output <file.md>` - Read a markdown file in the novel-reader UI
- `/tkm:preview-output <directory/>` - Walk through a directory's contents
- `/tkm:preview-output --stop` - Bring down a running server

### Generation Mode (Markdown)
- `/tkm:preview-output --explain <topic>` - Visual explanation (ASCII + Mermaid + prose)
- `/tkm:preview-output --slides <topic>` - Slide deck, one idea per slide
- `/tkm:preview-output --diagram <topic>` - Single tight diagram (ASCII + Mermaid)
- `/tkm:preview-output --ascii <topic>` - ASCII-only diagram that lives in the terminal

### Generation Mode (HTML)
- `/tkm:preview-output --html --explain <topic>` - Standalone HTML explanation
- `/tkm:preview-output --html --slides <topic>` - Polished HTML slide deck
- `/tkm:preview-output --html --diagram <topic>` - HTML diagram with zoom controls
- `/tkm:preview-output --html --diff [ref]` - Visual diff review
- `/tkm:preview-output --html --plan-review [plan-file]` - Plan held up against the codebase
- `/tkm:preview-output --html --recap [timeframe]` - Snapshot of recent project context

## Argument Resolution

Walk the arguments in this order and stop at the first match:

1. **`--stop`** → Bring the server down and exit
2. **`--html` present** → Flag HTML output mode, then keep going
3. **Generation flags** (`--explain`, `--slides`, `--diagram`, `--ascii`) → Generation mode. Load `references/generation-modes.md`
4. **HTML-only flags** (`--diff`, `--plan-review`, `--recap`) → Turn on HTML mode automatically, then generation mode. Load `references/generation-modes.md`
5. **Work out the path from the argument:**
   - An explicit path → use it as-is
   - A contextual reference → resolve it against the recent conversation
6. **Path resolves to something on disk** → View mode. Load `references/view-mode.md`
7. **Path is missing or won't resolve** → Ask the user which file they meant

**Turning a topic into a slug:**
- Lowercase it
- Swap spaces and special characters for hyphens
- Drop everything that isn't alphanumeric or a hyphen
- Squeeze runs of hyphens down to one
- Strip any leading or trailing hyphen
- **Cap at 80 chars** — if it runs longer, cut at a word boundary

**More than one flag:** keep the first generation flag; treat the rest as part of the topic.

**Placeholder `{topic}`:** stands in for the user's original input in title case — not the slug.

## Error Handling

| Error | Action |
|-------|--------|
| Empty topic | Ask the user for a topic |
| Flag with no topic | Prompt: "Please provide a topic: `/tkm:preview-output --explain <topic>`" |
| Topic empties out after sanitizing | Ask for a topic that includes alphanumeric characters |
| Write to disk fails | Report it; point at disk space and permissions as the likely cause |
| Server won't start | See whether the port is taken; try `/tkm:preview-output --stop` first |
| No generation flag and the reference won't resolve | Ask which file they meant |
| A file already sits at the output path | Overwrite it silently — no prompt |
| Server is already up | Reuse the running instance and just open the new URL |
| Parent `plans/` directory is absent | Create the directory tree before writing |
| `--diff` outside a git repo | Say: "No git repo detected. Run inside a git repository." |
| `--plan-review` with no plan file and no active plan | Say: "Provide a plan file path or run from a session with an active plan." |
| `--recap` with no git history | Say: "No git history found. Run inside a git repository with commits." |
| `--html --ascii` together | Unsupported — `--ascii` exists only for the terminal. Point them to `--html --diagram` |
| `--diff` on a PR number but `gh` is missing | Say: "GitHub CLI (gh) is required for PR diffs. Install from https://cli.github.com/" |

## HTML Output Mode (`--html`)

Hang `--html` on any generation flag and the output flips from Markdown to one self-contained HTML file.

**Output:** a single `.html` file with every bit of CSS and JS inlined. Double-click it open — no server in the loop.
**Location:** `{plan_dir}/visuals/{slug}.html` — the same plan-aware path logic markdown mode uses.
**Opening it:** `open` (macOS) / `xdg-open` (Linux) / `start` (Windows)
**MANDATORY — Theme Toggle:** every HTML page MUST carry a light/dark theme toggle button. The exact CSS, HTML, and JS live in `html-css-patterns.md` → "Theme Toggle Button". A page missing the toggle is not finished.

### Reference Loading (HTML mode)

Before you generate anything, you MUST read the references below:

| Mode | Always read | Mode-specific |
|------|-------------|---------------|
| All HTML modes | `html-design-guidelines.md` | — |
| `--explain` | `html-css-patterns.md`, `html-libraries.md` | Template: `architecture.html` |
| `--diagram` | `html-css-patterns.md`, `html-libraries.md` | Template: `mermaid-flowchart.html` or `architecture.html` |
| `--slides` | `html-slide-patterns.md`, `html-css-patterns.md`, `html-libraries.md` | Template: `slide-deck.html` |
| `--diff` | `html-css-patterns.md`, `html-libraries.md` | Templates: `data-table.html`, `architecture.html` |
| `--plan-review` | `html-css-patterns.md`, `html-libraries.md` | Templates: `architecture.html`, `data-table.html` |
| `--recap` | `html-css-patterns.md`, `html-libraries.md` | Templates: `architecture.html`, `data-table.html` |

For pages built from several sections (`--explain`, `--diff`, `--plan-review`, `--recap`), also read `html-responsive-nav.md`.

The Mermaid v11 syntax rules sit under `references/mermaid/`.

### HTML-Only Modes

#### `--diff [ref]` (implies --html)
A visual diff review. Figure out scope from: branch name, commit hash, HEAD, PR number, commit range, or fall back to main.
Pull: `git diff --stat`, `--name-status`, the changed files, the new API surface, the CHANGELOG.
Lay out: executive summary, KPI dashboard, module architecture (Mermaid), side-by-side feature comparisons, flow diagrams, file map, test coverage, review cards (Good/Bad/Ugly/Questions), decision log, re-entry context.

#### `--plan-review [plan-file]` (implies --html)
A plan held up against the codebase. Take either a plan file path or the active plan from context.
Pull: read the plan, read every file it touches, map the blast radius, check its assumptions against reality.
Lay out: plan summary, impact dashboard, current-vs-planned architecture (paired Mermaid), side-by-side change breakdown, dependency analysis, risk assessment, review cards, gaps in understanding.
Colour code: blue = current, green = planned, amber = concern, red = gap.

#### `--recap [timeframe]` (implies --html)
A snapshot of where the project stands. Window: shorthand (2w, 30d, 3m), default 2w.
Pull: project identity, git log, git status, decision context, an architecture scan.
Lay out: project identity, architecture snapshot (Mermaid), recent activity, decision log, state KPI cards, the mental model you need to hold, cognitive-debt hotspots, next steps.

### Style Strategy
- Baseline: the static anti-slop rules in `html-design-guidelines.md` (6 curated presets)
- For `--slides`: weigh calling `/tkm:design-ui` for a wider set of style choices
- Shift the look between back-to-back HTML outputs — a different font pairing, a different palette each time
