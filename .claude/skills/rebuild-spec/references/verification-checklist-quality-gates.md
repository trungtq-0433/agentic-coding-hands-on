# Verification Checklist: Quality Gates (W4.5, W5.6)
See verification-checklist-universal.md for Universal rules and Pending Marker Rule.

### UserStories (W4.5 quality gate — scoped)

W4.5 reviewer checks ONLY these 5 items. Full UserStories review at W7a.

**Check 1 — Single intent (critical):**
- Each US### has exactly one user action in goal
- Fail: "create, edit, and delete" in one story; "as well as" joining distinct actions
- Only flag critical when verbs describe CLEARLY DISTINCT independent actions

**Check 2 — Human actor (critical):**
- Actor is a named human role (user, admin, manager, guest)
- Fail: actor is "system", "app", "platform", or missing

**Check 3 — Outcome present (warning):**
- "so that..." or equivalent user-visible value statement
- Warning: story missing outcome

**Check 4 — Overly broad scope (warning):**
- Goal uses generic management verb without specific action
- Warning: "manage all user data", "administer the system"
- Acceptable: "manage my account settings" (specific resource, clear scope)

**Check 5 — US### uniqueness (critical):**
- No duplicate codes
- Fail: US005 appears twice

**Token budget:** user-stories.md only.


### FeatureList (W5.6 fast gate — scoped)

W5.6 reviewer checks these 8 items across 3 groups. Full FeatureList review happens at W7a.

**Group A — Structural integrity (critical on fail):**

**Check 1 — US### coverage:**
- Every US### in user-stories.md appears in at least one F###
- Fail: US005 exists in user-stories.md but no F### references it

**Check 2 — SCR### coverage:**
- Every SCR### main entry in screen-list.md owned by at least one F###
- Fail: SCR008 in screen-list.md, no F### has SCR008 in Related Screens

**Check 3 — Orphan codes:**
- No US### or SCR### in FeatureList that don't exist in their source artifact
- Fail: F003 references US099 but user-stories.md has no US099

**Check 4 — F-code uniqueness:**
- No duplicate F-code numbers across Feature Details
- Fail: F003_Auth and F003_Profile both exist

**Group B — Quality criteria per F### (critical or warning):**

**Check 5 — Single Intent (critical):**
- Each F### describes exactly one user-facing intent
- Fail: F003_UserManagement covers login + profile + admin (3 intents)

**Check 6 — Clear Flow (warning):**
- Identifiable input→process→output for each F###
- Fail: F007_System — no discernible user trigger or outcome

**Check 7 — Vague naming (warning):**
- F### name is not a standalone generic noun: "Management", "System", "Handler", "CRUD"
- Acceptable if project has ≤5 features total

**Check 8 — Scope overlap (warning):**
- Two F### do not share >50% of description keywords indicating duplicate scope

**Group C — Grouping coherence (critical):**

**Check 9 — Grouping coherence:**
- Each F###'s US###/SCR### set is thematically coherent
- Fail: F001_Auth owns payment-related US### codes

**Output format:** `feature-list-review.md` with YAML frontmatter `passed: bool, issues: int, warnings: int`.
**Token budget:** full feature-list.md (needs Feature Details); user-stories.md headers + US### list; screen-list.md SCR### index only.

