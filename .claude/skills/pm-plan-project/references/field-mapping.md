# Field Mapping (Input → Output)

A mapping showing which input the `pm-plan-project` skill fills each section of the two output files (`overview.md` / `stakeholders.md`) from. **For every item, first try to extract it from the documents, and only send the items that remain unfilled to the interview (`hearing.md`).**

> The service overview, background problems and objectives (`project/02_requirements/system-overview.md`) are out of scope for this skill. The `pm-gather-requirements` (REQ) skill owns them.

Legend: 📄 = proposal, 🗒️ = project brief (client brief), 💰 = estimate, 💵 = cost sheet, 💬 = interview required

## `project/01_management/overview.md`

| Section | Cell | Primary source | Secondary | Notes |
| --- | --- | --- | --- | --- |
| §1 Basic info | Project name | 📄/🗒️ | 💰 | |
| | Project code | — | — | 💬 (internal slug; never appears in the documents — propose candidates and confirm) |
| | Client name | 📄/💰/💵 | 🗒️ | |
| | Contract type | 💰 (states fixed-price / quasi-delegation etc.) | 📄 | Even when stated in the documents, **always re-confirm with a confirmation question** (the principle of identifying the contract model first) |
| | Contract period | 💰/📄 | 💵 (billing period) | |
| | Project type | 📄/🗒️ | — | 💬 if ambiguous |
| §2 KPI & success criteria | KPI table | 📄 (if present) | 🗒️ | Treat what 📄 says as a **draft candidate**. If the numbers are not measurable, settle them via 💬 |
| | Success criteria (prose) | 📄 | 🗒️ | 💬 if ambiguous |
| §3 Way of working | Development method / sprint length | 📄 | — | |
| | Communication channels | — | — | 💬 required (the template itself states "undecided") |
| | Ticket management tool | — | — | 💬 required |
| §4 Scope & role split | Who performs each work item (Sun* / client / joint) | 📄 (if scope is stated) | 💰 (contracted scope) | Check that it does not contradict the scope in the contract and proposal. Even when 📄 states it, **re-confirm together with the contract type (fixed-price / quasi-delegation)** (e.g. under a fixed-price contract Sun* bears strong responsibility for the deliverable, whereas quasi-delegation tends to assume client involvement). Express who does *not* handle something (out of scope) in the "Performed by" column — do not create a separate "out-of-scope" subheading |
| §5 Constraints | Technical constraints, budget & resource constraints | 📄 | 💵 (budget cap) | Supplement via 💬 |
| §6 Requirements to uphold (D/C/Q/S) | Memo for each category | Present the tone of 📄 as a hypothesis | — | Always settle via 💬. Never decide without permission |
| | Trade-off sliders (14 pts total) | — | — | 💬 required. The judgement is always the user's |
| §7 Revision history | — | The skill appends automatically on change | — | Do not create a "Related documents" section (it is already in GUIDE.md). With that removed, the revision history becomes the final numbered section |

## `project/01_management/stakeholders.md`

| Section | Cell | Primary source | Secondary | Notes |
| --- | --- | --- | --- | --- |
| §1 Client organization | Role / name / affiliation / contact / authority | — | 📄 (company name at most) | Real names and contacts are almost never in the documents → 💬 required |
| §2 Sun* organization | Role / name / affiliation / contact / authority | 💵 (role × headcount × rate structure) | 💰 | 💵 is the strongest source. Fill in missing names and contacts via 💬 |
| §3 Decision-making & approval flow | Who proposes / reviews / approves | — | — | 💬 required |
| §4 Escalation flow | Contact and response time per level | — | — | 💬 required |
| §5 Contact & communication channels | Channel and frequency per purpose | — | — | 💬 required. **Reflect the same answer in both this and the communication channels in overview.md §3** (never interview twice) |
| §6 Revision history | — | The skill appends automatically on change | — | |

## Items That Can Never Be Taken From the Documents and Always Require an Interview (summary)

- Project code (internal slug)
- Communication channels / ticket management tool (shared by overview.md §3 and stakeholders.md §5)
- Real names and contacts on the client and Sun* sides (the gaps in stakeholders.md §1 and §2)
- Decision-making & approval flow, escalation flow (stakeholders.md §3 and §4)
- The 14-pt D/C/Q/S trade-off allocation and the memo for each category (overview.md §6)
- Concrete KPI numbers (when the proposal only states them qualitatively)
- Who performs each work item in the scope & role split (overview.md §4; include who does *not* handle something in the "Performed by" column. Even when stated in the proposal, always insert a confirmation question together with the contract type)
