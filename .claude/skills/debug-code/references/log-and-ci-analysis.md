# Log & CI/CD Analysis

Pull logs from servers, CI/CD pipelines, and the application itself, then read them to find the failure.

## GitHub Actions Analysis

### List and Inspect Runs

```bash
# List recent runs (all workflows)
gh run list --limit 10

# List runs for specific workflow
gh run list --workflow=ci.yml --limit 5

# View specific run details
gh run view <run-id>

# View failed job logs only
gh run view <run-id> --log-failed

# Download complete logs
gh run view <run-id> --log > /tmp/ci-full.txt

# Re-run failed jobs
gh run rerun <run-id> --failed
```

### Common CI/CD Failure Patterns

| Pattern | Likely Cause | Investigation |
|---------|-------------|---------------|
| Green locally, red in CI | Environment mismatch | Compare Node/Python version, OS, env vars |
| Comes and goes | Race conditions, flaky tests | Run it 3x, watch timing and shared state |
| Times out | Resource caps, infinite loops | Inspect resource use, add timeouts |
| Permission errors | Token/secret misconfigured | Confirm `GITHUB_TOKEN` and secret names |
| Dependency install fails | Registry trouble, version clashes | Check the lockfile and registry status |
| Build green, tests red | Test environment setup | Check test config, database setup, fixtures |

### Analyzing Failed Steps

1. **Find the failing step** - `gh run view <id>` lays out the per-step status
2. **Pull the logs** - `gh run view <id> --log-failed` for the focused output
3. **Hunt the error signature** - Scan for `Error:`, `FAIL`, `exit code`, stack traces
4. **Read the annotations** - `gh api repos/{owner}/{repo}/check-runs/{id}/annotations`

## Server Log Analysis

### Log Collection Strategy

1. **Locate the logs** - Application logs, system logs, web server logs
2. **Window the timeframe** - Trim to the incident's window
3. **Follow the request IDs** - Trace one request across the services it touched
4. **Watch for patterns** - Repeated errors, shifts in error rate, payloads that look off

### Structured Log Queries

```bash
# Search application logs for errors (use Grep tool when possible)
# Pattern: timestamp, level, message
# Filter by time range and severity

# PostgreSQL slow query log
psql -c "SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Check database connections
psql -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"
```

### Cross-Source Correlation

1. **Sync the timestamps** across every log source (mind the timezones)
2. **Lay out the timeline** - First error → how it spread → where users felt it
3. **Name the trigger** - What changed right before that first error?
4. **Map the blast radius** - Which services and endpoints got caught in it?

## Application Log Analysis

### Error Pattern Recognition

- **Sudden spike** → A deployment, a config change, or an external dependency falling over
- **Slow climb** → A resource leak, data growth, or creeping degradation
- **Regular intervals** → Cron jobs, scheduled tasks, resource contention
- **One endpoint** → A code bug, a data issue, or one specific dependency
- **Every endpoint** → Infrastructure, the database, or the network

### Key Log Fields

Lead with: timestamp, level, error message, stack trace, request ID, user ID, endpoint, response code, duration

### Evidence Preservation

Capture the log excerpts that matter for the diagnostic report. Include:
- The exact error messages and stack traces
- Timestamps and request IDs
- A normal-vs-error comparison
- Counts and frequencies
