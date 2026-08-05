# View Mode

## Execution

**IMPORTANT:** launch the server as a Claude Code background task — pass `run_in_background: true` to the Bash tool.

The skill itself lives at `.claude/skills/markdown-novel-viewer/`.

### Stop Server

When the `--stop` flag comes in:

```bash
node .claude/skills/markdown-novel-viewer/scripts/server.cjs --stop
```

### Start Server

Start the `markdown-novel-viewer` server as a CC background task, with the `--foreground` flag:

```bash
INPUT_PATH="<resolved-path>"
if [[ -d "$INPUT_PATH" ]]; then
  node .claude/skills/markdown-novel-viewer/scripts/server.cjs \
    --dir "$INPUT_PATH" --host 0.0.0.0 --open --foreground
else
  node .claude/skills/markdown-novel-viewer/scripts/server.cjs \
    --file "$INPUT_PATH" --host 0.0.0.0 --open --foreground
fi
```

**Critical:** in the Bash tool call:
- Set `run_in_background: true`
- Set `timeout: 300000` (5 minutes)
- Parse the JSON output and hand the URL back to the user

Once it's up, report:
- The local URL for browsing
- The network URL for reaching it from another device
- That the server is now a CC background task (you'll find it under `/tasks`)

**CRITICAL:** show the FULL URL — path and query string included. NEVER clip it down to `host:port`.
