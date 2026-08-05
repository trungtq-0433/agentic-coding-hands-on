<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
<!-- Output path: docs/generated/entities.md -->

# Entities

**Project**: {PROJECT_NAME}
**Generated**: {DATE}

## Entity Relationship Diagram

```mermaid
erDiagram
    {ENTITY_1} {
        {ATTR_TYPE_1} {ATTR_NAME_1} PK
        {ATTR_TYPE_2} {ATTR_NAME_2}
        {ATTR_TYPE_3} {ATTR_NAME_3} FK
    }
    {ENTITY_2} {
        {ATTR_TYPE_1} {ATTR_NAME_1} PK
        {ATTR_TYPE_2} {ATTR_NAME_2}
    }
    {ENTITY_3} {
        {ATTR_TYPE_1} {ATTR_NAME_1} PK
        {ATTR_TYPE_2} {ATTR_NAME_2} FK
        {ATTR_TYPE_3} {ATTR_NAME_3}
    }
    {ENTITY_1} ||--o{ {ENTITY_3} : "has"
    {ENTITY_2} ||--o{ {ENTITY_3} : "manages"
```

## Entities

{POPULATED_BY_FRAGMENTS}

### {ENTITY_1}

**Description**: {DESCRIPTION}

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| {ATTR_NAME_1} | {TYPE} | PK, NOT NULL | {DESC} |
| {ATTR_NAME_2} | {TYPE} | NOT NULL | {DESC} |
| {ATTR_NAME_3} | {TYPE} | FK | {DESC} |

**Relationships**:
- One-to-Many with {ENTITY_3} via {ATTR_NAME_3}

**Discriminator Fields**:

> **Scope:** enum fields with ≥2 distinct behavioral values. Boolean flags (`is_active`, `is_published`) are NOT discriminators — document their behavioral impact in feature spec Business Rules.

{DISC-### applies to enum fields with ≥2 named values that have distinct behavioral outcomes. Examples:}

| Field | DISC-### | Values | Description |
|-------|----------|--------|-------------|
| {field_name} | DISC-### | val1, val2, ... | {what each value means at the domain level — NOT behavioral implications} |

{Fallback when entity has no discriminator fields: `**Discriminator Fields**: None.`}

---

### {ENTITY_2}

**Description**: {DESCRIPTION}

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| {ATTR_NAME_1} | {TYPE} | PK, NOT NULL | {DESC} |
| {ATTR_NAME_2} | {TYPE} | NOT NULL | {DESC} |

**Relationships**:
- One-to-Many with {ENTITY_3} via {ATTR_NAME_2}

**Discriminator Fields**:

| Field | DISC-### | Values | Description |
|-------|----------|--------|-------------|
| {field_name} | DISC-### | val1, val2, ... | {what each value means at the domain level — NOT behavioral implications} |

{Fallback when entity has no discriminator fields: `**Discriminator Fields**: None.`}

---

### {ENTITY_3}

**Description**: {DESCRIPTION}

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| {ATTR_NAME_1} | {TYPE} | PK, NOT NULL | {DESC} |
| {ATTR_NAME_2} | {TYPE} | FK, NOT NULL | {DESC} |
| {ATTR_NAME_3} | {TYPE} | | {DESC} |

**Relationships**:
- Many-to-One with {ENTITY_1} via {ATTR_NAME_2}
- Many-to-One with {ENTITY_2} via {ATTR_NAME_3}

**Discriminator Fields**:

| Field | DISC-### | Values | Description |
|-------|----------|--------|-------------|
| {field_name} | DISC-### | val1, val2, ... | {what each value means at the domain level — NOT behavioral implications} |

{Fallback when entity has no discriminator fields: `**Discriminator Fields**: None.`}

---

## Validation Rules

### {ENTITY_1}

| Rule | Field | Constraint | Error Message |
|------|-------|------------|---------------|
| {RULE_NAME_1} | {ATTR_NAME} | {CONSTRAINT} | {ERROR_MESSAGE} |
| {RULE_NAME_2} | {ATTR_NAME} | {CONSTRAINT} | {ERROR_MESSAGE} |

### {ENTITY_2}

| Rule | Field | Constraint | Error Message |
|------|-------|------------|---------------|
| {RULE_NAME_1} | {ATTR_NAME} | {CONSTRAINT} | {ERROR_MESSAGE} |

### {ENTITY_3}

| Rule | Field | Constraint | Error Message |
|------|-------|------------|---------------|
| {RULE_NAME_1} | {ATTR_NAME} | {CONSTRAINT} | {ERROR_MESSAGE} |

---

## Summary

- **Total Entities**: {TOTAL_ENTITIES}
- **Total Relationships**: {TOTAL_RELATIONSHIPS}
