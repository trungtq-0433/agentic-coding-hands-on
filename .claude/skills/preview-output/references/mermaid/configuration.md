# Mermaid.js Configuration & Theming

How to configure, theme, and customize Mermaid.js v11.

## Configuration Methods

**1. Set it site-wide at init:**
```javascript
mermaid.initialize({
  theme: 'dark',
  startOnLoad: true,
  securityLevel: 'strict',
  fontFamily: 'Arial'
});
```

**2. Set it per diagram in frontmatter:**
````markdown
```mermaid
---
theme: forest
look: handDrawn
---
flowchart TD
  A --> B
```
````

**3. The precedence:**
Default config → site config → diagram config, with the last winning.

## Core Options

**Rendering:**
- `startOnLoad`: render automatically when the page loads (default: true)
- `securityLevel`: "strict" (default), "loose", "antiscript", "sandbox"
- `deterministicIds`: stable, reproducible SVG IDs (default: false)
- `maxTextSize`: ceiling on diagram text (default: 50000)
- `maxEdges`: ceiling on edges drawn (default: 500)

**Visual style:**
- `look`: "classic" (default), "handDrawn"
- `handDrawnSeed`: a number that keeps the hand-drawn look consistent
- `darkMode`: on/off toggle

**Typography:**
- `fontFamily`: "trebuchet ms, verdana, arial, sans-serif" (default)
- `fontSize`: base text size (default: 16)

**Layout:**
- `layout`: "dagre" (default), "elk", "tidy-tree", "cose-bilkent"

**Debug:**
- `logLevel`: 0-5, trace through fatal
- `htmlLabels`: allow HTML inside labels (default: false)

## Theming

**The built-in themes:**
- `default` - the standard palette
- `dark` - dark background
- `forest` - green tones
- `neutral` - grayscale
- `base` - yours to customize

**Theme variables (base theme only):**
```javascript
mermaid.initialize({
  theme: 'base',
  themeVariables: {
    primaryColor: '#ff0000',
    primaryTextColor: '#fff',
    primaryBorderColor: '#7C0000',
    secondaryColor: '#006100',
    tertiaryColor: '#fff'
  }
});
```

**What you can override:**
- The color families — primary, secondary, tertiary
- Node fills and text colors
- Border and line colors
- Note background and text
- Per-diagram bits (flowchart nodes, sequence actors, pie sections)

**Custom CSS:**
```javascript
mermaid.initialize({
  themeCSS: `
    .node rect { fill: #f9f; }
    .edgeLabel { background-color: white; }
  `
});
```

## Accessibility

**ARIA support:**
```
accTitle: Diagram Title
accDescr: Brief description
accDescr {
  Multi-line detailed
  description
}
```

**Generated for you:**
- `aria-roledescription` attributes
- `<title>` and `<desc>` SVG elements
- `aria-labelledby` and `aria-describedby`

**WCAG compliance:**
Covered across every diagram type — flowchart, sequence, class, Gantt, and the rest.

## Icon Configuration

**Registering icon packs:**
```javascript
import { registerIconPacks } from 'mermaid';
registerIconPacks([
  {
    name: 'logos',
    loader: () => import('https://esm.run/@iconify-json/logos')
  }
]);
```

**Usage:**
```
architecture-beta
  service api(logos:nodejs)[API]
```

**Three ways to load them:**
1. From a CDN (lazy-loaded)
2. From npm via dynamic import
3. As a direct import

## Math Rendering

**KaTeX support:**
```
graph LR
  A["$$f(x) = x^2$$"] --> B
```

**Settings:**
- `legacyMathML`: fall back to the old MathML rendering
- `forceLegacyMathML`: force legacy even where the browser supports native

## Security

**The levels:**
- `strict` - HTML encoded (default, and the one to use)
- `loose` - lets some HTML through
- `antiscript` - strips scripts
- `sandbox` - runs sandboxed

**DOMPurify:**
On by default to block XSS. You can tune it through `dompurifyConfig` — but tread carefully.

## Layout Algorithms

**dagre (default):**
The standard hierarchical layout; fine for most diagrams.

**elk:**
A heavier-duty layout that copes better with tangled graphs.

**tidy-tree:**
Tidy tree shapes for hierarchies.

**cose-bilkent:**
A compound layout built for nested structures.

**Per-diagram:**
````markdown
```mermaid
---
layout: elk
---
flowchart TD
  A --> B
```
````

## Common Patterns

**A stable hand-drawn look:**
```javascript
mermaid.initialize({
  look: 'handDrawn',
  handDrawnSeed: 42  // a fixed seed keeps the look the same run to run
});
```

**Following the OS dark mode:**
```javascript
const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
mermaid.initialize({
  theme: isDark ? 'dark' : 'default'
});
```

**Tuning for performance:**
```javascript
mermaid.initialize({
  startOnLoad: false,  // render by hand
  maxEdges: 1000,       // raise this for dense graphs
  deterministicIds: true  // plays well with caching
});
```

## Validation

**Parse without rendering:**
```javascript
try {
  await mermaid.parse('graph TD\nA-->B');
  console.log('Valid syntax');
} catch(e) {
  console.error('Invalid:', e);
}
```

**Rendering in code:**
```javascript
const { svg } = await mermaid.render('graphId', 'graph TD\nA-->B');
document.getElementById('output').innerHTML = svg;
```
