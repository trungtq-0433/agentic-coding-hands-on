# API Contract Researcher Contract (Wave 6.87 — rebuild-spec v5)

## Session Context

Read `plans/<active-plan>/artifacts/_session-context.md` FIRST before any other read.
Do NOT re-derive information already present there.

## Synthesis Sources (read ALL before writing any entry)

Read these upstream artifacts from `plans/<active>/artifacts/`:
- `data-model.md` — entity definitions (MODEL### for Backed-by cross-refs)
- `permissions.md` — PERM### codes (auth cross-refs)
- `route-list.md` — REST endpoint identity (METHOD /path)
- `api-map.md` — endpoint-to-handler mapping
- `scout-report.md § Detected API Kind` — kind signal (rest/graphql/grpc/mixed)

## Source Code Authorization

**AUTHORIZED to read source code directly** via Grep/Read tools:
- FormRequest classes (validation rules — REST)
- Transformer/Resource classes (response surface — REST)
- GraphQL SDL files (`*.graphql`, `schema.graphql`) — types, queries, mutations, directives
- GraphQL resolver files — handler implementations
- `.proto` files — service/rpc/message definitions (gRPC)
- gRPC controller/handler files — implementation details
- Policy/Gate classes — auth mapping to PERM###

This is a source-READ contract, not a pure-synthesis contract. Use upstream artifacts for discovery; verify and extract from code.

## Output

Single file: `plans/<active>/artifacts/api-contracts.md`.
Template: `templates/api-contracts-template.md`.

If no synchronous API surface is detected (library, CLI, no endpoints), emit the header + `_(no synchronous API surface detected)_` + write completion marker with content `no_api_contracts`.

### Confidence Companion (advisory sidecar)

`confidence-report_api-contracts.md` is NOT part of the researcher's output above. It is emitted
automatically by `scripts/derive_confidence_report.py` (a deterministic script, not authored by
the researcher) after `api-contracts.md` is promoted (Wave AC.5) — a citation-coverage sidecar,
never gated, never asserted. See `references/confidence-report-contract.md` for the full
derivation rules and the A1 correctness-verification boundary.

## Gate (STRICT — scope boundary)

**Synchronous request/response ONLY.** Include:
- REST endpoints (GET/POST/PUT/PATCH/DELETE)
- GraphQL queries and mutations
- Inbound unary gRPC RPCs

**EXCLUDE** (these belong in behavior-logic BL###/INT-###):
- FCM push notifications
- WebSocket connections
- GraphQL subscriptions
- Server-Sent Events
- Outbound gRPC calls (client calls to external services)
- Message queue producers/consumers
- Event bus publishers

An excluded surface encountered during extraction → note in `## Open Questions`, never in the entries.

## Entry Grammar

Per-entry backbone (all 8 fields mandatory for every entry):

| Field | Description |
|-------|-------------|
| **Key** | Identity: `METHOD /path` (REST), operation name (GraphQL), `Service.Method` (gRPC) |
| **Request surface** | Body/query params + validation rules (REST); input type + directives (GraphQL); proto request message (gRPC) |
| **Response surface** | Transformer/resource keys — list exposed surface, NOT entity columns (REST); SDL return type fields (GraphQL); proto response message (gRPC) |
| **Backed by** | `MODEL###` reference to entities.md (optional if no direct entity mapping) |
| **Auth** | Middleware/policy -> `PERM###` (REST); `@guard`/`@can` -> `PERM###` (GraphQL); per-call mechanism or "trusted-internal" (gRPC). Missing auth is a security signal — write `none` explicitly, never leave blank |
| **Error model** | HTTP status codes referencing Global Error Contract (REST); `errors[].extensions` shape (GraphQL); gRPC status or in-band error shape (gRPC) |
| **Confidence** | `EXTRACTED` (schema-first: FormRequest/Transformer/SDL/.proto present), `INFERRED` (code-first, loose validation), `INFERRED-from-stub` (imported proto/SDL whose source file is absent in repo) |
| **Source** | `file:line` citation(s) for the primary definition |

## Collision Rule

- If `api-contracts.md` does not exist -> create it.
- If `api-contracts.md` exists with `status: ai-draft` or no status -> overwrite (re-draft).
- If `api-contracts.md` exists with `status: human-curated` -> MUST NOT overwrite; emit `[INFO] api_contracts_preserved`.

## Citation Rule (anti-hallucination)

**Every entry MUST carry a `Source:` field with `file:line` or `file:start-end`.**

- If an endpoint/operation cannot be source-cited -> move it to `## Open Questions` with the evidence gap noted.
- An entry without `Source: file:line` = **CRITICAL** contract violation.
- Confidence rule: schema-first (FormRequest/SDL/.proto present) = `EXTRACTED`; code-first with loose validation = `INFERRED`; imported definition whose source file is absent = `INFERRED-from-stub` (this does NOT fail — missing import source is expected in some architectures).

## DRY Rule

- Shared types (request/response DTOs, proto messages reused across entries) MUST be defined ONCE in `## Conventions > Shared Messages / Types`.
- Entries reference shared types by name, never re-list their fields.
- Entity fields live in `data-model.md` (MODEL###). Entries say "Backed by MODEL###" and list only the **response surface** (transformer/resolver output), which may differ from entity columns (computed fields, renamed keys, nested includes).
- Re-defining a shared type's fields inside an entry = DRY violation (validator warning).

## Kind-Specific Concerns

### REST
- Auth field must record middleware chain. Routes without auth middleware -> `none` (security signal, not omission).
- Response surface = transformer/resource output keys, NOT entity columns. Computed/derived fields marked with annotation.
- Global Error Contract covers standard status codes; entry-level overrides only for deviations.

### GraphQL
- Key = operation name (query/mutation), NOT `POST /graphql`.
- Auth = `@guard` + `@can(ability)` directives -> map to PERM### 1:1.
- Validation = `@rules(apply:[...])` or `@validator` directives (schema-first = EXTRACTED).
- Error model = `errors[].extensions.statusCode` (HTTP 200 always; errors in body).

### gRPC
- Key = `Service.Method`.
- Auth = frequently "trusted-internal" (no per-call auth; scoping via payload field like `company_id`). **State this explicitly** — it is a security signal revealing that authorization depends on network/deploy boundary, not per-call tokens.
- Error model has two patterns: (a) gRPC status codes (exception propagation); (b) in-band error fields (`result: bool`, `validate_errors[]`). Document which pattern each RPC uses.
- Streaming type (unary/server-stream/client-stream/bidi) noted per entry.
- Shared proto messages defined once in Conventions.

## Completion Marker

After all entries are written (including the empty-surface case), write:

```
plans/<active>/artifacts/.api-contracts.completed
```

- Non-zero entries: zero-byte file.
- Zero entries (no API surface): file content = `no_api_contracts`.

The marker distinguishes "W6.87 not run yet" from "W6.87 ran and found nothing."
MUST NOT write the marker before `api-contracts.md` is fully written.

## Fragment Mode (shard branch)

When dispatched as a **fragment researcher** (shard mode), the following overrides apply:

**Scope:** You are assigned a specific resource namespace slice. Write entries ONLY for the endpoints listed in your slice assignment.

**Output:** Write to `plans/<active>/artifacts/_fragments/api-contracts/NN-<namespace>.md` (ordinal-prefixed fragment file, NOT the draft itself).

**Rules (fragment contract — `references/artifact-sharding.md`):**
1. Write `### entry` blocks ONLY — no `##` section headers, no `## Conventions`, no preamble.
2. Reference shared types by name (defined once in `## Conventions` by the shell researcher). **Never re-list shared type fields** — this causes `shared_type_redefined` validator warnings (DRY violation).
3. Every entry MUST carry a `Source: file:line` citation (same as normal mode).
4. Stay within your assigned namespace. If an endpoint belongs to a different namespace, skip it.
5. The `kind:` tag and `## Kind` header are owned by the shell researcher. Do NOT emit them.

**Entry grammar:** Identical to normal mode (all 8 fields mandatory per entry). The only difference is the output target (fragment file vs. draft).

## See Also

- `references/artifact-sharding.md` — descriptor table, merge recipe, fragment contract
- `references/api-contract-source-patterns.md` — per-stack detection patterns for API kind
- `references/code-formats.md` — shared code format schema
- `templates/api-contracts-template.md` — output template
- `references/verification-checklist-core-artifacts.md § ApiContracts` — reviewer checklist
