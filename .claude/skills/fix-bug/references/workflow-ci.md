# CI/CD Fix Workflow

For GitHub Actions failures and broken CI/CD pipelines.

## Prerequisites
- `gh` CLI installed and authorized
- A GitHub Actions URL or run ID

## Workflow

1. **Pull the logs** with the `debugger` agent:
   ```bash
   gh run view <run-id> --log-failed
   gh run view <run-id> --log
   ```

2. **Read** the root cause out of the logs

3. **Build the fix** from what you found

4. **Run it locally** with the `tester` agent before you push

5. **Go again** if the tests fail — back to step 3

## Notes
- No `gh`? Tell the user to set it up: `gh auth login`
- Read the failing step *and* the ones before it for context
- Usual suspects: env vars, dependencies, permissions, timeouts
