# Best Practices Checklists

The quality gates and checklists that govern asset-generation work.

## Asset Generation Workflow

### Before Generating Assets
- [ ] Pinned a clear aesthetic direction from the brief
- [ ] Pulled the color palette and typographic character
- [ ] Named the asset's purpose and where it has to sit
- [ ] Thought through accessibility and any text that overlays it

### During Generation
- [ ] Wrote a design-driven, context-specific prompt
- [ ] Chose the right model and quality tier
- [ ] Set the aspect ratio the use case needs
- [ ] Ran a few variations when exploring

### After Generation
- [ ] Ran a full visual analysis (score ≥ 7/10)
- [ ] Pulled the exact palette with hex codes
- [ ] Compared the variations and picked the strongest
- [ ] Tried it with text/UI overlaid
- [ ] Trimmed the file size for the web
- [ ] Built responsive variants where needed
- [ ] Wrote down how and where to use the asset

## Design Guideline Extraction Workflow

### When Analyzing Existing Designs
- [ ] Captured clean, high-res reference screenshots
- [ ] Ran a full design analysis with structured prompts
- [ ] Pulled specific values (hex codes, px sizes, ms timings)
- [ ] Looked across several screens for repeated patterns
- [ ] Checked font guesses against Google Fonts
- [ ] Wrote findings in a form you can act on
- [ ] Produced CSS variable specs
- [ ] Saved the guidelines into the project's docs/

## Quality Gates

### Never Move to Integration Without
- [ ] Visual analysis score ≥ 7/10
- [ ] The extracted palette documented
- [ ] Accessibility contrast checks passing
- [ ] Responsive variants produced
- [ ] File optimization done
- [ ] Usage guidelines written

## Final Checklist

Before any asset counts as "done":
- [ ] Generated from a design-driven prompt, not a generic one
- [ ] Analyzed and scored ≥ 7/10
- [ ] Palette pulled for CSS
- [ ] Checked with UI overlaid for readability
- [ ] Optimized for the web (WebP/JPEG)
- [ ] Responsive variants built
- [ ] Usage guidelines written
- [ ] Accessibility checks passed (contrast, alt text)
- [ ] Wired into the frontend with proper optimization

## Common Issues & Solutions

### Issue 1: Generated Asset Too Generic
**Symptoms**: It looks like stock photography, no design character
**Solution**:
- Sharpen the prompt with specific aesthetic movements
- Name artists/designers/styles outright
- Push toward a more distinctive color direction
- Add context-specific detail that makes it one of a kind

### Issue 2: Inconsistent Design Language
**Symptoms**: Each asset feels unrelated to the last
**Solution**:
- Lock down a design system from the first asset that worked
- Carry the same palette keywords into every later prompt
- Hold one aesthetic direction across the whole run
- Reference the earlier successful assets in new prompts

### Issue 3: Low Analysis Scores
**Symptoms**: Scores keep landing below 7/10
**Solutions**:
- Re-check the criteria — are they reasonable?
- Study high-scoring designs for the patterns
- Run extraction on inspiration to learn what's working
- Feed the analysis's specific notes back into the next prompt

### Issue 4: Slow Generation Times
**Symptoms**: Waiting too long for results
**Solutions**:
- Use a fast model while exploring
- Generate in batches, not one at a time
- Save the ultra model for final production assets
- Run analysis on one batch while the next generates

**Remember**: Design first, generate second. Context is everything. Iterate without mercy. Analysis isn't optional. Demand specifics, not generalities.
