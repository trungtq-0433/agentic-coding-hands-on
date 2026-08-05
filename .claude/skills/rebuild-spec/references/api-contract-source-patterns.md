# API Contract Source Patterns

Reference for Wave 0 scout API-kind detection and Wave 6.87 researcher per-stack extraction. Scout reads this file to detect API kind; researcher reads it for extraction guidance.

## Detection Modes

**Mode A — Folder / File Convention (path-based glob)**
Stack uses fixed directory conventions or well-known filenames for API definitions. Presence of matching files = kind signal.

**Mode B — Annotation / Content Scan (content-based grep)**
Stack places API surface via decorators, annotations, or DSL. Files can live anywhere; grep for markers.

Stack may use both modes (e.g., Laravel REST via routes + GraphQL via Lighthouse SDL).

---

## Per-Stack Source Patterns

| Stack | Mode | REST signals | GraphQL signals | gRPC signals |
|-------|------|-------------|-----------------|--------------|
| Laravel (PHP) | A+B | `routes/web.php`, `routes/api.php`; `app/Http/Controllers/**`; FormRequest (`app/Http/Requests/**`); Transformer/Resource (`app/Http/Resources/**`, `app/Transformers/**`) | Lighthouse: `*.graphql` SDL files, `graphql/schema.graphql`, `lighthouse.php` config; `@guard`/`@can`/`@rules` directives in SDL | `.proto` files; `grpc` in `composer.json` deps; `*GrpcController.php` |
| Rails (Ruby) | A | `config/routes.rb`; `app/controllers/**`; `app/serializers/**` (ActiveModel) | `app/graphql/**`; `graphql-ruby` gem in Gemfile | `.proto` files; `grpc` gem in Gemfile |
| Django (Python) | A+B | `urls.py`; `views.py`/`viewsets.py`; `serializers.py` (DRF) | `graphene` / `strawberry` / `ariadne` in `pyproject.toml`; `schema.py` with `@strawberry.type` | `.proto` files; `grpcio` in `pyproject.toml` |
| NestJS (TS) | B | `@Controller()`, `@Get()/@Post()/@Put()/@Delete()`; DTO classes with `class-validator` decorators | `@Resolver()`, `@Query()`, `@Mutation()`; `*.graphql` SDL files; `@nestjs/graphql` in `package.json` | `@GrpcMethod()`, `@GrpcService()`; `.proto` files; `@nestjs/microservices` + `grpc` in `package.json` |
| Express/Fastify (TS/JS) | B | `app.get/post/put/delete()`; `router.*()` | `apollo-server` / `mercurius` / `yoga` in `package.json`; `typeDefs`/`resolvers` patterns | `.proto` files; `@grpc/grpc-js` in `package.json` |
| Spring (Java/Kotlin) | B | `@RestController`, `@RequestMapping`, `@GetMapping/@PostMapping`; DTO with `@Valid`/`@NotNull` | `@QueryMapping`, `@MutationMapping`; `spring-graphql` in `build.gradle`/`pom.xml`; `*.graphqls` SDL files | `.proto` files; `grpc-spring-boot-starter` in `build.gradle`/`pom.xml` |
| FastAPI (Python) | B | `@app.get/post/put/delete()`; Pydantic model params | `strawberry` / `ariadne` in `pyproject.toml` | `.proto` files; `grpcio` in `pyproject.toml` |
| Go (Gin/Echo/Chi) | B | `r.GET/POST/PUT/DELETE()`, `e.GET/POST()`, handler func registrations | `github.com/99designs/gqlgen` in `go.mod`; `*.graphqls` SDL files | `.proto` files; `google.golang.org/grpc` in `go.mod` |
| Rust (Actix/Axum) | B | `.route()`, `web::get/post()`, handler fn registrations | `async-graphql` / `juniper` in `Cargo.toml` | `.proto` files; `tonic` in `Cargo.toml` |
| .NET (ASP.NET Core) | B | `[ApiController]`, `[HttpGet/Post/Put/Delete]`; DTO with `[Required]`/`[Range]` | `HotChocolate` / `GraphQL.NET` in `.csproj` | `.proto` files; `Grpc.AspNetCore` in `.csproj` |

**Table is non-exhaustive.** Stack or library not in this table -> use `[SIGNAL_INFERRED]` protocol below.

---

## Async / Messaging Signal Class (v12.0.0 — 4th canonical kind)

The canonical API kinds are now **four**: `rest`, `graphql`, `grpc`, **`async`**. The async class
captures message-driven integration (producer/consumer + topic + event schema) — the backbone of
microservice topology that REST/GraphQL/gRPC miss. Consumed by Phase D `extract_service_topology.py`
adapters (`_topology_adapter_{spring,nestjs,go}.py`) to emit `topic[{name, role, event}]` into the
neutral digest. A stack/broker not listed → `[SIGNAL_INFERRED]` (same protocol below).

| Stack / broker | Async signals (producer/consumer + topic) |
|----------------|--------------------------------------------|
| Spring (Kafka) | `@KafkaListener(topics=...)` (consumer), `KafkaTemplate.send(topic,...)` (producer); `spring-kafka` dep; `*.avsc`/`*.proto` event schema |
| NestJS | `@EventPattern(...)`/`@MessagePattern(...)` (consumer), `ClientProxy.emit/send` (producer); `@nestjs/microservices` |
| Go | `segmentio/kafka-go` (`kafka.NewReader`→consumer, `kafka.NewWriter`→producer), `Shopify/sarama` / `IBM/sarama` |
| RabbitMQ (any) | `amqp` channel `Consume`/`basicConsume` (consumer), `Publish`/`basicPublish` (producer); exchange/queue names = topic |
| NATS (any) | `Subscribe`/`QueueSubscribe` (consumer), `Publish` (producer); subject = topic |
| AsyncAPI (any) | `asyncapi.yaml`/`asyncapi.json` — `channels.*.publish`/`subscribe` declare topic + message |

Outbound gRPC stays its own class → recorded as `INT-###` in behavior-logic per the existing pattern;
gRPC inbound per-repo is the `grpc` column above.

---

## Signal Inference Fallback `[SIGNAL_INFERRED]`

Mirrors the protocol in `references/bl-source-patterns.md § Signal Inference Fallback`.

**When to apply:**
- Stack has no row in the table above, OR
- Stack has a row but the project uses a custom library that does not match the row's patterns.

**Protocol:**
1. Add `[SIGNAL_INFERRED]` at the end of the detection note.
2. Include a 3-part justification block in the scout report (all three parts MANDATORY):
   - **Intent matched:** which kind the pattern signals (e.g., "graphql — SDL schema files with query/mutation definitions")
   - **No-row reason:** why no per-stack row applies (e.g., "stack=Phoenix Elixir, no row in table" or "stack=Go but project uses custom gRPC framework not in table")
   - **Observed pattern:** what was actually seen (e.g., "file `schema.ex` defines `query do ... end` blocks with Absinthe DSL")
3. The detection follows the matched kind.

**Limits:**
- Do NOT use `[SIGNAL_INFERRED]` to bypass a row that already matches.
- Do NOT upgrade a non-API file to an API kind signal just because it "looks API-ish."

---

## Canonical API Kinds (3 kinds)

All per-stack patterns above map to exactly these kinds. Scout and researcher use this list as the single source of truth.

| Kind | Key shape | Scope |
|------|-----------|-------|
| `rest` | `METHOD /path` | Synchronous HTTP endpoints |
| `graphql` | operation name | Queries and mutations (subscriptions excluded -> behavior-logic) |
| `grpc` | `Service.Method` | Inbound unary RPCs (outbound -> INT-### in behavior-logic) |

---

## Multi-Stack Handling (MAX Rule)

When `[MULTI_STACK]` is flagged in the scout File Inventory:

1. Detect kind per stack independently using the appropriate row.
2. If multiple kinds detected -> emit `mixed` (e.g., REST + GraphQL, or REST + gRPC).
3. Researcher emits one `kind:` section per detected kind in the output template.
4. **MAX rule for coverage:** reviewer evaluates completeness per kind then takes MAX gap across kinds (do NOT average — prevents a large REST surface masking zero GraphQL coverage).

---

## Mode B Grep Markers — Quick Reference

For Mode B stacks, scout applies grep to detect API-kind signals. The regex below is a seed — append alternates for stack-specific libraries.

```bash
# GraphQL detection
grep -rEln \
  "@(Resolver|Query|Mutation|QueryMapping|MutationMapping|strawberry\.(type|mutation|query))|type\s+(Query|Mutation)\s*\{|schema\s*\{" \
  --include="*.ts" --include="*.js" --include="*.java" --include="*.kt" \
  --include="*.py" --include="*.go" --include="*.rs" --include="*.cs" \
  --include="*.graphql" --include="*.graphqls" --include="*.gql" \
  src/ app/ lib/ internal/ 2>/dev/null

# gRPC detection
grep -rEln \
  "@GrpcMethod|@GrpcService|service\s+\w+\s*\{|rpc\s+\w+\s*\(" \
  --include="*.ts" --include="*.java" --include="*.kt" --include="*.py" \
  --include="*.go" --include="*.rs" --include="*.cs" --include="*.proto" \
  src/ app/ lib/ internal/ proto/ 2>/dev/null
```

File-glob detection (Mode A, all stacks):
```bash
# GraphQL SDL files
find . -type f \( -name "*.graphql" -o -name "*.graphqls" -o -name "*.gql" \) \
  ! -path "*/node_modules/*" ! -path "*/vendor/*" 2>/dev/null

# Proto files
find . -type f -name "*.proto" \
  ! -path "*/node_modules/*" ! -path "*/vendor/*" 2>/dev/null
```

Manifest dependency detection:
```bash
# GraphQL deps in package.json
grep -l '"apollo-server\|graphql-yoga\|mercurius\|@nestjs/graphql\|@apollo/server"' package.json 2>/dev/null

# GraphQL deps in composer.json
grep -l '"nuwave/lighthouse\|rebing/graphql-laravel"' composer.json 2>/dev/null

# gRPC deps
grep -l '"@grpc/grpc-js\|@nestjs/microservices\|grpc-spring-boot-starter\|grpcio\|tonic\|google.golang.org/grpc\|Grpc.AspNetCore"' \
  package.json composer.json pyproject.toml build.gradle pom.xml go.mod Cargo.toml *.csproj 2>/dev/null
```
