---
description: Send free-text feedback about Takumi Agent Kit to the team
argument-hint: [your feedback text]
---

<feedback-text>$ARGUMENTS</feedback-text>

You are relaying user feedback about Takumi Agent Kit. Follow this protocol exactly.

## Steps

1. **Get the feedback text.**
   - If `<feedback-text>` is non-empty, use it as-is.
   - If empty, ask the user: "What's your feedback about Takumi Agent Kit?" and wait for their reply. Use that reply as the feedback text.

2. **Send it** via the telemetry client using Bash:
   ```bash
   node "${CLAUDE_PLUGIN_ROOT:-$PWD}/.claude/hooks/lib/telemetry-client.cjs" send-feedback \
     --text="<escaped feedback>" \
     --session-id="${CLAUDE_SESSION_ID:-${TKM_SESSION_ID:-}}"
   ```
   - Escape double-quotes and backticks in the feedback text before substituting.
   - `session_id` is optional — if the env var is unset the command sends `null`.
   - The command prints a single JSON status line (e.g. `{"ok":true,"status":204}`).

3. **Report the result** to the user in one short sentence:
   - `ok:true` → "Thanks — feedback sent."
   - `error:"no_github_login"` → "Feedback not sent: run `sk init` first to set your GitHub identity."
   - `error:"no_endpoint"` or `error:"no_token"` → "Feedback not sent: telemetry is not configured in this kit install."
   - `error:"empty_text"` → "Feedback not sent: empty text."
   - Any other error → "Feedback failed: <error>." (include the raw error)

## Rules

- Do **not** rephrase or summarize the user's feedback — send it verbatim (trimmed + truncated server-side).
- Do **not** send more than once per invocation.
- Do **not** log or print the feedback text in your response; only confirm delivery.
