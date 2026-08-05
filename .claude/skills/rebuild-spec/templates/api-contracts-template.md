# API Contracts

**Project**: {PROJECT_NAME}
**Generated**: {DATE}
**Confidence legend**: `EXTRACTED` = schema/validation source present | `INFERRED` = deduced from usage | `INFERRED-from-stub` = imported proto/SDL whose source is absent

---

## Conventions

### Shared Messages / Types

{Define shared request/response types, DTOs, and proto messages used across multiple entries. Each type defined ONCE here; entries reference by name. DRY: never re-list MODEL### fields — say "Backed by MODEL###" and list only the exposed surface.}

| Type name | Definition source | Backed by | Notes |
|-----------|------------------|-----------|-------|
| {SharedTypeName} | `{file:line}` | MODEL### | {field list or "see definition source"} |

### Global Error Contract

{Define error envelope shapes per kind. Entries reference this section; only override when deviating from the standard.}

| Code / Status | When | Envelope |
|---------------|------|----------|
| {422 / gRPC INVALID_ARGUMENT / errors[]} | {condition} | {shape} |

### Pagination

{Document pagination envelope shape if consistent across entries. Reference by name in entries.}

---

## REST Endpoints

kind: rest

{One entry per synchronous REST endpoint. Key = METHOD /path.}

{POPULATED_BY_FRAGMENTS}

### {ROUTE_CODE} --- {METHOD} {/path} --- [{CONFIDENCE}]

{One-line purpose}. **Backed by:** {MODEL###}

- **Handler:** `{Controller@method}` --- `{file:line}`
- **Auth:** {middleware/policy -> PERM### | none (state explicitly)}
- **Request --- Body:**

  | Field | Type | Required | Constraint |
  |-------|------|----------|------------|
  | {field} | {type} | {yes/no} | {validation rule} |

- **Request --- Path/Query:** {params or "none"}
- **Response {status}** ({TransformerClass}, surface != entity columns):
  `{key1, key2, computed_field, ...}`
- **Errors:** {status codes referencing Global Error Contract; override if different}
- **Source:** `{file:line}` --- `{file:line}`

---

## GraphQL Operations

kind: graphql

{One entry per query/mutation. Key = operation name. Subscriptions excluded (async -> behavior-logic).}

{POPULATED_BY_FRAGMENTS}

### {GQL_CODE} --- {query|mutation} `{operationName}` --- [{CONFIDENCE}]

{One-line purpose}. **Returns:** `{ReturnType}` -> Backed by {MODEL###}

- **Auth:** {`@guard` + `@can(ability)` -> PERM### | none}
- **Arguments / Input --- {InputType}:**

  | Field | Type | Rules |
  |-------|------|-------|
  | {field} | {type} | {validation directive or rule} |

- **Returns --- {Type}:** `{exposed fields}`
- **Errors:** {`errors[]` + `extensions.statusCode` shape}
- **Source:** `{schema.graphql:line}` --- `{resolver file:line}`

---

## gRPC Methods

kind: grpc

{One entry per inbound unary RPC. Key = Service.Method. Outbound gRPC -> INT-### in behavior-logic. Streaming type noted per entry.}

{POPULATED_BY_FRAGMENTS}

### {GRPC_CODE} --- `{Service.Method}` --- [{CONFIDENCE}] --- {unary|server-stream|client-stream|bidi}

{One-line purpose}. **Returns:** `{ResponseMessage}`

- **Auth:** {per-call auth mechanism | trusted-internal (state explicitly --- this is a security signal, not an omission)}
- **Request --- {RequestMessage}** (`{proto file:line}`):

  | Field | Proto type | # |
  |-------|-----------|---|
  | {field} | {type} | {field number} |

- **Response --- {ResponseMessage}:** `{field list or reference to shared message}`
- **Errors:** {gRPC status (propagated) | in-band (`result` + `validate_errors`) | both}
- **Source:** `{proto file:line}` --- `{impl file:line}`
