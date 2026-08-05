# Extract Design Guidelines from Existing Assets

Work backward from existing images or videos to recover the design principles behind them, then write those down as guidelines.

## Purpose

- Read a competitor's design to understand the approach
- Recover a design system from inspiration screenshots
- Learn from work that's already excellent
- Turn visual analysis into documented guidelines
- Set a consistent aesthetic direction off a reference

## Use Cases

- Studying competitor sites or apps
- Mining inspiration galleries (Dribbble, Awwwards, Mobbin)
- Pulling a system out of brand materials
- Reverse-engineering an interface that works
- Building design docs from visual references

## Quick Workflows

### Single Image Analysis
Read `docs/inspiration/reference-design.png` with the detailed prompt from `extraction-prompts.md`. Save the output to `docs/design-guidelines/extracted-design-system.md`.

### Multi-Screen System Extraction
Read `docs/inspiration/home.png` and `docs/inspiration/about.png` together with the multi-screen prompt from `extraction-prompts.md`. Save to `docs/design-guidelines/complete-design-system.md`.

### Video Motion Analysis
Read the key frames from `docs/inspiration/interaction-demo.mp4` with the motion prompt from `extraction-prompts.md`. Save to `docs/design-guidelines/motion-system.md`.

### Competitive Analysis
Read `competitor-a.png`, `competitor-b.png`, and `competitor-c.png` with the competitive-analysis prompt from `extraction-prompts.md`. Save to `docs/design-guidelines/competitive-analysis.md`.

## Detailed References

- `extraction-prompts.md` — every extraction prompt template
- `extraction-best-practices.md` — capture quality, analysis tips
- `extraction-output-templates.md` — documentation formats

## Integration

Once the guidelines are out, put them to work when building components and choosing the provided assets.
