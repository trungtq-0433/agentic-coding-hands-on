# Frontend Verification

See the frontend work with your own eyes — drive it through Chrome MCP (Claude Chrome Extension), falling back to the `tkm:automate-browser` skill.

## Applicability Check

**If the task isn't frontend, skip this whole thing.** Signs that it is:
- Files touched: `*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, `*.html`, `*.css`, `*.scss`
- Changes to: components, layouts, pages, styles, DOM structure, UI behavior
- Keywords: render, display, layout, responsive, animation, visual, UI, UX

Nothing matches? Move on — this technique doesn't apply.

## Step 1: Detect Chrome MCP Availability

Ask `ListMcpResourcesTool` whether a Chrome MCP server is wired up:

```
Use ListMcpResourcesTool to check for Chrome MCP tools.
Look for tools prefixed with "chrome__" (e.g., chrome__navigate, chrome__screenshot).
```

**There** → go to Step 2A (Chrome MCP)
**Missing** → go to Step 2B (chrome-devtools fallback)

## Step 2A: Chrome MCP Available — Direct Verification

Drive the Chrome MCP tools to check the work in the user's real browser. Get the dev server running first.

### Navigate & Screenshot

```
1. chrome__navigate → http://localhost:3000 (or project dev URL)
2. chrome__screenshot → capture current page state
3. Read the screenshot with Read tool to visually inspect
```

### Visual Inspection Checklist

With the screenshot in hand, check:
1. **Layout** — Everything where it belongs, nothing overflowing or overlapping
2. **Content** — Text, images, and data rendered the way you expected
3. **Responsiveness** — Resize the viewport if the MCP allows it
4. **Interactions** — Exercise the interactive bits with chrome__click / chrome__type
5. **Console errors** — Use chrome__evaluate to read the `console.error` output

### Console Error Check

```
chrome__evaluate → "JSON.stringify(window.__consoleErrors || [])"
```

Or navigate and watch for error output coming back in the Chrome MCP tool responses.

### Get Page Content

```
chrome__get_content → extract DOM/text to verify rendered output matches expectations
```

## Step 2B: Chrome MCP NOT Available — Fallback to chrome-devtools Skill

With no Chrome MCP configured, fall back to the `tkm:automate-browser` skill (Puppeteer with bundled Chromium):

```bash
SKILL_DIR="$HOME/.claude/skills/chrome-devtools/scripts"

# Install deps if first time
npm install --prefix "$SKILL_DIR" 2>/dev/null

# Screenshot + console error check
node "$SKILL_DIR/screenshot.js" --url http://localhost:3000 --output ./verification-screenshot.png
node "$SKILL_DIR/console.js" --url http://localhost:3000 --types error,pageerror --duration 5000
```

If the `tkm:automate-browser` skill is gone too, skip the visual check and say so in the report:
> "Visual verification skipped — no Chrome MCP or chrome-devtools available."

## Step 3: Analyze Results

Once you've captured it:
1. **Read the screenshot** — Open the PNG with the Read tool and look it over
2. **Read the console** — No errors means pass; any errors mean investigate before you call it done
3. **Hold it against the expected** — Match it to the design specs or the user's description
4. **Write down what you found** — Put the screenshot path and any issues into the verification report

## Integration with Verification Protocol

This technique builds on `verification.md`. After the standard checks (tests pass, build succeeds), make frontend verification the last gate:

```
Standard verification → Tests pass → Build succeeds → Frontend visual verification → Claim complete
```

Report format:
```
## Frontend Verification
- Method: [Chrome MCP | chrome-devtools | skipped]
- Screenshot: ./verification-screenshot.png
- Console errors: [none | list]
- Visual check: [pass | issues found]
- Responsive: [checked at X viewports | skipped]
```
