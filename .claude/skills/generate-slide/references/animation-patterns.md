# Animation Patterns Reference

Use this reference when generating HTML presentations. Match animations to the intended feeling.

## Effect-to-Feeling Guide

| Feeling | Animations | Visual Cues |
|---------|-----------|-------------|
| **Dramatic / Cinematic** | Slow fade-ins (1–1.5s), large scale transitions (0.9→1), parallax | Dark backgrounds, spotlight effects |
| **Techy / Futuristic** | Neon glow (box-shadow), glitch/scramble text, grid reveals | Particle systems (canvas), monospace accents |
| **Playful / Friendly** | Bouncy easing (spring physics), floating/bobbing | Rounded corners, pastel colors |
| **Professional / Corporate** | Subtle fast animations (200–300ms), clean slides | Navy/slate, precise spacing |
| **Calm / Minimal** | Very slow subtle motion, gentle fades | High whitespace, muted palette, serif type |
| **Editorial / Magazine** | Staggered text reveals, image-text interplay | Strong type hierarchy, grid-breaking layouts |

## Entrance Animations

```css
/* Fade + Slide Up (most versatile) */
.reveal {
    opacity: 0;
    transform: translateY(30px);
    transition: opacity 0.6s var(--ease-out-expo),
                transform 0.6s var(--ease-out-expo);
}
.slide.visible .reveal { opacity: 1; transform: translateY(0); }

/* Scale In */
.reveal-scale {
    opacity: 0;
    transform: scale(0.9);
    transition: opacity 0.6s, transform 0.6s var(--ease-out-expo);
}
.slide.visible .reveal-scale { opacity: 1; transform: scale(1); }

/* Slide from Left */
.reveal-left {
    opacity: 0;
    transform: translateX(-50px);
    transition: opacity 0.6s, transform 0.6s var(--ease-out-expo);
}
.slide.visible .reveal-left { opacity: 1; transform: translateX(0); }

/* Blur In */
.reveal-blur {
    opacity: 0;
    filter: blur(10px);
    transition: opacity 0.8s, filter 0.8s var(--ease-out-expo);
}
.slide.visible .reveal-blur { opacity: 1; filter: blur(0); }
```

## Background Effects

```css
/* Gradient Mesh — layered radial gradients for depth */
.gradient-bg {
    background:
        radial-gradient(ellipse at 20% 80%, rgba(120, 0, 255, 0.3) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 20%, rgba(0, 255, 200, 0.2) 0%, transparent 50%),
        var(--bg-primary);
}

/* Grid Pattern — subtle structural lines */
.grid-bg {
    background-image:
        linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: 50px 50px;
}

/* Noise Texture — add grain without an image file */
.noise-bg::after {
    content: '';
    position: absolute;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 1;
}
```

## Interactive Effects

```javascript
/* 3D Tilt on Hover */
class TiltEffect {
    constructor(el) {
        el.style.transformStyle = 'preserve-3d';
        el.addEventListener('mousemove', (e) => {
            const { left, top, width, height } = el.getBoundingClientRect();
            const x = (e.clientX - left) / width - 0.5;
            const y = (e.clientY - top) / height - 0.5;
            el.style.transform = `rotateY(${x * 10}deg) rotateX(${-y * 10}deg)`;
        });
        el.addEventListener('mouseleave', () => {
            el.style.transform = 'rotateY(0) rotateX(0)';
        });
    }
}

/* Counter animation — animate numbers from 0 to target */
function animateCounter(el, target, duration = 1500) {
    const start = performance.now();
    const update = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); /* ease-out cubic */
        el.textContent = Math.round(eased * target).toLocaleString();
        if (progress < 1) requestAnimationFrame(update);
    };
    requestAnimationFrame(update);
}

/* Particle system (canvas) — use for Neon Cyber preset */
class ParticleSystem {
    constructor(canvas) {
        this.ctx = canvas.getContext('2d');
        this.particles = Array.from({ length: 50 }, () => ({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            size: Math.random() * 2 + 1,
        }));
        this.animate();
    }
    animate() {
        const { ctx } = this;
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        this.particles.forEach(p => {
            p.x += p.vx; p.y += p.vy;
            if (p.x < 0 || p.x > ctx.canvas.width) p.vx *= -1;
            if (p.y < 0 || p.y > ctx.canvas.height) p.vy *= -1;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(0,255,204,0.6)';
            ctx.fill();
        });
        requestAnimationFrame(() => this.animate());
    }
}
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Fonts not loading | Check Fontshare/Google Fonts URL; ensure font names match CSS `font-family` |
| Animations not triggering | Verify IntersectionObserver is running; check `.visible` class is being added |
| Scroll snap not working | Ensure `scroll-snap-type: y mandatory` on `html`; each `.slide` needs `scroll-snap-align: start` |
| Mobile performance | Disable heavy effects at 768px; reduce particle count; use `will-change: transform` sparingly |
| Negative clamp values | Use `calc(-1 * clamp(...))` — CSS silently ignores leading `-` before functions |
