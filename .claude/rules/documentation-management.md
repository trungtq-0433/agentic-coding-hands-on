# Project Documentation Management

### Roadmap & Changelog Maintenance
- **Project Roadmap** (`./docs/development-roadmap.md`): a living document that tracks the project's phases, milestones, and progress.
- **Project Changelog** (`./docs/project-changelog.md`): the running record of every significant change, feature, and fix.
- **System Architecture** (`./docs/system-architecture.md`): the running record of every significant change, feature, and fix.
- **Code Standards** (`./docs/code-standards.md`): the running record of every significant change, feature, and fix.

### Automatic Updates Required
- **After Feature Implementation**: move the roadmap progress forward and add changelog entries.
- **After Major Milestones**: revisit the roadmap phases and refresh the success metrics.
- **After Bug Fixes**: log the fix in the changelog with its severity and impact.
- **After Security Updates**: note the security improvements and version bumps.
- **Weekly Reviews**: refresh progress percentages and milestone statuses.

### Documentation Triggers
The `project-manager` agent MUST refresh these documents when:
- A development phase changes status (e.g. "In Progress" → "Complete").
- Major features ship or get released.
- Significant bugs get resolved or security patches go out.
- The project timeline or scope shifts.
- An external dependency or a breaking change lands.

### Update Protocol
1. **Before Updates**: read the current roadmap and changelog status first.
2. **During Updates**: hold version consistency and proper formatting.
3. **After Updates**: confirm links, dates, and cross-references are right.
4. **Quality Check**: make sure the updates match the real implementation progress.

### Plans

### Plan Location
Keep plans under `./plans`, each in a folder named with a timestamp and a descriptive label.

**Format:** follow the naming pattern from the `## Naming` section the hooks inject.

**Example:** `plans/251101-1505-authentication-and-profile-implementation/`

#### File Organization

```
plans/
├── 20251101-1505-authentication-and-profile-implementation/
    ├── research/
    │   ├── researcher-XX-report.md
    │   └── ...
│   ├── reports/
│   │   ├── scout-report.md
│   │   ├── researcher-report.md
│   │   └── ...
│   ├── plan.md                                # Overview access point
│   ├── phase-01-setup-environment.md          # Setup environment
│   ├── phase-02-implement-database.md         # Database models
│   ├── phase-03-implement-api-endpoints.md    # API endpoints
│   ├── phase-04-implement-ui-components.md    # UI components
│   ├── phase-05-implement-authentication.md   # Auth & authorization
│   ├── phase-06-implement-profile.md          # Profile page
│   └── phase-07-write-tests.md                # Tests
└── ...
```

#### File Structure

##### Overview Plan (plan.md)
- Keep it generic and under 80 lines.
- List every phase with its status/progress.
- Link out to the detailed phase files.
- Note the key dependencies.

##### Phase Files (phase-XX-name.md)
Stay fully within the `development-rules.md` file.
Each phase file should carry:

**Context Links**
- Links to related reports, files, documentation

**Overview**
- Priority
- Current status
- Brief description

**Key Insights**
- Important findings from research
- Critical considerations

**Requirements**
- Functional requirements
- Non-functional requirements

**Architecture**
- System design
- Component interactions
- Data flow

**Related Code Files**
- List of files to modify
- List of files to create
- List of files to delete

**Implementation Steps**
- Detailed, numbered steps
- Specific instructions

**Todo List**
- Checkbox list for tracking

**Success Criteria**
- Definition of done
- Validation methods

**Risk Assessment**
- Potential issues
- Mitigation strategies

**Security Considerations**
- Auth/authorization
- Data protection

**Next Steps**
- Dependencies
- Follow-up tasks
