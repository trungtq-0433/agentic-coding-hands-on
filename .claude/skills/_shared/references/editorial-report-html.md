# Editorial Report HTML

Shared design contract for any skill's `--html` flag. When `--html` is requested, create one additional `.html`
file **next to** the markdown report (same directory, same stem: `report.md` → `report.html`). The HTML must be
**self-contained**: inline CSS and JavaScript in one file, no build step, no external assets (one optional
Mermaid CDN tag is the only allowed network dependency, and the page must still render without it).

The markdown report stays the **primary artifact**; the HTML is a companion rendering of the same content.

Source style: long-form editorial / investor memo / printed-magazine aesthetic.

## Design Philosophy

- Editorial print, not slide deck. Think serious business magazine translated to scrollable web.
- Restraint over decoration. No gradients, no shadows, no rounded corners.
- Hairline rules and whitespace create structure.
- Serif display type carries authority; mono labels carry metadata and taxonomy.
- Paper-warm background, not pure white.
- Red accent is a scalpel: use only for italic emphasis, eyebrows, callouts, and active states.

## Color Tokens

```css
:root {
  --ink: #0a0a0a;
  --ink-soft: #1a1a1a;
  --paper: #faf7f2;
  --paper-warm: #f0ebe1;
  --accent: #b8232c;
  --accent-soft: #e8d4d6;
  --gold: #8a6f2c;
  --muted: #6b6258;
  --hairline: rgba(10,10,10,0.12);
  --serif: 'Fraunces', Georgia, serif;
  --sans: 'Inter Tight', system-ui, sans-serif;
  --mono: 'JetBrains Mono', monospace;
}
```

Rules:

- Page background = `--paper`; pure white forbidden.
- Dark surfaces use `--ink` with paper-colored text.
- Accent appears on italic serif emphasis, eyebrows, numbers, left borders, and active nav/timeline states.
- Use `--gold` only for optional/future/secondary track markers.

## Typography

- Cover title: serif, `clamp(60px, 11vw, 180px)`, weight 300, line-height 0.92.
- Display heading: serif, `clamp(48px, 7vw, 110px)`, weight 300.
- Section heading: serif, `clamp(32px, 4.5vw, 64px)`, weight 400.
- Pull quote: serif italic, `clamp(28px, 3.6vw, 48px)`, weight 300.
- Lead paragraph: serif, `clamp(18px, 1.6vw, 22px)`, line-height 1.5.
- Body: sans, 15px, line-height 1.65.
- Eyebrows, labels, metadata: mono, uppercase, 10-12px, letter spacing 0.12-0.18em.

Emphasis pattern (use at most one red italic phrase per major heading):

```html
<h2>One clear thesis.<br><em>One red italic phrase.</em></h2>
```

## Layout

- Each section is `.slide`: `min-height: 100vh; padding: 60px 8vw; border-bottom: 1px solid var(--hairline);`.
- Inner `.container`: `max-width: 1240px; margin: 0 auto;`.
- Mobile under 900px: reduce padding to `60px 6vw`; collapse multi-column grids to one column.
- Use asymmetry for two-column grids: `grid-template-columns: 1fr 1.2fr; gap: 80px;`.
- Every non-cover section carries:
  - Top-left `.slide-tag`: `■ 02 · Section name` in mono red.
  - Top-right `.slide-num`: `03 / 10` in mono muted.

## Content mapping (works for any report)

The HTML is a faithful rendering of the markdown report — same facts, same links, same numbers. Map the
report's structure onto editorial sections:

| Markdown report element | HTML treatment |
|---|---|
| Title + date + scope/metadata line | **Cover** section (serif title, mono metadata folio) |
| TL;DR / summary / key findings | **Lead** section — lead paragraph + a pull-quote for the single sharpest takeaway |
| Each `##` section | one `.slide` with `.slide-tag` + `.slide-num` |
| Tables (comparison/decision/coverage) | comparison-table component (below) |
| Bulleted options / approaches / clusters | `.card` grid (one `.card.dark` for the punchline per row) |
| The recommendation / chosen path / hottest topic | `.track-box` (accent left border) |
| Quotes (community voices, sources) | `.pull-quote`, **HTML-escaped** (see security) |
| Links / sources | inline `<a>`; keep every source link from the markdown |
| Risks / open questions | final cards or a closing statement |

Per-skill anchors (use the report you are given; do not invent content):
- **brainstorm** → cover · problem · evidence · options · recommendation · risks · handoff · closing.
- **create-plan** → cover · goal · phases (one card each) · dependencies · acceptance · risk. (`plan.md` stays
  primary; `plan.html` is a readable companion — do not change the cook handoff contract.)
- **rebuild-spec** → cover · overview · requirements · architecture · sections · open questions.
- **kensan** → cover · TL;DR · 🔥 hot topics (table) · per-topic cards · deep-dive sections (how-it-works,
  evidence, community pulse, what-to-learn). Render hot-topic heat and scores as mono labels.

## Components

Cards:

```css
.card { background: var(--paper-warm); padding: 36px 32px; border: 1px solid var(--hairline); }
.card.dark { background: var(--ink); color: var(--paper); border-color: var(--ink); }
```

- No border-radius. No shadow. One dark card per row for the punchline. Mono `.card-mark` index top-right.

Track box (recommended option / strongest claim / validation plan):

```css
.track-box { border-left: 3px solid var(--accent); background: var(--paper-warm); padding: 40px 44px; }
```

Pull quote (at most one per section):

```css
.pull-quote {
  border-left: 2px solid var(--accent);
  padding: 12px 0 12px 40px;
  font: 300 italic clamp(28px, 3.6vw, 48px)/1.25 var(--serif);
}
```

Comparison table: header mono 10px uppercase muted; header + final row bottom rule 1.5px solid ink;
intermediate rows hairline dividers; first column serif 500; featured column `rgba(184,35,44,0.04)`.

## Motion

One reveal primitive only:

```css
.reveal { opacity: 0; transform: translateY(24px); transition: opacity .9s cubic-bezier(.22,1,.36,1), transform .9s cubic-bezier(.22,1,.36,1); }
.reveal.visible { opacity: 1; transform: translateY(0); }
@media (prefers-reduced-motion: reduce), print {
  .reveal { opacity: 1; transform: none; transition: none; }
}
```

No parallax, scroll-jacking, bouncing, gradient animation, or decorative blobs.

## Diagrams (optional)

If the report benefits from a flow/architecture diagram, you may include Mermaid via CDN
(`https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js`). It is the **only** allowed external dependency;
the page must still read correctly with no network. Do not add other CDN libraries.

## Security (untrusted content)

When the report embeds quoted external content (kensan community quotes, fetched article text, KOL posts),
**HTML-escape it** before inserting into the page (`&`, `<`, `>`, `"`). Never inject raw fetched HTML or
`<script>` from a source. The HTML report is a document, not an app — no fetch, no eval, no remote data.

## Do / Don't

Do: pair every number with a mono uppercase label + one-sentence explanation; structure with hairlines and
whitespace; keep headings short and declarative; **preserve diacritics when Vietnamese appears** in user content.

Don't: no emojis (except where the source report's section markers like 🔥 are meaningful — render as small mono
glyphs, not decoration); no stock icons; no gradients; no drop shadows; no rounded cards; no pure-white page; no
SaaS landing-page hero.

## Minimum Section Template

```html
<section class="slide" id="recommendation">
  <span class="slide-tag">■ 05 · Recommendation</span>
  <span class="slide-num">05 / 08</span>
  <div class="container">
    <div class="reveal">
      <h4>Decision</h4>
      <h2>Build the narrow path.<br><em>Validate the risky premise.</em></h2>
    </div>
    <div class="three-col reveal" style="margin-top: 60px;">
      <div class="card"><div class="card-mark">01</div><h4>Why</h4><h3>Lowest reversible risk</h3><p>Body.</p></div>
      <div class="card"><div class="card-mark">02</div><h4>Watch</h4><h3>Assumption to test</h3><p>Body.</p></div>
      <div class="card dark"><div class="card-mark">03</div><h4>Next</h4><h3>Plan handoff</h3><p>Body.</p></div>
    </div>
  </div>
</section>
```
