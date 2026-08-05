---
description: Rate this Takumi Agent Kit session (0–3) with an optional comment
argument-hint: <0|1|2|3> [optional comment]
---

<rating-input>$ARGUMENTS</rating-input>

You are relaying a user rating for Takumi Agent Kit. Follow this protocol exactly.

## Steps

1. **Parse the rating.**
   - The first whitespace-separated token of `<rating-input>` must be `0`, `1`, `2`, or `3`.
   - Everything after that first token (if any) is the optional comment.
   - If the first token is missing or not one of `0|1|2|3`, reply:
     `Usage: /tkm:rate <0|1|2|3> [optional comment] — 0=Chưa hiệu quả, 1=Bình thường, 2=Có ích, 3=Rất hữu ích`
     and **do not** call the telemetry client.

2. **Send it** via the telemetry client using Bash. Pass the comment through an
   environment variable so shell metacharacters can't be interpreted:
   ```bash
   TKM_RATE_COMMENT=$'<raw comment text>' \
   node "${CLAUDE_PLUGIN_ROOT:-$PWD}/.claude/hooks/lib/telemetry-client.cjs" send-rating \
     --score="<SCORE>" \
     --comment="$TKM_RATE_COMMENT" \
     --session-id="${CLAUDE_SESSION_ID:-${TKM_SESSION_ID:-}}"
   ```
   - Use a `$'...'` single-quoted (ANSI-C) string so `$`, `` ` ``, `"`, and `\`
     in the user's comment are not interpreted by the shell. Inside `$'...'`
     the only character you need to escape is a single quote (as `\'`).
   - If the user gave no comment, omit the `TKM_RATE_COMMENT=...` assignment
     and pass `--comment=""`.
   - Never construct the comment flag by concatenating the raw user text into a
     double-quoted string — that path allows `$(...)` / backtick injection.
   - The command prints a single JSON status line (e.g. `{"ok":true,"status":204}`).

3. **Report the result** to the user in one short sentence:
   - `ok:true` → "Thanks — rating recorded." (add "We'll use score=0 notes to dig deeper." only when the score was 0)
   - `error:"invalid_score"` → "Rating not sent: score must be 0, 1, 2, or 3."
   - `error:"no_github_login"` → "Rating not sent: run `sk init` first to set your GitHub identity."
   - `error:"no_endpoint"` or `error:"no_token"` → "Rating not sent: telemetry is not configured in this kit install."
   - Any other error → "Rating failed: <error>."

## Rules

- Do **not** rephrase the comment — send it verbatim (trimmed + truncated server-side).
- Do **not** send more than once per invocation.
- Never prompt for a second rating in the same turn.
