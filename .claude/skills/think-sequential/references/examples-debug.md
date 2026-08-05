# Worked Example — Hunting a Performance Bug Step by Step

**Problem**: An API endpoint crawls — 2–3s where it should answer in under 200ms.

## Sequential Thinking Approach

```
Thought 1/5: Initial investigation

Endpoint: GET /api/users/{id}/dashboard
Expected: <200ms
Actual: 2-3s

Need to identify bottleneck.
Next: Analyze endpoint logic

Thought 2/5: Endpoint analysis

Dashboard fetches:
- User profile
- Recent activities (last 50)
- Notifications (unread)
- Analytics summary

Each is separate DB query. Could be N+1 problem.
Next: Profile actual execution

Thought 3/6: Profiling results (adjusted up—more complex)

Profiling:
- User profile: 20ms
- Activities: 1800ms (!!)
- Notifications: 100ms
- Analytics: 80ms

Activities query is bottleneck (90% of time).
Need to examine that query.
Next: Investigate activities query

Thought 4/6 [BRANCH A]: Hypothesis - N+1 query

Activities table has user_id FK to users.
Query might fetch activities, then user for each (N+1).
Verification: Check if uses joins or loops.

Thought 4/6 [BRANCH B]: Hypothesis - Missing index

Activities table might lack index on user_id + created_at.
Without index, full table scan for user's activities.
Verification: Check table indexes.

Thought 5/6 [VERIFICATION]: Testing hypotheses

Query examination: Uses proper joins (not N+1).
Index check: user_id indexed, NOT created_at.
Query filters by user_id AND sorts by created_at.

Branch B confirmed: Missing composite index causes slow sort.
Branch A eliminated: No N+1 issue.

Root cause identified.
Next: Implement solution

Thought 6/6 [FINAL]: Solution and verification

Create composite index:
```sql
CREATE INDEX idx_activities_user_created
ON activities(user_id, created_at DESC);
```

Tested: Response time now 120ms (target met).

Confidence: High (verified with profiling)
Result: 95% performance improvement
```

## Key Techniques Demonstrated

1. **Branches carried two hypotheses at once**: the N+1 theory and the missing-index theory ran side by side
2. **The fix waited on proof**: both theories were tested before any change
3. **Numbers drove the path**: profiling figures, not hunches, steered the search
4. **The count grew with the difficulty**: thoughts expanded once the real complexity showed
5. **Elimination did the work**: N+1 ruled out, the index issue pinned down

## Comparison

**Without sequential thinking**: you reach for N+1 — the usual suspect — and burn time tuning the wrong thing.

**With sequential thinking**: you test each suspect in turn, find the actual cause, and ship the fix that matters.
