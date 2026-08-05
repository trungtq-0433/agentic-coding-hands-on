# Runtime Awareness

Keep an eye on quota and window fill as the session runs, and tune accordingly.

## Overview

Two numbers are worth watching live:
1. **Usage Limits** - how much API quota you have burned (5-hour and 7-day rolling windows)
2. **Context Window** - how full the 200K window currently is

## Architecture

```
┌─────────────────┐    ┌──────────────────────────┐
│  statusline.cjs │───▶│  /tmp/sk-context-*.json  │
│  (writes data)  │    │  (context window data)   │
└─────────────────┘    └────────────┬─────────────┘
                                    │
                       ┌────────────▼─────────────┐
                       │  usage-context-hook.cjs  │◀── PostToolUse
                       │  - Reads context file    │
                       │  - Fetches usage limits  │
                       │  - Injects awareness     │
                       └──────────────────────────┘
```

## Usage Limits API

### Endpoint

```
GET https://api.anthropic.com/api/oauth/usage
```

### Authentication

Send an OAuth Bearer token along with the `anthropic-beta: oauth-2025-04-20` header.

### Credential Locations

| Platform | Method | Location |
|----------|--------|----------|
| macOS | Keychain | `Claude Code-credentials` |
| Windows | File | `%USERPROFILE%\.claude\.credentials.json` |
| Linux | File | `~/.claude/.credentials.json` |

### Response Structure

```json
{
  "five_hour": {
    "utilization": 45,
    "resets_at": "2025-01-15T18:00:00Z"
  },
  "seven_day": {
    "utilization": 32,
    "resets_at": "2025-01-22T00:00:00Z"
  },
  "seven_day_sonnet": {
    "utilization": 11,
    "resets_at": "2025-01-15T09:00:00Z"
  }
}
```

- `utilization`: comes through as a 0-100 percentage, not a decimal fraction
- `resets_at`: an ISO 8601 timestamp marking when the quota clears
- `seven_day_sonnet`: a per-model limit, which can be null

## Context Window Data

### Source

The statusline drops context data into `/tmp/sk-context-{session_id}.json`:

```json
{
  "percent": 67,
  "tokens": 134000,
  "size": 200000,
  "usage": {
    "input_tokens": 80000,
    "cache_creation_input_tokens": 30000,
    "cache_read_input_tokens": 24000
  },
  "timestamp": 1705312000000
}
```

### Token Calculation

```
total = input_tokens + cache_creation_input_tokens + cache_read_input_tokens
percent = (total + AUTOCOMPACT_BUFFER) / context_window_size * 100
```

Here `AUTOCOMPACT_BUFFER = 45000`, holding back 22.5% of the window.

## Hook Output

On a 5-minute cadence, the PostToolUse hook injects the awareness block:

```xml
<usage-awareness>
Limits: 5h=45%, 7d=32%
Context: 67%
</usage-awareness>
```

### Warning Indicators

| Level | Threshold | Indicator |
|-------|-----------|-----------|
| Normal | < 70% | Plain percentage |
| Warning | 70-89% | `[WARNING]` |
| Critical | ≥ 90% | `[CRITICAL]` |

### Examples

Normal state:
```xml
<usage-awareness>
Limits: 5h=45%, 7d=32%
Context: 67%
</usage-awareness>
```

Warning state:
```xml
<usage-awareness>
Limits: 5h=75% [WARNING], 7d=32%
Context: 78% [WARNING - consider compaction]
</usage-awareness>
```

Critical state:
```xml
<usage-awareness>
Limits: 5h=92% [CRITICAL], 7d=65%
Context: 91% [CRITICAL - compaction needed]
</usage-awareness>
```

## Recommendations by Threshold

### Context Window

| Utilization | Action |
|-------------|--------|
| < 70% | Carry on as usual |
| 70-80% | Line up a compaction plan |
| 80-90% | Run the compaction |
| > 90% | Compact now, or reset the session |

### Usage Limits

| 5-Hour | Action |
|--------|--------|
| < 70% | Use it freely |
| 70-90% | Dial back parallelism, push work to subagents |
| > 90% | Hold for the reset or drop to a lower-tier model |

| 7-Day | Action |
|-------|--------|
| < 70% | Use it freely |
| 70-90% | Keep an eye on the daily burn |
| > 90% | Spend only on what is essential |

## Configuration

### Hook Settings (`.claude/settings.json`)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "node .claude/hooks/usage-quota-cache-refresh.cjs"
        }]
      }
    ]
  }
}
```

### Throttling

- **Injection interval**: every 5 minutes (300,000ms)
- **API cache TTL**: 60 seconds
- **Context data freshness**: 30 seconds

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| No usage limits shown | OAuth token missing | Run `claude login` |
| Stale context data | Statusline has stopped writing | Check statusline config |
| 401 Unauthorized | Token has expired | Re-authenticate |
| Hook not firing | Settings are wrong | Verify the PostToolUse matcher |
