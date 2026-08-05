# Documentation Triggers

## When to Update Docs

The docs in `./docs` MUST be brought current whenever:

| Trigger | Which Docs | Action |
|---------|-----------|--------|
| Phase status changes | project-roadmap.md | Update progress %, milestone status |
| Major feature complete | project-roadmap.md, codebase-summary.md | Add feature, update architecture |
| Bug fix (significant) | project-roadmap.md | Document fix, severity, impact |
| Security patch | project-roadmap.md, system-architecture.md | Record improvement |
| API contract changes | system-architecture.md, code-standards.md | Update endpoints, schemas |
| Architecture decision | system-architecture.md | Document decision + rationale |
| Scope/timeline change | project-roadmap.md | Adjust phases, dates |
| Dependencies updated | system-architecture.md | Record version changes |
| Breaking changes | code-standards.md | Document migration path |

## Documentation Files

```
./docs/
├── project-overview-pdr.md     # Product requirements
├── code-standards.md           # Coding conventions
├── codebase-summary.md         # Architecture overview
├── design-guidelines.md        # UI/UX standards
├── deployment-guide.md         # Deploy procedures
├── system-architecture.md      # System design
└── project-roadmap.md          # Milestones & progress
```

## Update Protocol

1. **Read current state:** Open the target doc before you touch it
2. **Analyze reports:** Go through the agent reports in the plan's reports directory
3. **Update content:** Move the progress %, the statuses, the dates, the descriptions
4. **Cross-reference:** Make sure the docs still agree with each other
5. **Validate:** Confirm the dates, versions, and references hold up

## Quality Standards

- **Consistency:** One formatting and versioning style across the whole set
- **Accuracy:** Progress %, dates, and statuses match what's actually true
- **Completeness:** Enough detail to brief a stakeholder
- **Timeliness:** Land the update in the same session as the change that prompted it
- **Traceability:** A visible thread from each roadmap item to the code that built it

## Delegation Pattern

Hand documentation updates to the `doc-writer` subagent:

```
Task(
  subagent_type: "doc-writer",
  prompt: "Update ./docs for [changes]. Work context: [path]",
  description: "Update docs"
)
```

The project manager decides WHEN; the doc-writer works out HOW.
