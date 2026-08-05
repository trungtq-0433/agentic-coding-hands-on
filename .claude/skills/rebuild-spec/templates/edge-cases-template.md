<!-- LARGE OUTPUT NOTE: if this file exceeds 400 lines, signal to orchestrator for chunked review -->

# Edge Cases — {F###_NAME}

{MANDATORY — minimum 3 rows for UI features, 1 row for background features.
"User-Facing Message" must be plain language (e.g., "You don't have permission to do this").
"HTTP 400" alone is rejected — always pair with the actual message shown to the user.}

| Scenario | What Happens | User-Facing Message |
|----------|--------------|---------------------|
| {boundary condition / invalid input} | {specific system behavior — what the system does internally} | "{plain-language error or feedback message shown to user}" |
| {concurrent operation / race condition} | {specific system behavior — queue, lock, reject, retry} | "{plain-language message, or "None — silent handling"}" |
| {missing prerequisite / empty state} | {fallback behavior or recovery path} | "{plain-language empty-state message or prompt}" |
| {permission / access violation} | {what the system enforces} | "{plain-language access denied message}" |
