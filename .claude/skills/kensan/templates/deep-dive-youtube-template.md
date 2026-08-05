# 研鑽 Deep Dive — YouTube KOL pulse — {{window}} — {{date}}

<!--
  Use this template when the deep-dive subject is a cluster of YOUTUBE videos from
  the KOL watch list — i.e. "what are the creators covering, what's signal vs view-
  bait, and what's the actual technical content". NOT a single technology's mechanism
  (technical template) and NOT a GitHub-activity cluster (github-activity template).

  Discovery is the channel RSS feed (title + description + view count). When yt-dlp
  is installed, recent items also carry a [transcript] — mine it for real content.
  When a transcript is blocked/auth-walled, SAY SO and do not quote as if you had it.

  Fill rules:
  - Every video carries its link + channel + view count (view = n/a if unknown).
  - Describe what a video EMPHASISES (from description/transcript), not what the
    title teases. NEVER invent quotes or numbers; mark transcript-blocked items.
  - View ≠ value: rank teaching/signal separately from reaction/drama.
  - If the topic has a real primary (paper/model card), pull the mechanism from THERE,
    not from a creator's title. Don't pad a thin section.
-->

## TL;DR
- **Dominant theme(s):** {{the 1–2 axes the creators are circling}}
- **Highest-signal video:** {{title — channel}} — [{{link}}]({{url}})
- **Highest-view (often drama):** {{title — channel — views}} — [{{link}}]({{url}})
- **Watch this, skip that:** {{the concrete steer}}

## Context — why this is hot this week
{{2–3 sentences: the release/event the creators are reacting to, and where the real
learning is vs the noise. Link the trigger.}}

## Creator / video map by role
{{Group the videos by what they actually deliver. This separation is the point.}}

### Reaction / drama (high view, low learning)
- {{channel}} — "{{title}}" ({{views}}) — {{what it really is: hype-tracking, not technical}} — [↗]({{url}})

### Signal / teaching
- {{channel}} — "{{title}}" ({{views}}) — {{the substantive point it makes}} — [↗]({{url}})

### Conference / deep (high quality, often low view)
- {{channel/event}} — "{{title}}" ({{views}}) — {{why it's worth the time}} — [↗]({{url}})

## Top videos leaderboard
| Video | Channel | Views | Value | Link |
|-------|---------|-------|-------|------|
| {{title}} | {{channel}} | {{views / n/a}} | {{signal / teaching / drama}} | [↗]({{url}}) |

## The actual technical content
{{Mine the high-signal videos' transcripts/descriptions for the real substance — the
mechanism, the claim, the demo result. Quote verbatim where the transcript is
available; where it's blocked, state that and rely on a linked primary instead.
This is the depth: what a viewer would actually learn, distilled + sourced.}}
- {{technical point}} — "{{verbatim from transcript}}" — [{{channel}}]({{url}})
- {{point with blocked transcript}} — *transcript not retrievable; per primary:* {{claim}} — [{{primary}}]({{url}})

## Signal vs hype check
- {{view-vs-value mismatch: which big-view videos are escalating-title rage-bait}}
- {{any "X beats Y" / "self-improving" style claim that the primary doesn't support}}

## What to watch / skip
- **Watch:** [{{video}}]({{url}}) — {{why — the real learning}}
- **Skip / skim:** {{channel/pattern}} — {{why it's noise}}

## Open questions
- {{unresolved — claim awaiting a primary, transcript that couldn't be read, etc.}}

## Sources & crawl provenance
- YouTube: {{N}} videos ({{window}}) · transcripts mined: {{N via yt-dlp}} · blocked: {{N}}
- Videos read deeply / primaries followed: [{{}}]({{url}}) · [{{}}]({{url}})
