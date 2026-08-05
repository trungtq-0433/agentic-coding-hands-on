# [Feature Name] Implementation Plan

**Date**: YYYY-MM-DD  
**Type**: Feature Implementation  
**Status**: Planning  
**Context Tokens**: <200 words

## Executive Summary
Brief 2-3 sentence description of the feature and its business value.

## Context Links
- **Related Plans**: [List other plan files - no full content]
- **Dependencies**: [External systems, APIs, existing features]
- **Reference Docs**: [Link to docs in .sun/ directory]

## Requirements
### Functional Requirements
- [ ] Requirement 1
- [ ] Requirement 2

### Non-Functional Requirements  
- [ ] Performance target
- [ ] Security requirement
- [ ] Scalability requirement

## Architecture Overview
```mermaid
[Simple component diagram]
```

### Key Components
- **Component 1**: Brief description
- **Component 2**: Brief description

### Data Models
- **Model 1**: Key fields
- **Model 2**: Key fields

## Implementation Phases

### Phase 1: [Name] (Est: X days)
**Scope**: Specific boundaries
**Tasks**:
1. [ ] Task 1 - file: `path/to/file.ts`
2. [ ] Task 2 - file: `path/to/file.ts`

**Acceptance Criteria** (each item may carry a `→ verify: <command>` so "done" is checkable, not subjective):
- [ ] Criteria 1 → verify: `<command>` (expected: <outcome>)
- [ ] Criteria 2

> The `→ verify:` suffix is optional and additive — older plans without it still parse. When present, it is the exact command whose output proves the criterion; the evidence gate records the run in `temper-results.json`.

### Phase 2: [Name] (Est: X days)
[Repeat structure]

## Testing Strategy
- **Unit Tests**: Specific test coverage targets
- **Integration Tests**: Key interaction points
- **E2E Tests**: Critical user flows

## Security Considerations
- [ ] Security item 1
- [ ] Security item 2

## Risk Assessment
| Risk | Impact | Mitigation |
|------|--------|------------|
| Risk 1 | High | Mitigation strategy |

## Quick Reference
### Key Commands
```bash
npm run command
```

### Configuration Files
- `config/file.ts`: Purpose
- `.env.example`: Environment variables

## TODO Checklist
- [ ] Phase 1 Task 1
- [ ] Phase 1 Task 2
- [ ] Phase 2 Task 1
- [ ] Testing complete
- [ ] Documentation updated
- [ ] Code review passed
