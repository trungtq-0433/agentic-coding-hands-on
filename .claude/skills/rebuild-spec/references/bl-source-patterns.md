# Background Logic Source Patterns

Reference for Wave 0 scout BL inventory emission. Scout reads this file to select per-stack detection patterns.

## Detection Modes

**Mode A — Folder Convention (path-based glob)**
Stack uses fixed directory conventions (Laravel, Rails, Django). Each file matching a glob = one inventory entry.

**Mode B — Annotation/Decorator (content-based scan)**
Stack places logic via decorators/annotations; files can live anywhere (NestJS, Spring, FastAPI, .NET, Go, Rust).
Each decorator/annotation hit (one method/class) = one inventory entry.
Multiple hits in same file → multiple entries (e.g. a NestJS service with three `@OnEvent()` handlers = 3 entries).

Stack may appear as both A and B (Django uses folder + `@shared_task` decorator).

---

## Per-Stack Source Patterns

| Stack | Mode | scheduled-job | queue-worker | event-listener | observer | mail | notification | middleware | custom-command | integration | webhook |
|-------|------|---------------|--------------|----------------|----------|------|--------------|------------|----------------|-------------|---------|
| Laravel (PHP) | A | `app/Console/Commands/**` (registered in `Console/Kernel.php::schedule()`) | `app/Jobs/**` | `app/Listeners/**`, `app/Events/**` | `app/Observers/**` | `app/Mail/**` | `app/Notifications/**` | `app/Http/Middleware/**` excl. Auth* | `app/Console/Commands/**` (non-scheduled) | `app/Services/{ExternalName}/**` | `app/Http/Controllers/**` with webhook in name/route |
| Rails (Ruby) | A | `app/jobs/scheduled/**` + `config/schedule.rb` entries | `app/jobs/**` (ApplicationJob subclasses) | `app/listeners/**`, `ActiveSupport::Notifications` subscribers | `app/observers/**` | `app/mailers/**` | `app/notifications/**` (noticed gem) | `app/middleware/**` excl. Auth | `lib/tasks/**/*.rake` | external gem client modules | controllers with webhook route |
| Django (Python) | A+B | `@shared_task` with Celery beat schedule | `@shared_task` (non-periodic) | `signals.py` `@receiver` decorators | `pre_save`/`post_save` signal handlers | `**/email.py`, `core.mail` senders | `**/notifications/**` (django-notifications) | `MIDDLEWARE` setting classes excl. Auth* | management `commands/**` | external service modules | views with webhook in name/URL |
| NestJS (TS) | B | `@Cron()`, `@Interval()`, `@Timeout()` | `@Process()` (Bull/BullMQ) | `@OnEvent()` handlers | lifecycle hooks (`OnModuleInit`, `OnApplicationBootstrap`) | files matching `*mail*.service.ts` with email send calls | `*notification*.service.ts` | `@Injectable() implements NestMiddleware` excl. Auth | `@Command()` (nestjs-command) | external SDK injection clients (`@InjectModel` etc.) | controllers with webhook route or guard |
| Spring (Java/Kotlin) | B | `@Scheduled` methods | `@RabbitListener`, `@KafkaListener`, `@JmsListener` | `@EventListener`, `@TransactionalEventListener` | `@EntityListeners` classes | `JavaMailSender`/`MailService` callers | (spring-boot-mail notification patterns) | `Filter` / `HandlerInterceptor` excl. Auth | `@ShellComponent` / `CommandLineRunner` / `ApplicationRunner` | `@FeignClient` interfaces | controllers/handlers with webhook path |
| FastAPI (Python) | B | APScheduler `@scheduler.scheduled_job` | Celery `@shared_task` (if Celery present) | `@app.on_event` / custom event handlers | n/a | smtp/email sender functions | n/a | `BaseHTTPMiddleware` subclasses excl. Auth | CLI scripts in `scripts/**` or `commands/**` | external SDK clients | routers with webhook path |
| Go (Gin/Echo + asynq/cron) | B | cron lib `cron.New().AddFunc` / `gocron` registrations | asynq `Handler.HandleFunc` registrations | event bus `Subscribe` / handler registrations | n/a | mailer function definitions | n/a | middleware `func` registered to engine excl. Auth | `cobra` command definitions | external SDK client structs | handlers with webhook in route path |
| Rust (Actix/Axum + tokio-cron) | B | scheduler `.add(Job::new(...))` | message queue handler closures | event listener `register` calls | n/a | mailer function definitions | n/a | tower middleware layers excl. Auth | CLI binary `main`/`command` handlers | external HTTP client structs | handlers with webhook in route path |
| .NET (ASP.NET Core) | B | `IHostedService` / `BackgroundService` subclasses | MassTransit `IConsumer<T>` implementations | MediatR `INotificationHandler<T>` | EF Core `SaveChangesInterceptor` / `DbCommandInterceptor` | `IEmailSender` implementations | n/a | `IMiddleware` / `Use*` middleware excl. Auth | `IHostedService` CLI pattern / `CommandLineApplication` | external HTTP client classes | controllers with webhook route |
| systemd (any stack) | A | `*.timer` unit files paired with a `*.service` unit's `ExecStart=` (in-repo `deploy/systemd/**` or `/etc/systemd/system/**` — may live outside the app's own language surface, needs a separate glob) | n/a | n/a | n/a | n/a | n/a | n/a | `*.service` unit (no paired `.timer`) invoking a one-off binary via `ExecStart=` | n/a | n/a |

**Table is non-exhaustive.** Stack or library not in this table → use `[SIGNAL_INFERRED]` protocol below.

---

## Signal Inference Fallback `[SIGNAL_INFERRED]`

Mirrors the protocol in `references/composite-screen-detection.md § Signal Inference Fallback`.

**When to apply:**
- Stack has no row in the table above, OR
- Stack has a row but the project uses a custom library that does not match the row's patterns.

**Protocol:**
1. Add `[SIGNAL_INFERRED]` at the end of the inventory entry line.
2. Include a 3-part justification block in the scout report (all three parts MANDATORY):
   - **Intent matched:** which of the 10 canonical types the pattern fits (e.g., "queue-worker — async job consumer pattern")
   - **No-row reason:** why no per-stack row applies (e.g., "stack=Phoenix Elixir, no row in table" or "stack=Laravel but project uses custom QueueGenie not standard Job class")
   - **Observed pattern:** what was actually seen (e.g., "file defines `defmodule MyWorker do use Oban.Worker` with `@impl true def perform(args)`")
3. The entry follows the matched canonical type.

**Limits:**
- Do NOT use `[SIGNAL_INFERRED]` to bypass a row that already matches.
- Do NOT upgrade a non-BL file to BL just because it "looks background-y" — must match Intent of one of the 10 canonical types.
- **Ratio cap:** enforced by reviewer. See `references/verification-checklist-core-artifacts.md` § BehaviorLogic Cardinality Cross-Check Rule 5 for canonical thresholds, strict-inequality bounds, division-by-zero guard, and `### Unknown` exemption.
- Tag is advisory; remove when a future skill update adds a covering row.

---

## Canonical BL Types (10 types)

All per-stack patterns above map to exactly these 10 types. Researcher and reviewer use this list as the single source of truth.

| Type | Description |
|------|-------------|
| `scheduled-job` | Cron-like scheduled tasks |
| `queue-worker` | Background job workers (async queue consumers) |
| `event-listener` | Event-driven handlers |
| `observer` | Model lifecycle hooks (created/updated/deleted) |
| `mail` | Email sending logic |
| `notification` | In-app / push notification logic |
| `middleware` | Request/response processing chain (non-auth) |
| `custom-command` | CLI commands |
| `integration` | Third-party integrations (external API clients) |
| `webhook` | Incoming/outgoing webhook handlers |

Auth/permission middleware is excluded — see `permissions-template.md`.

---

## File-Exchange Schema Signal

For BL entries matching import/export vocabulary (`import, export, csv, xlsx, upload, download, bulk`), locate the column/header contract via `validateHeader()` calls, schema-array constants (e.g. `EXPECTED_COLUMNS`, `HEADER_MAP`), or column-mapping objects near the parse/generate call site. Capture this into the BL block's `**File Schema**` field (see `templates/behavior-logic-template.md`) — this file covers detection only, not field grammar.

---

## Multi-Stack Handling

When `[MULTI_STACK]` is flagged in the scout File Inventory:

1. Emit one subsection per detected stack (e.g., `### Laravel`, `### NestJS`).
2. Apply the pattern table row for each stack independently.
3. **Reviewer computes gap per stack then takes MAX** (do NOT OR-merge) — prevents a large stack masking a coverage gap in a smaller stack.
   - Example: Laravel 150/150 (gap 0%) + NestJS 0/20 (gap 100%) → reported gap = max(0%, 100%) = 100% critical, not average 50%.

---

## Mode B Grep Markers — Quick Reference

For Mode B stacks, scout applies grep to detect annotation/decorator hits. The regex below is a seed — append alternates for stack-specific libraries (e.g., Phoenix Oban, Elixir GenServer) and rerun.

```bash
grep -rEn \
  "@(Cron|Interval|Timeout|Process|OnEvent|Scheduled|EventListener|TransactionalEventListener|RabbitListener|KafkaListener|JmsListener|EntityListeners|FeignClient|ShellComponent|Command|InjectModel|app\.(task|on_event)|shared_task|scheduler\.scheduled_job|receiver)|IHostedService|BackgroundService|IConsumer<|INotificationHandler<|SaveChangesInterceptor|DbCommandInterceptor|IEmailSender|IMiddleware|cron\.New\(\)|asynq\.|gocron\.|tower::Layer|Job::new" \
  --include="*.ts" --include="*.java" --include="*.kt" --include="*.py" \
  --include="*.go" --include="*.rs" --include="*.cs" \
  --include="*.rb" --include="*.php" \
  src/ app/ lib/ internal/ 2>/dev/null
```

Each matching line with a qualifying decorator/annotation hit = one inventory entry. Record file path + symbol (class or method name) from context.
