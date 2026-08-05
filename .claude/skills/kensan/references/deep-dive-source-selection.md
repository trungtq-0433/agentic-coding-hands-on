# Deep-Dive Source Selection

A deep-dive's quality comes from reading the RIGHT few primary sources deeply, not skimming many. Pick 2–5
artifacts to actually read (WebFetch / arxiv abstract / repo README), then synthesize.

## Pick the template (match the report to what the cluster IS)

The deep-dive's *shape* must fit its subject — don't force a technology-mechanism essay onto a list of GitHub
activity. Choose by the cluster's dominant content:

| If the cluster is… | Use template | Focus |
|--------------------|--------------|-------|
| one technology / paper / model / release with a mechanism to explain | `technical-deep-dive-template.md` | how it works, reproduce, benchmarks |
| GitHub activity — KOL contributions + trending repos (github-user / github-trending / github-releases / goodailist items dominate) | `deep-dive-github-activity-template.md` | who shipped what · trending leaderboard · repo spotlight |
| a topic's discourse on X/Twitter (takes, who's saying what) | `deep-dive-x-topic-template.md` | discourse map · post leaderboard · signal vs hype |
| a cluster of YouTube videos from the KOL list | `deep-dive-youtube-template.md` | role map · video leaderboard · mined transcript content |

Mixed cluster → pick the template matching the **dominant** source type; fold the minority in as a "story
thread" / cross-link. When in genuine doubt between technology vs activity, ask: *is there one thing whose
mechanism I must explain* (→ technical) *or many actors/items to map* (→ activity/pulse).

## Prefer primary over secondary

1. **The thing itself** — the paper (arXiv), the repo (README + key code + release notes), the official blog/post.
2. **The author's own explanation** — a thread/talk by the people who built it.
3. Only then **secondary** — a news recap, a reviewer's writeup — and only to find the primary it points to.

A news headline ("X released, +12%") is a pointer, not a source. Follow it to the primary.

## Selection signals

- **Authority:** built/written by the people responsible; an official channel.
- **What the community cites:** if every HN/Reddit thread links the same paper or repo, read that.
- **Substance density:** a 2-page method section beats a 20-tweet hype thread.
- **Recency + relevance:** within the window, on-topic for the cluster.

## Budget

Default depth: **1 topic, deep**. Read 2–5 primary artifacts + the discussion set. If a source is paywalled or
unreachable, note it and move on — never block. Spend the reading budget on understanding *how it works* and
on the strongest community voices; skim the rest.

## Read the parts that explain the mechanism

Skimming the abstract/intro is what produces a shallow report. Go to where the HOW lives:

- **Paper:** the **method / approach / architecture section**, the **main results table**, and the **figure
  captions** (they often state the mechanism most plainly). The abstract is a pointer, not the substance.
- **Repo:** the README's usage section **plus the core source file(s)** — open the actual module that implements
  the idea, name the functions/classes, and copy the key snippet. Read an `examples/` file and the release notes.
  Fetch raw files with `gh` (it routes API-free, no 60/h cap).
- **System / product / pricing:** the docs' **how-it-works**, the **config/parameters**, and the **limits/pricing**
  page where the real numbers live.

## Extraction checklist (what to pull out, per source)

For each primary you read, capture the raw material the report is built from:

1. **Mechanism** — the steps in order, and *why* each step exists.
2. **Architecture / data flow** — the components and how data/control moves (enough to draw).
3. **A worked example** — one concrete input → steps → output, with real values.
4. **Parameters & defaults** — the knobs, their effect, and the authors' stated design rationale.
5. **Commands / code / config** — the minimum to run or apply it, copied verbatim (+ link).
6. **Evidence + methodology** — the actual numbers and how they were measured.
7. **Limitations / failure modes** — what the source itself admits it can't do.

If you cannot fill 1–3 from what you read, you have not read deeply enough — go back to the method section or the
core code before synthesizing. Never fill these by guessing.

## Output

A short ranked list of the artifacts you read (with links **and which section/file**) feeds the deep-dive's
"How it works" and "Sources" sections, so the reader can retrace your path.
