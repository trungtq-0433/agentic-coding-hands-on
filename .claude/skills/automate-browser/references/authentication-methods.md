# Authentication & Cookies

For accessing protected/authenticated pages, use one of these methods:

### Method 1: Inject Cookies Directly

Use when you have cookie values (from DevTools or manual extraction):

```bash
# Inject single cookie
node "$SKILL_DIR/inject-auth.js" --url https://site.com \
  --cookies '[{"name":"session","value":"abc123","domain":".site.com"}]'

# Multiple cookies with all properties
node "$SKILL_DIR/inject-auth.js" --url https://site.com \
  --cookies '[{"name":"session","value":"abc","domain":".site.com","httpOnly":true,"secure":true}]'

# With Bearer token header
node "$SKILL_DIR/inject-auth.js" --url https://api.site.com \
  --token "Bearer eyJhbG..." --header Authorization
```

### Method 2: Import from Browser Extension

Best for complex auth (OAuth, multi-cookie sessions):

```bash
# 1. Install "Cookie-Editor" or "EditThisCookie" Chrome extension
# 2. Navigate to site → Log in manually
# 3. Click extension → Export as JSON → Save to cookies.json
# 4. Import into puppeteer session:

node "$SKILL_DIR/import-cookies.js" --file ./cookies.json --url https://site.com

# Netscape format (from curl/wget):
node "$SKILL_DIR/import-cookies.js" --file ./cookies.txt --format netscape --url https://site.com

# Only import cookies matching target domain:
node "$SKILL_DIR/import-cookies.js" --file ./cookies.json --url https://site.com --strict-domain
```

### Method 3: Use Your Chrome Profile

Most reliable for complex auth (2FA, OAuth, SSO). Uses your existing Chrome session:

```bash
# Use Chrome's default profile (preserves all cookies, extensions, saved passwords)
node "$SKILL_DIR/navigate.js" --url https://site.com --use-default-profile true

# Use specific Chrome profile directory
node "$SKILL_DIR/navigate.js" --url https://site.com --profile "/path/to/chrome/profile"
```

**[!] Important**: Chrome must be fully closed when using its profile (single instance lock).

**Profile paths by OS:**
- **macOS**: `~/Library/Application Support/Google/Chrome`
- **Windows**: `%LOCALAPPDATA%/Google/Chrome/User Data`
- **Linux**: `~/.config/google-chrome`

### Method 4: Connect to Running Chrome

Best for debugging (can see browser window while scripts run):

```bash
# Step 1: Launch Chrome with remote debugging (in separate terminal)
# macOS:
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# Windows:
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

# Linux:
google-chrome --remote-debugging-port=9222

# Step 2: Log in manually in the Chrome window

# Step 3: Connect and automate
node "$SKILL_DIR/connect-chrome.js" --browser-url http://localhost:9222 --url https://site.com

# Or launch Chrome automatically (opens new window):
node "$SKILL_DIR/connect-chrome.js" --launch --port 9222 --url https://site.com
```

### Method 5: Interactive Login (OAuth/SSO)

Best for OAuth, SSO, or any login requiring manual interaction in the browser:

```bash
# Open browser at login page, wait for redirect to dashboard after OAuth
node "$SKILL_DIR/navigate.js" --url https://app.example.com/login \
  --wait-for-login "/dashboard"

# With longer timeout (10 min) for slow SSO providers
node "$SKILL_DIR/navigate.js" --url https://app.example.com/login \
  --wait-for-login "/dashboard" --login-timeout 600000

# Use regex for complex URL patterns
node "$SKILL_DIR/navigate.js" --url https://app.example.com/login \
  --wait-for-login "/(dashboard|home|app)"
```

**How it works:**
1. Opens browser in **headed mode** (always, regardless of OS)
2. Navigates to the login URL
3. Waits for you to complete the login flow manually (OAuth, 2FA, etc.)
4. Detects success when URL matches the regex pattern
5. Saves all cookies to `.auth-session.json` for 24-hour reuse
6. Subsequent scripts reuse the authenticated session automatically

### Session Persistence

Auth sessions are saved to `.auth-session.json` for 24-hour reuse:

```bash
# First script injects auth
node "$SKILL_DIR/inject-auth.js" --url https://site.com --cookies '[...]'

# Subsequent scripts reuse saved auth automatically
node "$SKILL_DIR/navigate.js" --url https://site.com/dashboard
node "$SKILL_DIR/screenshot.js" --url https://site.com/profile --output ./profile.png

# Clear auth session when done
node "$SKILL_DIR/inject-auth.js" --url https://site.com --clear true
```

### Choosing the Right Method

| Method | Best For | Complexity |
|--------|----------|------------|
| Inject cookies | Simple session cookies, API tokens | Low |
| Import from extension | Multi-cookie auth, OAuth tokens | Medium |
| Chrome profile | 2FA, SSO, complex OAuth flows | Low* |
| Connect to Chrome | Debugging, visual verification | Medium |
| Interactive login | OAuth/SSO with manual browser interaction | Low |

*Requires Chrome to be closed first
