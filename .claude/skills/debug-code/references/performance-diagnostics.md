# Performance Diagnostics

Find the bottleneck, measure what the queries cost, and shape a plan to make it faster.

## When to Use

- Response times have climbed noticeably
- The app feels sluggish or unresponsive
- Database queries drag on
- CPU, memory, or disk running hot
- Resources running out, or OOM errors

## Diagnostic Process

### 1. Quantify the Problem

**Measure before you optimize.** Pin down the baseline and where things stand now.

- What's the expected response time against the actual?
- When did it start slipping? (line it up with changes)
- Which endpoints or operations feel it?
- Is it steady or intermittent?

### 2. Identify the Bottleneck Layer

```
Request → Network → Web Server → Application → Database → Filesystem
                                      ↓
                              External APIs / Services
```

**How to narrow it:** time each layer and see where the delay actually lands.

| Layer | Check | Tool |
|-------|-------|------|
| Network | Latency, DNS, TLS | `curl -w` timing, network logs |
| Web server | Request queue, connections | Server metrics, access logs |
| Application | CPU profiling, memory | Profiler, APM, `process.memoryUsage()` |
| Database | Query time, connections | `EXPLAIN ANALYZE`, `pg_stat_statements` |
| Filesystem | I/O wait, disk usage | `iostat`, `df -h` |
| External APIs | Response time, timeouts | Request logging with durations |

### 3. Database Performance

#### PostgreSQL Diagnostics

```sql
-- Slow queries (requires pg_stat_statements extension)
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC LIMIT 20;

-- Active queries right now
SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;

-- Table sizes and bloat
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC LIMIT 20;

-- Missing indexes (sequential scans on large tables)
SELECT relname, seq_scan, seq_tup_read, idx_scan
FROM pg_stat_user_tables
WHERE seq_scan > 100 AND seq_tup_read > 10000
ORDER BY seq_tup_read DESC;

-- Connection pool status
SELECT count(*), state FROM pg_stat_activity GROUP BY state;
```

#### Query Optimization

```sql
-- Analyze specific query execution plan
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) <your-query>;
```

**Watch for:** sequential scans over large tables, nested loops chewing through high row counts, sorts with no index behind them, buffer hits running far higher than they should.

### 4. Application Performance

**Where bottlenecks usually hide:**

| Issue | Symptom | Fix |
|-------|---------|-----|
| N+1 queries | Many tiny DB calls per request | Eager loading, batch queries |
| Memory leaks | Memory creeping up over time | Profile the heap, check event listeners |
| Blocking I/O | High response time, idle CPU | Go async, pool connections |
| CPU-bound | CPU rising in step with load | Sharpen the algorithm, add caching |
| Connection exhaustion | Timeouts that come and go | Size the pool, reuse connections |
| Large payloads | Slow transfers, heavy memory | Paginate, compress, stream |

### 5. Optimization Strategy

**Work it in this order:**
1. **Quick wins** - Add the missing index, kill the N+1, switch on caching
2. **Configuration** - Pool sizes, timeouts, buffer sizes, worker counts
3. **Code changes** - Better algorithms, better data structures
4. **Architecture** - A caching layer, read replicas, async processing, a CDN

**Always:** measure after every change to confirm it helped. One change at a time.

## Reporting Performance Issues

Put this in the diagnostic report:
- **Baseline vs current** metrics (with the numbers)
- **The bottleneck**, named, with evidence
- **The root cause**, explained
- **Recommended fixes** and the impact you expect
- **A verification plan** to confirm the gain
