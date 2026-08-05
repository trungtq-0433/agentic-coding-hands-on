# UI Testing Workflow

Bring up the tkm:automate-browser skill first.

## Purpose
Put a website through a thorough UI pass and write up what you find.

## Arguments
- $1: URL - the site under test
- $2: OPTIONS - optional run flags (e.g., --headless, --mobile, --auth)

## Testing Protected Routes (Authentication)

### Step 1: User Manual Login
Walk the user through it:
1. Open the target site in their browser
2. Sign in by hand with their own credentials
3. Open browser DevTools (F12) → Application tab → Cookies/Storage

### Step 2: Extract Auth Credentials
Have the user hand back one of these:
- **Cookies**: the cookie values (name, value, domain)
- **Access Token**: the JWT/Bearer token out of localStorage or cookies
- **Session Storage**: whichever session keys matter

### Step 3: Inject Authentication
Drive it in with the `inject-auth.js` script:

```bash
cd $SKILL_DIR  # .claude/skills/chrome-devtools/scripts

# Option A: Inject cookies
node inject-auth.js --url https://example.com --cookies '[{"name":"session","value":"abc123","domain":".example.com"}]'

# Option B: Inject Bearer token
node inject-auth.js --url https://example.com --token "Bearer eyJhbGciOi..." --header Authorization --token-key access_token

# Option C: Inject localStorage
node inject-auth.js --url https://example.com --local-storage '{"auth_token":"xyz","user_id":"123"}'
```

### Step 4: Run Tests
With auth in place, the tests run as usual:
```bash
node navigate.js --url https://example.com/dashboard
node screenshot.js --url https://example.com/profile --output profile.png
```

## Workflow
- Lean on the `tkm:create-plan` skill to lay out the test plan and report
- Every screenshot lands in the one report directory
- Walk the URL, map out the pages, components, and endpoints
- Shape the test plan around what you found
- Fan out across `tester` subagents in parallel — pages, forms, navigation, user flows, accessibility, responsive layouts, performance, security, seo
- Read each screenshot back through the Read tool
- Write the full Markdown report
- Offer the user a preview via `/tkm:preview-output`

## Output Requirements
- Clean, structured Markdown — headers, lists, code blocks
- Carry the results summary, the findings that matter, and the screenshot references
- Stay token-light without dropping quality
- Trade grammar for concision

**Do not** start patching anything.
