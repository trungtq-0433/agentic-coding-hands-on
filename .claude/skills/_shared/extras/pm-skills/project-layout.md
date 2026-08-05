# Canonical Project Document Layout

The single source of truth for **where project documents live and what they are called**. Every skill and
agent in this kit reads and writes these paths verbatim — never invent a variant prefix (`docs/`,
`documents/`, `project-docs/`) or a variant filename. If a path is not listed here, it is not part of the
managed layout.

## 1. The Tree

All managed documents live under **`project/`** at the repository root.

```
project/
├── 01_management/
│   ├── overview.md                       # contract, org, way of working, constraints   (PLAN)
│   ├── stakeholders.md                   # organization, approval & escalation flow     (PLAN)
│   ├── qa.md                             # open items for the customer (planning)       (PLAN)
│   ├── schedule.md                       # master schedule, milestones, WBS             (SCH)
│   ├── progress.md                       # actual progress against plan                 (REP)
│   ├── task-list.md                      # tasks + GitHub Issue links                   (TASK)
│   ├── define-dod.md                     # completion criteria, closing judgement       (DOD)
│   ├── decision.md                       # settled decisions (JP-PM; skills never edit)
│   ├── stories/
│   │   └── story-{WBS ID}-{name}.md      # story details                                (STORY)
│   ├── reports/
│   │   └── {YYYY-MM-DD}-weekly-report.md # client-facing weekly report                  (REP)
│   ├── risks-problems/
│   │   ├── risk-list.md                  # risks (not yet happened)                     (RISK)
│   │   └── problem-list.md               # issues (already happened)                    (RISK)
│   └── mtg-logs/                         # meeting minutes (input only)
├── 02_requirements/
│   ├── system-overview.md                # service overview, background, objectives     (REQ)
│   ├── role-list.md                      # roles + permission matrix                    (REQ)
│   ├── function-list.md                  # function list (scope)                        (REQ)
│   ├── non-function-list.md              # non-functional requirements                  (REQ)
│   ├── glossary.md                       # glossary                                     (REQ)
│   ├── qa.md                             # open items for the customer (requirements)   (REQ)
│   └── functions/                        # per-function details (requirement-analysist)
├── 03_basic-design/
│   └── system-design/architecture.md     # read-only input for TEST
├── 04_screen-design/
│   └── screen-list.md                    # formal screen design (later phase)
├── 05_test/
│   ├── test-plan.md                      # test plan                                    (TEST)
│   ├── test-schedule.md                  # test milestones + test WBS                   (TEST)
│   ├── qa.md                             # open items for the customer (test)           (TEST)
│   └── testcase/                         # test cases (test execution phase)
└── 07_feedbacks/
    ├── feedback-list.md                  # day-to-day feedback tracker                  (FB)
    └── change-request.md                 # change requests (CR)
```

`plans/project-management/` (the reserved JP-PM scratch root; `screens/` is the `WF` wireframe
workspace) sits **outside** `project/` on purpose — it is an exploratory scratch area, not a managed
deliverable. It also holds **`jp-pm-memory.md`** — the `jp-project-manager` agent's own working notes
(which skill got how far, `What to do next`, `GitHub Settings`). That file is agent state, not a project
deliverable: the kit ships none of it, the agent creates it on first run, and it is deliberately kept out
of any harness-specific directory so the same notes are found whichever coding agent runs this kit.

## 2. Naming Rules

- **Prefix is always `project/`**, never `docs/`. The numbered phase folders (`01_management`,
  `02_requirements`, …) are part of the path and never abbreviated.
- The requirements overview is **`system-overview.md`** (not `project-overview.md`). `overview.md` under
  `01_management/` is a different document (contract & organization) — never conflate the two.
- Story files are `stories/story-{WBS ID}-{name}.md`, e.g.
  `story-E-01-S01-business-requirements-interview.md`. The WBS ID is inherited verbatim from
  `schedule.md` §3.
- Weekly reports are `reports/{YYYY-MM-DD}-weekly-report.md`.

## 3. Missing Files Are Normal — Never Dead-End

This kit ships **no `project/` tree**. A consumer installs it into a repository that may have nothing under
`project/` at all, so every skill must handle "the file is not there yet".

- **The owning skill creates its own files.** Each skill listed above owns a set of files and ships their
  skeletons in `references/skeletons.md`. When an owned file is missing or empty, `Write` it from that
  skeleton and continue — never stop with "the template cannot be found".
- **Files you do not own are read-only, and their absence is data.** Treat a missing `schedule.md` the same
  way you treat one whose §3 holds only `<!-- e.g. ... -->` examples: "not started". Report it and point at
  the skill that owns it (`pm-plan-schedule`/SCH here) instead of creating it yourself.
- **A skeleton is not content.** Creating the file from a skeleton never counts as filling it in — the
  interview still has to happen, and the placeholder rows still have to be replaced.
