# Analysis Best Practices

How to keep visual analysis sharp, and the traps that dull it.

## Analysis Best Practices

### 1. Be Specific
❌ Vague: "Is this image good?"
✓ Sharp: "Does this hold the brutalist line? Rate how well it takes a text overlay."

### 2. Use Structured Prompts
Lay the request out as numbered criteria so the feedback is something you can act on:
```
1. [Criterion A]
2. [Criterion B]
3. [Criterion C]
Overall Rating: X/10
```

### 3. Request Hex Codes
❌ Don't settle for: "The image uses blue tones"
✓ Insist on: "Extract hex codes: #1E40AF, #3B82F6, #60A5FA"

### 4. Compare Variations
Never take the first generation without something to weigh it against:
- Make 3+ variations
- Analyze them side by side
- Pick on the scores, not the gut

### 5. Test Integration Context
Read the asset *with* UI on top of it, never in isolation:
- Mock up the text overlays
- Drop in real buttons and CTAs
- Judge it across responsive contexts

### 6. Document Decisions
Keep the analysis reports as part of the design-system record:
```
docs/
  assets/
    hero-image.png
    hero-analysis.md       # Analysis report
    hero-color-palette.md  # Extracted colors
  design-guidelines/
    asset-usage.md         # Guidelines derived from analysis
```

## Common Analysis Pitfalls

### ❌ Vague Feedback
You get back: "Colors are nice"
**Fix**: Demand the hex codes and a read on the harmony

### ❌ No Numeric Rating
You get back: "Pretty good quality"
**Fix**: Always ask for a 1-10 score with a reason

### ❌ Missing Context
Reading an asset without saying what it's for
**Fix**: Put the context in the prompt (hero section, background, marketing, etc.)

### ❌ Single Analysis Point
Only checking the look, skipping the technical and integration angles
**Fix**: Run the full evaluation template across every dimension

## Evaluation Criteria

### Core Evaluation Points
- Holds to the chosen aesthetic direction
- Color harmony and palette consistency
- Compositional balance and focal points
- Plays well with text overlay (when there is one)
- Professional quality, rated 1-10
- Technically fit (aspect ratio, resolution, file character)

### Context-Specific Points
- **For hero sections**: takes a text overlay, supports the hierarchy
- **For backgrounds**: subtle, clean pattern repeats, real texture detail
- **For marketing**: on brand, emotionally landing, attention-grabbing
- **For decorative elements**: integrates, carries the right visual weight, feels unique
