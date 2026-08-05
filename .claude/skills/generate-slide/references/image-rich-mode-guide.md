# Image-Rich Mode Guide (`--image` option)

By default, the skill produces text-only slides. When the user wants illustrations — passes `--image`, says "với hình ảnh minh hoạ", "image-rich", "add illustrations", "make it lively with visuals" — switch to **image-rich mode**.

In this mode:
1. **Treat empty space as opportunity for illustration**, not a problem to solve by upsizing fonts.
2. **Important slides get illustrations** — covers, section dividers (optional), key moments, conclusion. Filler/detail slides don't need them.
3. **Place image placeholders** with the right aspect ratio for AI image generators, and **embed the suggested prompt inside each placeholder** so the user can copy-paste into Gemini (Nano Banana) or ChatGPT (GPT Image).

## Supported aspect ratios

For maximum cross-tool compatibility:

| Ratio | Pixel example | Best for |
|-------|---------------|----------|
| **3:2** (landscape, 1536×1024) | wide illustration banner | Hero image at top, full-width visual |
| **2:3** (portrait, 1024×1536) | tall figure | Side-by-side with text column |
| **1:1** (square, 1024×1024) | balanced icon-like image | Card grid illustrations, icons |

## Placeholder design

Use the bundled `addImagePlaceholder(slide, x, y, w, h, prompt)` helper from `assets/helpers.js`. Each placeholder is:
- Light grey fill (`F7F7F7`) with dashed red border
- Aspect ratio matching 3:2 / 2:3 / 1:1
- Centered AI prompt the user copies
- Label "🖼  AI PROMPT — COPY & PASTE" above
- Adaptive font size (auto-shrinks for dense prompts in small boxes)

```javascript
helpers.addImagePlaceholder(slide, 0.5, 1.3, 6.0, 4.0,
  "Aspect ratio: 3:2. Style: clean professional illustration, flat design. Subject: a team of diverse engineers collaborating around a holographic AI interface. Mood: optimistic, modern. Color palette: white background (#FFFFFF) with bold red accent (#FF2200) on the central display.");
```

## Prompt template

Every placeholder's prompt should include five parts:

```
Aspect ratio: <ratio>.
Style: <visual style — flat illustration / 3D render / photography / line art>.
Subject: <what's in the image — be specific>.
Mood: <feeling — professional / playful / urgent / optimistic>.
Color palette: <explicit hex codes>.
```

## CRITICAL — Brand-appropriate imagery rules

### Rule 0 — Always spell out colors with hex codes

The image generator has zero context about Sun* brand. "Sun Red accent" is useless.
- ❌ "Color palette: white background with Sun Red accent."
- ✅ "Color palette: clean white background (#FFFFFF) with a single bold red accent (#FF2200)."

### Rule 1 — Avoid morbid, violent, or horror-coded metaphors

Image generators interpret metaphors **literally** and lean dramatic. A prompt like "graveyard of failed projects" produces an actual graveyard with tombstones, fog, skulls — horror content. Sun* is a professional B2B brand.

**Never use these subjects, even metaphorically:**
- Graveyards, tombstones, RIP, coffins, skeletons, skulls
- Burning buildings, ruins on fire, explosions, wreckage
- Corpses, blood, wounds, decay, rotting matter
- Weapons, violence, threatening figures, dark hooded characters
- Apocalyptic landscapes, post-disaster scenes
- "Death of X" imagery of any kind

**Use business-appropriate metaphors instead:**

| You want to convey... | Good visual metaphor | Bad metaphor (avoid) |
|----------------------|---------------------|---------------------|
| Failed past projects | A cluttered abandoned workshop with dusty equipment | Graveyard of broken monitors |
| Compounding tech debt | A tangled mess of cables growing thicker | Decaying corpse of a system |
| Risk / instability | A precariously stacked tower of blocks tilting | Building on fire collapsing |
| Knowledge loss | An empty office chair, scattered papers, dim lights | Tombstone "RIP knowledge" |
| Stagnation | A wilted potted plant on a desk, faded but not dead | Dying / dead organisms |
| Maze / no way out | A complex maze with dead ends, top-down view | Person trapped, suffering |
| Old / outdated | Dusty filing cabinets, vintage computer, aged paper | Ancient ruins, decay |

### Rule 2 — Keep any text in the image few, large, and centrally placed

When the image is placed in the slide and scaled to its final size (3-4 inches wide), can the text still be read at the back of a room? If yes, fine. If not, too much text or too small.

**The "thumb test":** imagine final image at slide-placeholder size. Each piece of text needs enough area to remain readable. A single short label taking 15-25% of image height is fine. Six tiny axis labels at 3-5% each will be noise.

**Good (works after slide-scaling):**
- ✅ "One bold short label 'PARITY' centered, ~20% of image height"
- ✅ "A single large title word at the top, ~25% of visible area"
- ✅ "Two clearly separated labels — 'OLD' on left, 'NEW' on right — each large"

**Bad (illegible after scaling):**
- ❌ "Axis labels M1, M3, M5, M7 along the bottom" (6 tiny labels)
- ❌ "Code snippets visible on the terminal screen" (small body text)
- ❌ "List of feature names rendered inside folder shapes" (multiple small labels)

**Rule of thumb**: **0-2 text elements per image, each large enough to read.** If you want 3+ text elements, drop some or build with pptxgenjs shapes + text in the slide.

### Rule 3 — Style register: "professional editorial illustration"

Default style language:
- ✅ "Clean editorial illustration"
- ✅ "Flat design with subtle depth"
- ✅ "Minimalist business illustration"
- ✅ "Refined isometric illustration"
- ✅ "Watercolor editorial illustration"

Avoid these — they push toward inappropriate dramatic output:
- ❌ "Cinematic" (movie-poster drama)
- ❌ "Dark fantasy", "gothic", "noir", "dystopian"
- ❌ "Hyperrealistic" (uncanny / unsettling)
- ❌ "Concept art" (video-game cover style)
- ❌ "Dramatic lighting" (harsh contrast / horror)

For serious tone, use **muted palette and composition**, not dramatic style words.

## Palette heuristics by slide content

Don't default every prompt to "Sun Red on white". Vary by emotional register.

**Brand color codes — use in prompts:**

| Brand color | Hex code | Emotional register |
|-------------|----------|-------------------|
| Sun Red | `#FF2200` | Energy, decisiveness, key CTA. Main accent on hero / important slides. |
| Sun Dark Red | `#AD0C00` | Caution, problems, warnings. Use on pain / failure / risk slides. |
| Sun Gold | `#B69256` | Warmth, growth, mastery, achievement. Positive outcomes, case studies. |
| Sun Yellow | `#FDBA05` | Highlight, attention, bright energy. Use sparingly. |
| Text dark | `#1A1A1A` | Body text, neutral foreground. |
| Text grey | `#666666` | Secondary, supporting elements. |
| Light grey | `#F7F7F7` | Card / panel background. |
| White | `#FFFFFF` | Primary background. |

**Palette heuristics by content:**

| Slide content | Suggested palette |
|---------------|-------------------|
| Cover / hero / strong message | White `#FFFFFF` + bold red `#FF2200` on focal element |
| Problem / warning / pain | Muted greys + dark red `#AD0C00`; somber mood |
| Solution / positive outcome | White + Sun Gold `#B69256`; optimistic |
| Process / system diagram | Neutral light greys + single red `#FF2200` for critical step |
| Case study / achievement | Warm white + Sun Gold `#B69256`, red `#FF2200` for key metric |
| Data / chart / metrics | Mostly grey + red `#FF2200` for highlighted point only |
| Section divider hero | Bold Sun Red `#FF2200` dominant with white text |
| Transformation | Two-tone: muted past `#666666`, vibrant future `#FF2200` or `#B69256` |

## Image placement strategy

| Slide type | Image strategy |
|-----------|----------------|
| Cover | Optional large background image |
| TOC | No image — keep clean |
| Section divider | Optional 1 hero illustration |
| Body slide (normal) | 0-1 images, contextual |
| Body slide (important) | 1-2 images, hero + supporting |
| Body slide (numerical/table) | No image — let data speak |
| Closing | Optional thematic image |

For each body slide, ask: would an illustration genuinely help the audience understand or remember this, or would it just be decoration? If decoration, skip.

## Image-rich layouts

See `references/layouts.md` sections 13-17 for code snippets:

| Layout | When to use |
|--------|-------------|
| **#13 Hero image + headline + paragraph** | Section openers, "what is X" slides |
| **#14 Side image + bullets** | Concept slides where image illustrates bullets |
| **#15 Image grid (2×2 or 1×3)** | Multiple examples / personas / variants |
| **#16 Big centerpiece + annotations** | Diagrams, system overviews |
| **#17 Image background + overlay text** | Quotes, mission statements, dramatic moments |
