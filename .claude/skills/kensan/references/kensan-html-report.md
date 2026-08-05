# Kensan HTML report — dense single-page

The HTML contract for kensan's `--html` (briefing · deep-dive · rollup). **Different from**
`../_shared/references/editorial-report-html.md`: that one is a sparse magazine (full-viewport slides,
"summarize"); this one is a **dense single-page report** that matches the markdown's detail and adds a crawl
provenance section. The markdown report stays primary; the HTML is a companion at the same path with `.html`.

## Hard rules
- **Self-contained:** one `.html`, inline CSS + JS, no build, no network (one optional Mermaid CDN tag is the
  only allowed external dependency; the page must read fine without it).
- **Single dense page:** sections stack in normal document flow — **no `min-height:100vh`, no slideshow, no
  tabs/accordions/modals.** Everything is visible on one scroll, like reading a report. A thin sticky top bar
  with anchor links is fine; content is never hidden behind interaction.
- **Markdown parity:** render the report's **full** detail — do NOT summarize or drop sections. Every table,
  grouped list, quote, link, and number in the markdown appears in the HTML.
- **HTML-escape** all quoted community/source text (`&`, `<`, `>`, `"`). Never inject raw fetched HTML/script.
- **Preserve diacritics** for Vietnamese content.
- **Code / diagrams:** render fenced blocks (```` ``` ````) as a styled monospace `<pre>` (preserve whitespace,
  horizontal scroll, escaped) — this carries the deep-dive's code/commands and the ASCII architecture diagram.
  A ```mermaid block may render via the optional Mermaid CDN, else fall back to the escaped `<pre>` source.

## Visual tokens (reuse the editorial palette, dense rhythm)
Reuse the tokens from `../_shared/references/editorial-report-html.md` (`--ink #0a0a0a`, `--paper #faf7f2`,
`--paper-warm #f0ebe1`, `--accent #b8232c`, `--muted #6b6258`, hairlines; serif display `Fraunces/Georgia`, mono
labels, sans body). But use a **dense report rhythm**, not magazine whitespace:
- Section padding ~`40px 6vw` (not `60px 8vw`), section heading `clamp(24px,3vw,38px)`, body 15px/1.6.
- Sections separated by a 1px hairline; no full-viewport gaps.
- Tables are first-class (comparison/decision/provenance): mono uppercase headers, hairline rows, ink rule top+bottom.
- Stat bands: a row of `label / big-number / one-line` cells for counts.

## Page structure
1. **Cover / meta** — title, window/date, scope, run counts. Compact (not a full screen).
2. **TL;DR / period overview** — lead paragraph + the key narrative (full, not trimmed).
3. **Body sections** — one `<section>` per `##` in the markdown, rendered in full (tables → tables, grouped
   lists → grouped lists).
4. **Sources & crawl provenance** *(mandatory)* — see below.
5. **Carry-forward / open questions.**
6. **Coverage footer** — what was read, window, ledger size.

## Sources & crawl provenance section (v1 = counts)
Render the provenance the skill provides (briefing: the run's `_provenance`; rollup: `stats_store.py aggregate`
output). v1 shows **counts by platform** as a stat band + a small table; the per-source list (with links) is
captured in the data for a later pass — don't block on it.

```
SOURCES & CRAWL PROVENANCE
[ youtube 13 ] [ github-releases 22 ] [ github-user 9 ] [ rss 47 ] [ arxiv 98 ] [ hf-papers 27 ] [ hn 23 ] [ bluesky 20 ] [ social (best-effort) ]

| Platform | Items | Notes |
|----------|-------|-------|
| arxiv    | 98    | papers |
| rss      | 47    | blogs/newsletters |
| …        | …     | … |
```
If a run lacked stats (older reports), state "provenance available for N of M reports" rather than implying full coverage.

## Per-mode content maps
- **briefing** → cover · TL;DR · 🔥 hot topics (table) · 🆕 new (cards/list, full) · 🔄 updates · skim list ·
  **provenance** (the run's `_provenance`) · coverage.
- **deep-dive** → cover · TL;DR · then the body sections **of whichever deep-dive template was used** (the
  subject decides the shape — render each `##` in full, do not reshape):
  - *technology* → context · **how-it-works (step-by-step mechanism prose + architecture/data-flow diagram +
    worked example/trace + key params & rationale)** · using-it/reproducing · evidence/methodology (tables) ·
    limitations/failure-modes · community pulse · what-to-learn/try.
  - *github-activity* → **KOL-contribution table** · **trending-repo leaderboard (stars/lang/why)** · repo
    spotlight(s) · story threads · who-to-watch/try.
  - *x-topic* → discourse map (camps + quotes) · post leaderboard · consensus vs debate · signal-vs-hype · primary check.
  - *youtube* → creator/video role map · video leaderboard · mined transcript content · signal-vs-hype · watch/skip.
  - always ends with · open questions · **provenance** (topic-scoped) · sources. Render leaderboards as tables and
    multi-paragraph prose in **full** (do not collapse into bullets).
- **rollup** → cover · period overview · topics×takeaway (table) · what's-new grouped · carry-forward ·
  **provenance** (aggregated by `stats_store.py aggregate`) · coverage.

## Security
A document, not an app: no remote fetch, no eval, no live data. Quoted untrusted text is escaped. Mermaid CDN
optional and non-essential.
