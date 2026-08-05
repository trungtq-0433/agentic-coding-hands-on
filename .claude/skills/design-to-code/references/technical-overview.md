# Technical Guide Overview

The technical side of bringing assets into a frontend, and the practices that keep them lean.

## Quick Reference

### File Optimization
```bash
python scripts/media_optimizer.py \
  --input docs/assets/hero-image.png \
  --output docs/assets/hero-optimized.webp \
  --quality 85
```

### Format Selection
- **WebP**: the web workhorse, 25-35% smaller than PNG, broadly supported
- **AVIF**: the leading edge, 50% smaller than WebP, support still patchy
- **PNG**: lossless, heavy, reach for it when you need transparency
- **JPEG**: lossy, lighter than PNG, photos without transparency

### Responsive Variants
```bash
# Desktop hero (16:9)
--aspect-ratio 16:9

# Mobile hero (9:16 or 3:4)
--aspect-ratio 9:16

# Square cards (1:1)
--aspect-ratio 1:1
```

## Detailed References

- `technical-accessibility.md` — WCAG compliance, contrast checks, alt text
- `technical-workflows.md` — full pipeline examples
- `technical-best-practices.md` — checklists, quality gates

## Quick Commands

```bash
# Optimize
python scripts/media_optimizer.py \
  --input docs/assets/[image].png \
  --output docs/assets/[image].webp \
  --quality 85
```

**Analyze** — Read `docs/assets/[image].png` with your evaluation-criteria prompt. Save to `docs/assets/analysis.md`.

**Extract colors** — Read `docs/assets/[image].png` with:
> "Extract 5-8 dominant colors with hex codes. Classify as primary/accent/neutral."

## Responsive Image Strategies

**Art Direction (different crops)**:
```html
<picture>
  <source media="(min-width: 768px)" srcset="hero-desktop.webp">
  <source media="(max-width: 767px)" srcset="hero-mobile.webp">
  <img src="hero-desktop.jpg" alt="Hero image">
</picture>
```

**Resolution Switching (same crop, different sizes)**:
```html
<img
  srcset="hero-400w.webp 400w, hero-800w.webp 800w, hero-1200w.webp 1200w"
  sizes="(max-width: 600px) 400px, (max-width: 1000px) 800px, 1200px"
  src="hero-800w.jpg"
  alt="Hero image"
/>
```
