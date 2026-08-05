# Telegram Notification Hook

Fire a Telegram message whenever a Claude Code session or subagent finishes. Two files handle delivery: `notify.cjs` (entry point) and `providers/telegram.cjs` (transport). No bash script — CJS only.

---

## 1. Create a Bot

1. Open Telegram, start a chat with **@BotFather**.
2. Send `/newbot`. Follow the prompts — pick any name and username.
3. BotFather replies with a token like `7123456789:AAFooBarBazQux-ExampleToken`. Save it.

## 2. Get Your Chat ID

### Personal (DM)

Send any message to your bot, then fetch:

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```

Find `result[0].message.chat.id` — that integer is your chat ID.

Quick one-liner:

```bash
curl -s "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates" | jq '.result[-1].message.chat.id'
```

### Group / Team Channel

Add the bot to the group, then send it a mention (`@your_bot_username hello`). Hit the same `getUpdates` URL. Group chat IDs are negative (e.g. `-1001234567890`).

## 3. Set Environment Variables

The hook reads `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`. Priority order (highest first):

1. Shell environment (`process.env`)
2. `.claude/.env` — project-level
3. `.claude/hooks/.env` — hook-only

Pick one location. Example for `.claude/.env` (recommended for per-project isolation):

```env
TELEGRAM_BOT_TOKEN=7123456789:AAFooBarBazQux-ExampleToken
TELEGRAM_CHAT_ID=112233445
```

For global use across all projects, export from your shell profile (`~/.zshrc`, `~/.bashrc`):

```bash
export TELEGRAM_BOT_TOKEN="7123456789:AAFooBarBazQux-ExampleToken"
export TELEGRAM_CHAT_ID="112233445"
```

Variable names are exact — no aliases accepted:
- `TELEGRAM_BOT_TOKEN` (not `BOT_TOKEN`, not `TELEGRAM_TOKEN`)
- `TELEGRAM_CHAT_ID` (not `CHAT_ID`, not `TELEGRAM_ID`)

## 4. Register the Hook

Add to `.claude/settings.local.json`:

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "node ${CLAUDE_PROJECT_DIR}/.claude/hooks/notifications/notify.cjs"
      }]
    }],
    "SubagentStop": [{
      "hooks": [{
        "type": "command",
        "command": "node ${CLAUDE_PROJECT_DIR}/.claude/hooks/notifications/notify.cjs"
      }]
    }]
  }
}
```

`Stop` fires when the main session ends. `SubagentStop` fires when a specialised subagent (planner, tester, reviewer, etc.) finishes. Register both or just `Stop` — your call.

## 5. Smoke Test

Pipe a mock event directly:

```bash
echo '{
  "hook_event_name": "Stop",
  "cwd": "'"$(pwd)"'",
  "session_id": "smoke-test-001"
}' | node .claude/hooks/notifications/notify.cjs
```

Check Telegram for the message. For a subagent mock:

```bash
echo '{
  "hook_event_name": "SubagentStop",
  "cwd": "'"$(pwd)"'",
  "session_id": "smoke-test-002",
  "agent_type": "tester"
}' | node .claude/hooks/notifications/notify.cjs
```

> Hook events use snake_case field names per the Claude Code API contract.

---

## What the Notifications Look Like

**Session complete (`Stop`):**
```
🚀 Session Complete

📅 2026-03-14 09:41:22
📁 Project: my-api-service
🔧 Operations: 11
🆔 Session: d4e5f6a7...

Tools Used:
   4 Edit
   3 Read
   2 Bash
   1 Write
   1 Grep

Files Modified:
• src/handlers/webhook.ts
• src/lib/queue.ts
• tests/webhook.test.ts

📍 /Users/dev/projects/my-api-service
```

**Subagent complete (`SubagentStop`):**
```
🤖 Subagent Complete

📅 2026-03-14 09:48:05
📁 Project: my-api-service
🔧 Agent: tester
🆔 Session: d4e5f6a7...

Specialized agent completed its task.

📍 /Users/dev/projects/my-api-service
```

---

## Multiple Channels

Route different event types to separate chats via optional env vars:

```env
TELEGRAM_BOT_TOKEN=7123456789:AAFooBarBazQux-ExampleToken
TELEGRAM_CHAT_ID=112233445
TELEGRAM_CHAT_ID_SUCCESS=112233445
TELEGRAM_CHAT_ID_ERROR=998877665
```

Custom filtering logic (skip tiny operations, throttle off-hours) belongs in `providers/telegram.cjs`.

## Per-Project Bots

Scope credentials per project with project-level `.claude/.env`:

```env
# Project A — .claude/.env
TELEGRAM_BOT_TOKEN=7111111111:AAProjectAlphaToken
TELEGRAM_CHAT_ID=100200300

# Project B — .claude/.env
TELEGRAM_BOT_TOKEN=7222222222:AAProjectBetaToken
TELEGRAM_CHAT_ID=400500600
```

---

## Troubleshooting

**`TELEGRAM_BOT_TOKEN environment variable not set`**
- Confirm the variable is exported: `echo $TELEGRAM_BOT_TOKEN`
- If set in shell profile, reload it: `source ~/.zshrc`
- Confirm the key is exactly `TELEGRAM_BOT_TOKEN`

**`TELEGRAM_CHAT_ID environment variable not set`**
- Rerun the `getUpdates` flow — the chat ID must be a plain integer, no quotes inside the value.

**No message arrives**
- Verify the token is valid: `curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"` — expect bot info back.
- Send a test message directly: `curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" -d "chat_id=$TELEGRAM_CHAT_ID" -d "text=ping"`
- For DM bots: you must send the bot at least one message first before it can reply to you.
- For group bots: confirm the bot is still a member (group → Members).
- If the Telegram chat shows a "Restart" button, the bot was blocked — tap Restart.

**Hook never fires**
- Validate `.claude/settings.local.json` is valid JSON: `node -e "require('./.claude/settings.local.json')" && echo ok`
- Confirm the command path references `notify.cjs`, not an old `.sh` script.
- Run the smoke test in §5 to isolate the hook from Claude Code itself.

**Escaped markdown in message**
Test the parse mode directly:
```bash
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
  -H "Content-Type: application/json" \
  -d "{\"chat_id\": \"$TELEGRAM_CHAT_ID\", \"text\": \"*bold* _italic_\", \"parse_mode\": \"Markdown\"}"
```

**`jq: command not found`** (only needed for the one-liner chat-ID lookup)
```bash
brew install jq       # macOS
apt-get install jq    # Debian/Ubuntu
yum install jq        # RHEL/CentOS
```

---

## Security

- Add `.env` and `.env.*` to `.gitignore` — never commit tokens.
- Rotate via BotFather: `/mybots` → select bot → API Token → Revoke current token → copy new token → update config.
- Bots need only send-message permission. Don't grant admin rights in groups.
- Keep chat IDs out of public repos — treat them as semi-sensitive identifiers.

---

## Reference

| Item | Value |
|---|---|
| Entry point | `.claude/hooks/notifications/notify.cjs` |
| Transport | `.claude/hooks/notifications/providers/telegram.cjs` |
| Hook config | `.claude/settings.local.json` |
| Required vars | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| Supported events | `Stop`, `SubagentStop` |
| Runtime | Node.js only — no `bash`, `curl`, or `jq` at runtime |
| Telegram Bot API | https://core.telegram.org/bots/api |
| Claude Code Hooks | https://docs.claude.com/claude-code/hooks |
