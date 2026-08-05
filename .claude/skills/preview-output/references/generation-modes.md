# Generation Modes

## Step 1: Settle on Where the File Lands

1. Look for an active plan context (it arrives via `## Plan Context` in the hook injection)
2. With an active plan: write to `{plan_dir}/visuals/{topic-slug}.md`
3. Without one: write to `plans/visuals/{topic-slug}.md`
4. Make the `visuals/` directory if it isn't there yet

## Step 2: Build the Content

**Mermaid syntax:**
For any mermaid code block, the v11 syntax rules are in the `mermaid/` references.

**Two rules that always hold:**
- Wrap node text that contains special characters: `A["text with /slashes"]`
- Escape brackets inside labels: `A["array[0]"]`

Pick the template that matches the flag:

### --explain (Visual Explanation)
```markdown
# Visual Explanation: {topic}

## Overview
A line or two on what this explains.

## Quick View (ASCII)
[ASCII sketch of how the pieces connect]

## Detailed Flow
[Mermaid sequence/flowchart diagram]

## Key Concepts
1. **Concept A** - What it is
2. **Concept B** - What it is

## Code Example (if applicable)
[A relevant snippet, commented]
```

### --slides (Presentation Format)
```markdown
# {Topic} - Visual Presentation

---
## Slide 1: Introduction
- One idea per slide
- Bullets, nothing dense

---
## Slide 2: The Problem
[Mermaid flowchart]

---
## Slide 3: The Solution
- First point
- Second point

---
## Slide 4: Summary
What to walk away with...
```

### --diagram (Focused Diagram)
```markdown
# Diagram: {topic}

## ASCII Version
[ASCII architecture sketch]

## Mermaid Version
[Mermaid flowchart/graph]
```

### --ascii (Terminal-Friendly Only)
```
[ASCII-only box diagram, with a legend]
```

## Step 3: Write It Out and Preview

1. Write the generated content to the path you settled on
2. Bring up the preview server pointed at that file:
```bash
node .claude/skills/markdown-novel-viewer/scripts/server.cjs \
  --file "<generated-file-path>" --host 0.0.0.0 --open --foreground
```

## Step 4: Report Back

Hand the user:
- The path of the generated file
- The preview URL (local + network)
- A reminder that the file is parked in the plan's `visuals/` folder for later

---

## HTML Mode Generation

With `--html` in play (or pulled in by `--diff`, `--plan-review`, `--recap`), build a self-contained HTML file rather than Markdown.

### HTML Step 1: Settle on Where the File Lands
- Same plan-aware logic as markdown mode, just a `.html` extension
- Active plan: `{plan_dir}/visuals/{topic-slug}.html`
- No plan: `plans/visuals/{topic-slug}.html`
- Make the `visuals/` directory if it's missing

### HTML Step 2: Read the References
Start with `html-design-guidelines.md` every time (anti-slop rules, style presets).

Then read whatever the mode calls for:

| Mode | References | Templates to study |
|------|------------|-------------------|
| --html --explain | html-css-patterns.md, html-libraries.md | architecture.html |
| --html --diagram | html-css-patterns.md, html-libraries.md | mermaid-flowchart.html or architecture.html |
| --html --slides | html-slide-patterns.md, html-css-patterns.md, html-libraries.md | slide-deck.html |
| --html --diff | html-css-patterns.md, html-libraries.md | data-table.html, architecture.html |
| --html --plan-review | html-css-patterns.md, html-libraries.md | architecture.html, data-table.html |
| --html --recap | html-css-patterns.md, html-libraries.md | architecture.html, data-table.html |

For pages with several sections (explain, diff, plan-review, recap), also read `html-responsive-nav.md`.

### HTML Step 3: Build the Content

Move through four phases:

**Think:** decide what each piece of content should render as:
- Mermaid when the shape is the point (flowcharts, sequence, ER, state, mind maps, class, C4)
- CSS Grid for prose-heavy architecture (cards with descriptions, code references)
- HTML `<table>` for tabular data (requirement audits, comparisons, matrices)
- Chart.js for actual charts (KPI dashboards, sparklines)
- A hybrid for big systems (15+ elements): a plain Mermaid overview backed by detailed CSS Grid cards

**Structure:** choose the template pattern, lay out the sections, and assign each a depth tier (hero/elevated/default/recessed).

**Style:** pull a font pairing and palette from the curated presets, shifting away from your last output. Then run the anti-slop checks:
- Inter/Roboto/system-ui not used alone as the body font
- No indigo/violet (#8b5cf6, #7c3aed) for the accent
- No animated glowing box-shadows
- No gradient text on headings
- No emoji icons in section headers
- No faux traffic-light dots faked onto code blocks

**Deliver:** write one self-contained `.html` file with all CSS and JavaScript inlined. The only external pulls are from CDNs — Google Fonts, Mermaid.js v11, Chart.js, anime.js.

**MANDATORY — Theme Toggle:** every HTML page MUST carry the light/dark theme toggle button from `html-css-patterns.md` → "Theme Toggle Button". No exceptions. That button (`<button class="theme-toggle">`) has to be the first child of `<body>`, with its CSS and JS inlined. A page without it is not finished.

For `--slides`: it's worth calling `/tkm:design-ui` to widen the style choices.
Any Mermaid diagram has to follow the `mermaid/` references.

### HTML Step 4: Open It in the Browser
- macOS: `open "{output-path}"`
- Linux: `xdg-open "{output-path}"`
- Windows: `start "{output-path}"`
- No server in the loop — the file stands on its own
- Report the path and confirm the browser opened

### Gathering Data for the HTML-Only Modes

#### --diff [ref]
1. Work out scope: branch name → working-tree diff; commit hash → `git show`; HEAD → uncommitted; PR number → `gh pr diff`; range → two commits; nothing → diff against main
2. Run `git diff --stat`, `git diff --name-status`, line counts
3. Read every changed file along with its surrounding context
4. Sweep the new public API surface (grep exports, functions, classes, interfaces)
5. Check CHANGELOG.md, README.md, and any doc updates
6. Reconstruct the reasoning behind the change from commits, conversation, and progress docs

#### --plan-review [plan-file]
1. Take an explicit plan file path, or pick it up from the active plan context
2. Read the plan end to end (problem, changes, rejected alternatives, scope)
3. Read every file the plan references plus their dependencies
4. Map the blast radius (imports, tests, config, public API)
5. Check the plan's assumptions against the actual state of the code

#### --recap [timeframe]
1. Parse the window: shorthand (2w, 30d, 3m) → git `--since` format; default 2w
2. Project identity: README, CHANGELOG, package.json, the file layout
3. Recent activity: `git log --oneline --since=...`, `git shortlog`
4. Where things stand: `git status`, branches gone stale, TODOs, progress docs
5. Why choices were made: commit messages, plans, ADRs
6. Architecture scan: key files, module structure, the areas that change most

### Quality Checklist
Before you hand over the HTML, confirm:
- [ ] **Squint test:** does the visual hierarchy hold up at arm's length?
- [ ] **Swap test:** would this read as AI-generated? Check it against the forbidden patterns
- [ ] **Theme toggle (MANDATORY):** is the toggle the first child of `<body>`? Do both light and dark render correctly? See `html-css-patterns.md` → "Theme Toggle Button".
- [ ] **Overflow:** no horizontal scroll on the content (tables aside, and those go in a scroll container)
- [ ] **Mermaid:** zoom controls in place? ELK layout once you hit 10+ nodes?
- [ ] **Responsiveness:** still readable at mobile width?
