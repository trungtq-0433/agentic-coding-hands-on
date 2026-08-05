# 研鑽 Deep Dive — GitHub activity — {{window}} — {{date}}

<!--
  Use this template when the deep-dive subject is GITHUB ACTIVITY (a cluster of
  github-user / github-trending / github-releases / goodailist items) — i.e. "who
  shipped what, which repos are hot today", NOT a single technology's mechanism.
  For a single paper/system/release, use technical-deep-dive-template.md instead.

  Focus, in order: (1) what the KOLs you track actually shipped, (2) the day's
  trending/popular repos (goodailist-style leaderboard), (3) a deeper look at the
  1–3 standout repos.

  Fill rules:
  - Every repo/person/claim carries a link (github.com/<repo|user>). No link → drop.
  - NEVER invent star counts, dates, languages, or descriptions. Read them from the
    repo via `gh` (API-free); if a field is unknown, write "n/a".
  - Judge AI-relevance and novelty from the repo's description + topics + README —
    not the name. Say plainly when an item is routine (not a new development).
  - Separate genuinely NEW/notable from noise. Don't pad; a thin section gets one line.
-->

## TL;DR
- **Standout contribution:** {{KOL + what they shipped + why it matters}} — [{{repo}}]({{url}})
- **Top trending repo:** {{repo — what it is — stars}} — [{{repo}}]({{url}})
- **What to actually look at today:** {{the one or two things worth your time}}
- **Skip / don't misread:** {{a hyped-but-routine item, or a common misreading}}

## KOL contribution highlights
{{Per notable person you track: the most significant thing they did in the window —
a NEW repo, a release, a substantial push to their own project, an opened PR/issue
that signals direction. Lead with substance (what it does, from description+topics),
not the event verb. Skip routine churn.}}

| KOL | Activity | What it is (from desc/topics) | New? | Link |
|-----|----------|-------------------------------|------|------|
| {{@user}} | {{released/created/pushed}} | {{one line — lang · topics}} | {{🆕 new / update / routine}} | [{{repo}}]({{url}}) |

- **Pattern across KOLs:** {{any shared theme — several people touching the same area, a tool everyone forked, etc., with links}}

## Trending / popular repos today (goodailist-style)
{{Ranked leaderboard of the day's hot AI repos — from goodailist + github-trending.
Rank by stars (and the day's momentum where known). State what each IS and why it's
trending; don't infer from the name.}}

| # | Repo | Stars | Lang | What it is | Why trending | Link |
|---|------|-------|------|-----------|--------------|------|
| 1 | {{owner/repo}} | {{★ count}} | {{lang}} | {{one line}} | {{release / HN / viral / new}} | [↗]({{url}}) |

- **Momentum note:** {{which are brand-new vs steadily climbing; star velocity if known}} — mark "n/a" when not measured.

## Standout repo spotlight(s)
{{Pick 1–3 repos worth a closer look and READ their README + a core file via `gh`.
For each: what it does, how you'd use it (the key command/snippet, linked), who it's
for, and an honest "should you care?". This is the depth — repo-centric, not a
technology-mechanism essay.}}

### {{owner/repo}} — [{{url}}]({{url}}) · {{★}} · {{lang}} · {{created/updated}}
- **What it does:** {{from the README, the real capability}}
- **How to use:** `{{key command / snippet — copied + linked}}`
- **Why it's getting attention:** {{the actual hook}}
- **Honest read:** {{is it substantive or hype? mature or 1-day-old? benchmark-backed or claim-only?}}

## Story threads (cross-repo narrative)
{{When several activities form one story — a distillation drama, everyone shipping
MCP servers, a model + the tools built around it — tell it in a few sentences with
links. Skip if the day is just unrelated items.}}

## Who to watch / what to try
- **Watch:** {{KOL/repo to keep an eye on next run}} — {{why}} — [{{url}}]({{url}})
- **Try:** {{a repo to clone / a command to run}} — {{what you'll learn}} — [{{url}}]({{url}})

## Open questions
- {{unresolved — e.g. "is repo X actually maintained or a one-off dump?"}}

## Sources & crawl provenance
- Backends: {{gh / api counts}} · github-user {{N}} · github-trending {{N}} · goodailist {{N}} · github-releases {{N}}
- Repos/people read deeply: [{{repo}}]({{url}}) · [{{…}}]({{url}})
