# Skeleton for the Files This Skill Owns

`Write` a new story file from this skeleton whenever you elaborate a story — there is no shared template
file to copy from, and the kit ships none. Never overwrite an existing story file without permission; see
the layout rule [`skills/_shared/extras/pm-skills/project-layout.md`](../../_shared/extras/pm-skills/project-layout.md) §3.

File name: `project/01_management/stories/story-{WBS ID}-{name}.md`, e.g.
`story-E-01-S01-sign-in.md`. The WBS ID and the story name are inherited **verbatim** from
`schedule.md` §3 — never renumber or rename them.

---

## `project/01_management/stories/story-{WBS ID}-{name}.md`

```markdown
# {Story ID}: {Story name}

## 1. Story Information

| Item | Value |
| --- | --- |
| Story ID | <!-- E-01-S01, from schedule.md §3 --> |
| Story name | <!-- from schedule.md §3 --> |
| Related Epic | <!-- E-01 --> |
| Related function IDs | <!-- F-001, from function-list.md --> |
| Priority | <!-- from function-list.md --> |
| Status | <!-- Drafting details / Details written --> |
| Created on | <!-- YYYY-MM-DD --> |

## 2. User Story

<!-- One sentence: "As a <role>, I want to <do something> because <reason>." -->

## 3. Background & Purpose

<!-- The problem this story solves and why it matters. -->

## 4. Target Users

<!-- The roles that use it, by ROLE-ID from role-list.md, and how they differ. -->

## 5. Scope

**In scope**
<!-- What this story covers. -->

**Out of scope**
<!-- What it explicitly does not cover, and where that lives instead. -->

## 6. Main Business Flow

**Happy path**
<!-- 1. … 2. … 3. … -->

**Alternate & exception flows**
<!-- What happens when it goes wrong: validation failure, no permission, no data. -->

## 7. Data Requirements

| Item | Source | Display-only or editable | Notes |
| --- | --- | --- | --- |
| <!-- e.g. display name --> | <!-- entered here / from an upstream system --> | <!-- display-only / editable --> | |

## 8. Technical Constraints & Non-Functional Considerations

<!-- Target devices, external APIs, infrastructure requirements, and the related NFR-IDs. -->

## 9. Acceptance Criteria

> **Never leave this section empty** — it is the basis used by the design work and `pm-create-tasks`.
> At minimum, put down a starting draft.

- [ ] <!-- a condition that can be objectively verified -->

## 10. Assumptions & Open Items

| # | `[ASSUMPTION]` / open item | Rationale | Who confirms | By when |
| --- | --- | --- | --- | --- |
| 1 | <!-- what was assumed because the answer was "I don't know / later" --> | | | |

## 11. Related Documents

<!-- The relevant F-IDs / NFR-IDs / D-IDs and a link to this story in schedule.md §3. -->

## 12. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- pm-create-stories skill --> | <!-- created --> |
```
