# Investigation Methodology

A five-step approach for system-level trouble — incidents and failures that span more than one component.

## When to Use

- Server throwing 500s or returning responses you didn't expect
- System behavior shifted with no obvious code change behind it
- Failures crossing several services, databases, or pieces of infrastructure
- You need to understand "what happened" before you can fix anything

## Step 1: Initial Assessment

**Map the scope and the impact before you dig in.**

1. **Collect the symptoms** - Error messages, affected endpoints, what users report
2. **Name the affected components** - Which services, databases, or queues are in play?
3. **Fix the timeframe** - When did it start? Line it up against deployments and changes
4. **Weigh the severity** - How many users? Any data at risk? Revenue on the line?
5. **Review what changed** - Git log, deployment history, config edits, dependency bumps

```bash
# Recent deployments
gh run list --limit 10
# Recent commits
git log --oneline -20 --since="2 days ago"
# Config changes
git diff HEAD~5 -- '*.env*' '*.config*' '*.yml' '*.yaml' '*.json'
```

## Step 2: Data Collection

**Gather the evidence in order, before you start interpreting it.**

1. **Server/application logs** - Narrow to the timeframe and the affected components
2. **CI/CD pipeline logs** - For GitHub Actions, run `gh run view <run-id> --log-failed`
3. **Database state** - Query the relevant tables, look at recent migrations
4. **System metrics** - CPU, memory, disk, network use
5. **External dependencies** - Status of third-party APIs, DNS, the CDN

```bash
# GitHub Actions: list recent workflow runs
gh run list --workflow=<workflow> --limit 5
# View failed run logs
gh run view <run-id> --log-failed
# Download full logs
gh run view <run-id> --log > /tmp/ci-logs.txt
```

**To get oriented in the codebase:**
- Read `docs/codebase-summary.md` if it's there and recent (<2 days old)
- If not, run `tkm:pack-codebase` to produce a fresh summary
- Use `/tkm:scan-codebase` or `/tkm:scan-codebase ext` to surface the relevant files
- Reach for the `tkm:search-docs` skill for package/plugin documentation

## Step 3: Analysis Process

**Line the evidence up across sources and let it talk to itself.**

1. **Rebuild the timeline** - Order the events chronologically across every log source
2. **Spot the patterns** - Repeating errors, timing rhythms, the user segments hit
3. **Trace the execution path** - Follow the request as it moves through the components
4. **Read the database** - Query performance, table relationships, data integrity
5. **Map the dependencies** - What relies on the component that's failing?

**Questions worth asking:**
- Does the issue track with particular deployments or time windows?
- Is it intermittent or steady?
- Does it hit every user or only some?
- Are upstream or downstream services throwing related errors?

## Step 4: Root Cause Identification

**Eliminate candidates one at a time, with evidence.**

1. **List the hypotheses** ranked by how strong the evidence is
2. **Test each one** - Design the smallest experiment that confirms or rules it out
3. **Back it with evidence** - Logs, metrics, reproduction steps
4. **Weigh the environment** - Race conditions, resource limits, config drift
5. **Write down the chain** - The full sequence from trigger to symptom

**Avoid:** locking onto the first hypothesis without testing the rest. Several plausible causes means you eliminate, not assume.

## Step 5: Solution Development

**Shape targeted fixes that the evidence supports.**

1. **Immediate fix** - The smallest change that brings service back (hotfix, rollback, config change)
2. **Root cause fix** - Settle the underlying issue for good
3. **Preventive measures** - Monitoring, alerting, validation to catch a repeat early
4. **Verification plan** - How you'll confirm the fix holds in production

**Order of priority:** impact × urgency. Restore service first, repair the root cause next, prevent the recurrence last.

## Integration with Code-Level Debugging

Once the investigation closes in on specific code:
- Hand off to `systematic-debugging.md` for the code-level fix
- Use `root-cause-tracing.md` when the error sits deep in the call stack
- Apply `defense-in-depth.md` after the fix lands
- Always close out with `verification.md`
