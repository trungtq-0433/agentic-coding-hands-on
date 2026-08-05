# Checklist-Based Review Workflow

Running the structured review checklists against a diff during code review.

## When to Use

- Pre-landing review (from `/tkm:ship` pipeline)
- Explicit request for checklist review
- Security audit before release
- The code-reviewer agent on anything sizable (10+ files, or security-sensitive)

## Workflow

### 1. Auto-Detect Project Type

```bash
# Check for web app frameworks
if grep -qE '"(react|vue|svelte|next|nuxt|angular)"' package.json 2>/dev/null; then
  echo "web-app"
# Check for API patterns
elif ls src/routes/ src/api/ src/controllers/ app/controllers/ 2>/dev/null | head -1; then
  echo "api"
else
  echo "base-only"
fi
```

### 2. Load Checklists

Always load: `checklists/base.md`

Overlay based on detection:
- `web-app` → also load `checklists/web-app.md`
- `api` → also load `checklists/api.md`
- Both detected → load both overlays

### 3. Get the Diff

```bash
git fetch origin main --quiet
git diff origin/main
```

**CRITICAL:** Read the diff end to end before you flag a single thing — the suppressions only make sense with the whole picture.

### 4. Two-Pass Review

**Pass 1 (CRITICAL) — Run first:**
- Run the diff past every critical category (base + overlays)
- Each finding carries: `[file:line]`, the problem, the fix
- These halt the `/ship` pipeline

**Pass 2 (INFORMATIONAL) — Run second:**
- Run the diff past every informational category (base + overlays)
- Same shape: `[file:line]`, the problem, the fix
- They ride along in the PR body but block nothing

### 5. Check Suppressions

Before any finding goes out, make sure it isn't on the suppressions list (foot of `base.md`).

Key suppressions:
- Already addressed in the diff
- Readability-aiding redundancy
- Style/formatting issues
- "Consider using X" when Y works fine

### 6. Output

```
Pre-Landing Review: N issues (X critical, Y informational)

**CRITICAL** (blocking):
- [src/auth/login.ts:42] SQL injection via string interpolation in user lookup
  Fix: Use parameterized query: `db.query('SELECT * FROM users WHERE email = $1', [email])`

**Issues** (non-blocking):
- [src/api/users.ts:88] Magic number 30 for pagination limit
  Fix: Extract to constant `DEFAULT_PAGE_SIZE = 30`
```

### 7. Critical Issue Resolution

For each critical issue, use `AskUserQuestion`:
- Problem with `file:line`
- Recommended fix
- Options:
  - A) Fix now (recommended)
  - B) Acknowledge and proceed
  - C) False positive — skip

Picked A (fix)? Apply the fixes, commit, and re-run the tests before you carry on.

## Integration with /tkm:ship

Ship calls into this workflow at Step 4. A Critical finding stops the pipeline cold; informational ones just land in the PR body.

## Integration with /tkm:review-code

Inside a standard code review, the checklist rides alongside the scout → review → fix → verify pipeline rather than replacing it. Its findings fold in with the reviewer's own.
