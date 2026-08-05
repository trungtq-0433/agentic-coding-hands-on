# HTML Presentation Template

Reference architecture for generating scroll-snap HTML slide presentations. Every HTML-mode presentation follows this structure.

## Base HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Presentation Title</title>

    <!-- Fonts: use Fontshare or Google Fonts — NEVER system fonts (Inter, Roboto, Arial = AI slop) -->
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Space+Grotesk:wght@400;500;600&display=swap" />

    <style>
      /* ===========================================
           CSS CUSTOM PROPERTIES (THEME)
           Change these to change the whole look.
           Values come from the chosen style preset.
           =========================================== */
      :root {
        /* Colors — paste from style-presets.md */
        --bg-primary: #1a1a1a;
        --card-bg: #FF5722;
        --text-primary: #ffffff;

        /* Typography — MUST use clamp() */
        --font-display: "Archivo Black", sans-serif;
        --font-body: "Space Grotesk", sans-serif;
        --title-size: clamp(2rem, 6vw, 5rem);
        --subtitle-size: clamp(0.875rem, 2vw, 1.25rem);
        --body-size: clamp(0.75rem, 1.2vw, 1rem);

        /* Spacing — MUST use clamp() */
        --slide-padding: clamp(1.5rem, 4vw, 4rem);
        --content-gap: clamp(1rem, 2vw, 2rem);

        /* Animation */
        --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
        --duration-normal: 0.6s;
      }

      /* Base reset */
      * { margin: 0; padding: 0; box-sizing: border-box; }

      /* ---- PASTE viewport-base.css CONTENTS HERE ---- */

      /* ===========================================
           REVEAL ANIMATIONS
           .reveal elements animate in when parent .slide gets .visible class
           =========================================== */
      .reveal {
        opacity: 0;
        transform: translateY(30px);
        transition:
          opacity var(--duration-normal) var(--ease-out-expo),
          transform var(--duration-normal) var(--ease-out-expo);
      }

      .slide.visible .reveal {
        opacity: 1;
        transform: translateY(0);
      }

      /* Stagger children — each child reveals slightly after the previous */
      .reveal:nth-child(1) { transition-delay: 0.1s; }
      .reveal:nth-child(2) { transition-delay: 0.2s; }
      .reveal:nth-child(3) { transition-delay: 0.3s; }
      .reveal:nth-child(4) { transition-delay: 0.4s; }

      /* ---- Preset-specific styles go here ---- */
    </style>
  </head>
  <body>

    <!-- Optional: Progress bar at top of page -->
    <div class="progress-bar" style="position:fixed;top:0;left:0;height:3px;background:var(--accent,#FF5722);width:0%;z-index:100;transition:width 0.2s;"></div>

    <!-- Optional: Navigation dots -->
    <nav class="nav-dots" style="position:fixed;right:1.5rem;top:50%;transform:translateY(-50%);z-index:100;display:flex;flex-direction:column;gap:0.5rem;"></nav>

    <!-- ========== SLIDES ========== -->
    <section class="slide title-slide">
      <div class="slide-content">
        <h1 class="reveal">Presentation Title</h1>
        <p class="reveal">Subtitle / Author</p>
      </div>
    </section>

    <section class="slide">
      <div class="slide-content">
        <h2 class="reveal">Slide Title</h2>
        <p class="reveal">Content goes here...</p>
      </div>
    </section>

    <!-- More slides... -->

    <script>
      /* ===========================================
           SLIDE PRESENTATION CONTROLLER
           Handles keyboard nav, touch/swipe, scroll snap,
           intersection observer for animations, progress bar.
           =========================================== */
      class SlidePresentation {
        constructor() {
          this.slides = document.querySelectorAll('.slide');
          this.currentSlide = 0;
          this.navDotsContainer = document.querySelector('.nav-dots');
          this.progressBar = document.querySelector('.progress-bar');

          this.setupIntersectionObserver();
          this.setupKeyboardNav();
          this.setupTouchNav();
          this.setupProgressBar();
          this.setupNavDots();
        }

        /* Add .visible class when a slide scrolls into view → triggers CSS animations */
        setupIntersectionObserver() {
          const observer = new IntersectionObserver(
            (entries) => {
              entries.forEach((entry) => {
                if (entry.isIntersecting) {
                  entry.target.classList.add('visible');
                  this.currentSlide = Array.from(this.slides).indexOf(entry.target);
                  this.updateNavDots();
                  this.updateProgressBar();
                }
              });
            },
            { threshold: 0.5 }
          );
          this.slides.forEach((s) => observer.observe(s));
        }

        setupKeyboardNav() {
          document.addEventListener('keydown', (e) => {
            if (['ArrowDown', 'ArrowRight', ' ', 'PageDown'].includes(e.key)) {
              e.preventDefault();
              this.navigateTo(this.currentSlide + 1);
            } else if (['ArrowUp', 'ArrowLeft', 'PageUp'].includes(e.key)) {
              e.preventDefault();
              this.navigateTo(this.currentSlide - 1);
            }
          });
        }

        setupTouchNav() {
          let touchStartY = 0;
          document.addEventListener('touchstart', (e) => { touchStartY = e.touches[0].clientY; }, { passive: true });
          document.addEventListener('touchend', (e) => {
            const delta = touchStartY - e.changedTouches[0].clientY;
            if (Math.abs(delta) > 50) {
              this.navigateTo(this.currentSlide + (delta > 0 ? 1 : -1));
            }
          }, { passive: true });
        }

        setupProgressBar() {
          if (!this.progressBar) return;
          this.updateProgressBar();
        }

        setupNavDots() {
          if (!this.navDotsContainer) return;
          /* Always clear before building — prevents duplicate dots on re-open */
          this.navDotsContainer.innerHTML = '';
          this.slides.forEach((_, i) => {
            const dot = document.createElement('button');
            dot.style.cssText = 'width:8px;height:8px;border-radius:50%;border:none;cursor:pointer;background:rgba(255,255,255,0.4);transition:all 0.3s;padding:0;';
            dot.addEventListener('click', () => this.navigateTo(i));
            this.navDotsContainer.appendChild(dot);
          });
          this.updateNavDots();
        }

        navigateTo(index) {
          const clamped = Math.max(0, Math.min(index, this.slides.length - 1));
          this.slides[clamped].scrollIntoView({ behavior: 'smooth' });
        }

        updateNavDots() {
          if (!this.navDotsContainer) return;
          this.navDotsContainer.querySelectorAll('button').forEach((dot, i) => {
            dot.style.background = i === this.currentSlide
              ? 'rgba(255,255,255,1)'
              : 'rgba(255,255,255,0.4)';
            dot.style.transform = i === this.currentSlide ? 'scale(1.4)' : 'scale(1)';
          });
        }

        updateProgressBar() {
          if (!this.progressBar) return;
          const pct = ((this.currentSlide + 1) / this.slides.length) * 100;
          this.progressBar.style.width = pct + '%';
        }
      }

      new SlidePresentation();
    </script>
  </body>
</html>
```

## Required JavaScript Features

Every HTML presentation must include:

1. **`SlidePresentation` class** with:
   - Keyboard navigation (arrows, space, page up/down)
   - Touch/swipe support (50px threshold)
   - Intersection Observer for `.visible` class (triggers CSS animations)
   - Progress bar updates
   - Navigation dots (always `innerHTML = ''` before building to prevent duplicates)

2. **Content density hard limits** (enforced in generation, not code):
   - Title slides: 1 heading + 1 subtitle
   - Content slides: max 4–6 bullets OR 2 paragraphs
   - Feature grids: max 6 cards

## Critical CSS Rules

| Rule | Correct | Wrong |
|------|---------|-------|
| Negate CSS function | `calc(-1 * clamp(...))` | `-clamp(...)` |
| Font sourcing | Fontshare / Google Fonts URL | Inter, Roboto, Arial, system fonts |
| Image max-height | `min(50vh, 400px)` | Filling full slide height |
| `prefers-reduced-motion` | `animation-duration: 0.01ms !important` | Ignoring the media query |
