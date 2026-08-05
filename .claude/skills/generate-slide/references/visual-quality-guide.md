# Visual Quality Guide — Sun* PPTX Slides

A deck that follows brand colors but looks cramped, text-heavy, or amateurish misses the point. The goal is **beautiful and visually engaging**, not just brand-compliant.

The guidance below is what to aim for. It's not a checklist of rigid rules — every deck has its quirks and exceptions, and your judgment matters more than mechanical compliance.

## Aim for slides that fill the space gracefully

The most common failure mode is the opposite of cramming: **slides that look empty**. Cards take up most of the slide but their content sits at 11-13pt, leaving 40-50% of the card blank. The slide looks under-confident.

The fix: **match font size to the available space, not to an abstract minimum.** A typical body slide can comfortably hold around **80-120 words** when typography is right-sized. Around 120 words is the upper end; below 60 words you should probably scale fonts up.

When a source section feels too dense even at maximum readable sizes, **splitting into 2 slides is the right move**. Common split patterns:
- **Overview + Details** — high-level frame, then deeper dive
- **Concept + Examples** — define on one, illustrate on the next
- **Problem + Solution** — pain points, then response
- **Metrics + Lessons** — numbers, then narrative takeaways

## Aim for readable, content-aware typography

The biggest mistake is **using one font size regardless of card size**. A 4-bullet list inside a 6"-wide × 4"-tall card needs much larger text than the same list inside a 3"-wide × 2.5"-tall card. **Scale typography to the container.**

**Reference scale** (use the upper end when roomy; lower end when dense):

| Element | Smaller / dense | Standard | Larger / roomy |
|---------|-----------------|----------|----------------|
| Slide title | 22pt bold | 22pt bold | 22pt bold (keep fixed) |
| Card / section header | 14pt bold | 16-18pt bold | 20-22pt bold |
| Body text inside a card | 12pt | 14-16pt | 18-20pt |
| Bullet items (short, ≤6 words each) | 13pt | 16-18pt | 20-22pt |
| Captions / labels | 9-10pt | 10-11pt | 12pt |
| Big numbers / stats | 32-36pt bold | 40-48pt bold | 56-72pt bold |

**Heuristic**: estimate how many lines the card body needs (with the chosen font size + width), and compare to available height. If text fills less than ~60% of available height, **scale the font up** until it fills 70-85%. Leave 15-30% breathing room — but not 50% empty space below the text.

**Concrete examples**:
- **2-column comparison cards** (each ~6" × 4-5") with 4-6 short bullets: use **body 16-18pt**, not 11-13pt.
- **4-card 2×2 grid** (each ~6" × 2.5") with short bullets: use **body 14-16pt**, header 18pt.
- **Dense table** with 6+ rows: use body 11-12pt (rows are short).
- **Hero callout** filling most of the slide: use body 24-32pt.
- **Process flow** with 5 narrow boxes (~2.5" each): use body 10-11pt (boxes are narrow).

Going below 11pt for body text is rarely right. Either scale up the card or split the slide. The exception is dense tables or footnotes.

**Practical workflow**: when in doubt, start 1-2 sizes larger than instinct. After visual QA, scale down only if something overflows. Easier to step down than recognize under-filling.

## Resize containers, not just fonts

Sometimes scaling fonts to 20pt still leaves a card half-empty because content is genuinely brief. **Shrink the card** instead of leaving blank space. A 5-bullet card with short bullets is fine at 3.5" tall.

Two complementary strategies:
1. **Grow the type** until text fills the container (when text is short, container is over-sized)
2. **Shrink the container** to match content (when content has a natural limit)

For comparison slides with side-by-side cards, often best to do **both**: scale fonts to 18-20pt *and* shrink card height from 5.0" to 3.5-4.0". Use leftover vertical space for a key message strip below, or leave an intentional bottom margin.

## Aim for visual richness

Every body slide should ideally have at least one visual element. Options include:
- **Numbered circles, big-number callouts, percentages**
- **Icons or emoji** (see next section — encouraged!)
- **Cards / panels** with colored backgrounds
- **Comparison columns** side-by-side
- **Process flows** with arrows
- **Metrics tables** with colored headers
- **Pain/Solution split** layouts

Vary layouts across consecutive slides. Three "numbered points" slides in a row feels monotone.

## Use icons and emoji to add personality

Icons and emoji make slides feel modern and human. **Sprinkle them in thoughtfully**:
- **Category reinforcement**: ✓ for success, ⚠ for warnings, ★ for tiers, → for flow
- **Section header glyphs**: 📊 DATA, 🎯 GOALS, 🚀 LAUNCH, 💡 KEY MESSAGE, 🔧 TOOLS, 📨 CONTACT
- **Replacing plain numbered circles** with topical glyphs
- **Adding visual anchor** to text-heavy slides

```javascript
// Inline emoji
slide.addText("🚀 Launch the product", { fontSize: 16, ... });
// Large visual anchor
slide.addText("💡", { x: 1, y: 2, w: 1, h: 1, fontSize: 60, valign: "middle", margin: 0 });
// Symbol characters
slide.addText("→", { fontSize: 24, color: SUN_RED, bold: true, ... });
```

**Don't go overboard** — 1-3 icons per slide is plenty.

## Color discipline

**Sun Red `#FF2200` is one accent per slide** — not a flood fill. Each body slide should have one or two prominent red elements (callout bar, key message highlight, header underline). Rest stays neutral.

Multi-category content can use sub-colors — Sun Dark Red, Gold, Yellow — but treat as exceptions, not defaults.
