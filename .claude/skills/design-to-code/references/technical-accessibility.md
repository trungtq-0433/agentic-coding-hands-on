# Accessibility Checks

WCAG compliance and accessibility rules for generated assets.

## Text Overlay Readability

### Color Contrast Ratios
- **WCAG AA**: 4.5:1 for normal text, 3:1 for large text
- **WCAG AAA**: 7:1 for normal text, 4.5:1 for large text

### Testing Requirements
- Check it across the image variations
- Weigh a gradient overlay added in code
- Add text shadows to push legibility up

### Alt Text Guidelines
- Describe the asset's purpose and mood
- Don't echo text that's already visible
- Keep it short (150 characters, tops)

## CSS Techniques for Accessibility

### Gradient Overlay for Text Readability
```css
.hero {
  position: relative;
  background-image: url('hero.webp');
}
.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to bottom,
    rgba(0,0,0,0.3) 0%,
    rgba(0,0,0,0.6) 100%
  );
}
```

### Text Shadow for Contrast
```css
.hero-text {
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);
}
```

### Ensure Minimum Contrast
```css
.hero-cta {
  background: var(--color-primary-600);
  color: white; /* Ensure 4.5:1 contrast */
}
```

## Integration Testing Analysis

Read how the asset behaves under the UI — Read `docs/assets/hero-with-text-overlay.png` with this prompt:

> "Analyze this design asset with UI elements overlaid:
>
> 1. Text Readability: Can all text be read clearly?
> 2. Contrast Issues: Identify any WCAG violations
> 3. Visual Hierarchy: Do buttons and CTAs stand out?
> 4. Spacing Problems: Any crowding or poor breathing room?
> 5. Responsive Concerns: Will this work on mobile at 9:16?
>
> Provide specific recommendations for adjustments."

Save to `docs/assets/integration-analysis.md`.

## Next.js Integration Example

```tsx
// app/components/Hero.tsx
import Image from 'next/image'

export function Hero() {
  return (
    <section className="relative h-screen">
      {/* Background image with optimization */}
      <Image
        src="/assets/hero-desktop.webp"
        alt="Minimalist desert landscape"
        fill
        priority
        quality={85}
        className="object-cover"
        sizes="100vw"
      />

      {/* Gradient overlay for text readability */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/30 to-black/60" />

      {/* Content */}
      <div className="relative z-10 flex h-full items-center justify-center">
        <h1 className="text-6xl font-bold text-white drop-shadow-lg">
          Your Headline
        </h1>
      </div>
    </section>
  )
}
```

## Common Issues

### Issue: Poor Text Overlay Readability
**Symptoms**: Text is hard to read over the generated background
**Solutions**:
- Add the CSS gradient overlay (above)
- Regenerate with "clean composition for text overlay" in the prompt
- Place the darker/lighter zones on purpose
- Add text shadows or backdrop-blur
