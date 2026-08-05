# The llms.txt standard — a working guide

Origin: [llmstxt.org](https://llmstxt.org/). This is a working interpretation the skill leans on — reading this is enough; no need to open the source spec mid-build.

## What llms.txt is

A markdown file at a site's root, written for **an agent to read, not a human to browse**. Context windows are too narrow to swallow a whole website; llms.txt is a *curated table of contents* — it points the agent straight at what it needs, with one line per link saying what that link holds.

It does not replace the docs. It is the map that leads into them.

## Hard rules and soft rules

| Element | Level | Rule |
|---|---|---|
| **H1** | Required | Product name. The one thing that *must* be present. |
| **Blockquote** | Strongly recommended | One sentence summarizing the product: what it is, who it's for, core value. |
| **Body paragraphs** | Optional | A few context paragraphs/lists, if needed. |
| **H2 sections** | Optional | Group related links under each `##`. |
| **`## Optional`** | Special | Place LAST. Signals to the agent: this part is skippable when context is tight. |

## Link syntax

```markdown
- [Title](path): a short description of what this link holds
```

Each item is a markdown hyperlink followed by a colon and a description. The description is what the agent reads to **decide whether to open the link** — without it, the map loses half its value.

## Two files, two roles

| File | Role |
|---|---|
| `llms.txt` | The index: links + descriptions. The agent reads it to orient, then opens what it needs. |
| `llms-full.txt` | Content inlined (no external links to follow). The agent loads it once and understands everything. Produced with the `--full` flag. |

## How to write it well

Three things decide whether the file is usable:

- **The blockquote must answer "what is this product" in one breath.** The agent reads it first; if it's vague, everything after loses its bearings.
- **Write each link description from the angle "what does the agent need to know to decide whether to open it".** Not a summary of the file, but *when it is needed*.
- **Sections are how the agent locates things fast.** Group by domain (Overview, Features, API, Flows), and push look-up-when-needed material down to `## Optional`.

The rest is ordinary discipline: relative paths within the repo (a full base URL if web-hosted), one canonical link per topic, plain language with no bare jargon.

## Example (an internal platform)

Take a genuine agent-first setting: an internal operations portal where an agent acts on a person's behalf (request equipment, adjust timesheets).

```markdown
# Asset & Timesheet Portal

> An internal portal where employees — and agents acting for them — raise equipment requests, manage assigned assets, and handle timekeeping, including making up missing hours at month-end.

## Overview

- [Overview](docs/system/overview.md): what problem the portal solves, who uses it
- [Architecture](docs/system/architecture.md): the main services and data flow

## Features

- [Feature list](docs/generated/feature-list.md): the full set of capabilities
- [Asset request](docs/features/asset-request/technical-spec.md): create a device grant/replacement request
- [Timesheet adjustment](docs/features/timesheet-adjust/technical-spec.md): detect missing hours and file a make-up form

## API

- [API map](docs/generated/api-map.md): endpoints by business domain

## Flows

- [Request approval flow](docs/flows/asset-approval.md): steps from creation to grant

## Optional

- [Changelog](CHANGELOG.md): change history
- [Asset policy](docs/asset-policy.md): allocation rules
```

## Signs of a broken file

- **A directory, not a map** — every URL dumped in without curation.
- **Mute links** — no description; the agent must open each one to learn what it is.
- **Descriptions that swallow the page** — so long they defeat the point of "concise".
- **One endless flat plane** — a long list with no sections, no priority order.
- **Broken paths** — relative URLs when the file is web-hosted and the base is missing.

## Validation gate (the skill self-checks before writing)

- [ ] H1 present (product name).
- [ ] Blockquote summary present (no `<TODO>` left).
- [ ] Every link uses `[title](path): desc` syntax and **has a real description**.
- [ ] No empty section.
- [ ] `## Optional` (if present) is last.
