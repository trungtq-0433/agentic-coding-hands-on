# Quick Design Workflow

Fast design work with the planning kept to a minimum.

## Prerequisites
- Bring up the `tkm:design-ui` skill first

## Initial Research
Run the `tkm:design-ui` searches:
```bash
python3 .claude/skills/design-ui/scripts/search.py "<product-type>" --domain product
python3 .claude/skills/design-ui/scripts/search.py "<style-keywords>" --domain style
python3 .claude/skills/design-ui/scripts/search.py "<mood>" --domain typography
python3 .claude/skills/design-ui/scripts/search.py "<industry>" --domain color
```

## Workflow Steps

### 1. Start the Design
Hand it straight to the `ui-ux-designer` subagent:
- Skip the heavy planning
- Get to implementation fast
- Make the calls as you go

### 2. Implement
- Default to HTML/CSS/JS if unspecified
- Keep the focus on the core
- Don't let the speed cost the quality

### 3. Report & Approve
- Summarize the changes briefly
- Ask the user for approval
- Update `./docs/design-guidelines.md` once approved

## When to Use
- Simple components
- Prototypes and MVPs
- Tight timelines
- Iterative exploration
- Single-page designs

## Quality Shortcuts
Moving fast, but still hold:
- Semantic HTML
- CSS variables for consistency
- Basic accessibility
- A clean code structure

## Related
- `workflow-immersive.md` — for the comprehensive designs
- `technical-overview.md` — quick reference
