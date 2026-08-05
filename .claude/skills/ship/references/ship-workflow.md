# Ship Workflow — Step by Step

## Step 1: Pre-flight

1. See where you're standing: `git branch --show-current`
   - Landed on the target branch (main/master/dev)? **ABORT** — "Ship from a feature branch, not the target branch."
2. Pin down the ship mode from the arguments:
   - `official` → target = the default branch, auto-detected (main/master)
   - `beta` → target = the dev branch, auto-detected (dev/beta/develop)
   - Nothing passed → read it off the branch name:
     - `feature/* hotfix/* bugfix/*` → official
     - `dev/* beta/* experiment/*` → beta
     - Can't tell → `AskUserQuestion` offering "Official (main)" or "Beta (dev)"
3. Work out the target branch:
   ```bash
   # For official: detect default branch
   git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'
   # Fallback
   git rev-parse --verify origin/main 2>/dev/null && echo "main" || echo "master"

   # For beta: detect dev branch
   for b in dev beta develop; do
     git rev-parse --verify origin/$b 2>/dev/null && echo "$b" && break
   done
   ```
4. Take stock with `git status` (skip `-uall`). Whatever is uncommitted rides along.
5. Get the shape of the shipment: `git diff <target>...HEAD --stat` plus `git log <target>..HEAD --oneline`.
6. Under `--dry-run`: narrate each step's intent and stop right here.

## Step 2: Link Issues

Tie the work back to GitHub issues so the trail stays intact.

1. Hunt for open issues using keywords pulled from the branch name and commit messages:
   ```bash
   # Extract keywords from branch name
   BRANCH=$(git branch --show-current)
   KEYWORDS=$(echo "$BRANCH" | sed 's/[^a-zA-Z0-9]/ /g' | tr '[:upper:]' '[:lower:]')

   # Search existing issues
   gh issue list --state open --limit 10 --search "$KEYWORDS"
   ```

2. Also see whether the commits themselves name any issues:
   ```bash
   git log <target>..HEAD --oneline | grep -oE '#[0-9]+' | sort -u
   ```

3. **Matches turned up:** keep the issue numbers on hand for the PR link.

4. **Nothing matched:** open a fresh issue with this layout:
   ```bash
   gh issue create --title "<type>: <summary from commits>" --body "$(cat <<'EOF'
   ## Problem Statement
   <infer from diff and commit messages>

   ## Proposal
   <summarize the implementation approach>

   ## How It Works
   <describe key changes with bullet points>

   ### Architecture
   ```
   <ASCII diagram of component interactions>
   ```

   ## Challenges
   - <potential edge cases or risks>

   ## Plan & Phases
   - [x] Implementation complete
   - [x] Tests passing
   - [ ] Code review approved
   - [ ] Merged to <target>

   ## Human Review Tasks
   - [ ] Verify business logic correctness
   - [ ] Check for edge cases not covered by tests
   - [ ] Validate UX/API contract changes (if any)
   EOF
   )"
   ```

5. Hold onto those issue numbers — Step 15 (PR creation) needs them.

## Step 3: Merge target branch

Pull the target in first, so the tests run against what the merge actually produces:

```bash
git fetch origin <target> && git merge origin/<target> --no-edit
```

- **Conflicts show up:** settle the trivial ones yourself (lockfiles, version files). Anything thornier — **STOP** and put them on screen.
- **Nothing to merge:** move on without a word.

## Step 4: Run Tests

**Skip when:** `--skip-tests` is set.

1. Figure out the test command (covered in `auto-detect.md`)
2. Pass it to the `tester` subagent — don't run the suite inline
3. Read pass/fail back off the agent's result

- **Anything red:** show the failures and **STOP**. No further steps.
- **All green:** jot the counts and carry on.
- **No runner found:** ask via `AskUserQuestion` — "No test runner detected. Skip tests or provide command?"

## Step 5: Code Quality Gate

Run `/tkm:lint-code` after tests and before inspection.

- **Error-level violations or tool failure:** show `.takumi/reports/sunlint.json` when present and **STOP**.
- **Warnings only:** advisory by default. In `official`, surface them clearly before continuing.
- **Missing SunLint:** stop and print `npm install -g @sun-asterisk/sunlint`.

## Step 6: License Audit

Run `/tkm:audit-licenses`.

- **Violations or policy denies:** show `.takumi/reports/licenseal.json` and **STOP**.
- **Licenseal gaps:** block `official`; surface as review work for `beta`.
- **Reviewable findings:** ask the user to run `/tkm:audit-licenses --review` instead of inventing approvals.
- **Missing licenseal:** stop and print `uv tool install licenseal` or `pipx install licenseal`.

## Step 7: Pre-Landing Review

**Skip when:** `--skip-review` is set.

1. Grab the whole diff with `git diff origin/<target>`
2. Send the diff to the `reviewer` subagent
3. Look at it twice:
   - **Pass 1 (CRITICAL):** the things that bite — injection holes, auth that can be slipped past, races, security gaps
   - **Pass 2 (INFORMATIONAL):** the things that nag — dead code, bare magic numbers, thin test coverage, style drift

4. **Report what came back:**
   ```
   Pre-Landing Review: N issues (X critical, Y informational)
   ```

5. **Critical findings present:** take EACH one to `AskUserQuestion`:
   - The problem, pinned to a `file:line`
   - The fix you'd recommend
   - Choices: A) Fix now (recommended), B) Acknowledge and ship anyway, C) False positive — skip

6. **They picked Fix (A):** apply it, commit the touched files, then loop back and **re-run tests** (Step 4) before going on.
7. **Only informational left:** fold them into the PR body and keep going.
8. **Clean bill:** print "No issues found." and keep going.

## Step 8: Version Bump (conditional)

1. Find where the version lives (covered in `auto-detect.md`)
2. No version file? **skip without comment**
3. Pick the bump from how big the diff is:
   - **Under 50 lines:** patch bump
   - **50 lines or more:** patch bump (the safe default)
   - **A real feature or a breaking change:** ask via `AskUserQuestion` — "This looks like a significant change. Bump minor or patch?"
4. On beta mode, tack on a prerelease suffix (e.g., `1.2.4-beta.1`)
5. Write the new number back into whatever file held it

## Step 9: Changelog (conditional)

1. Look for CHANGELOG.md or CHANGES.md
2. Neither there? **skip without comment**
3. Build the entry from every commit on the branch:
   - `git log <target>..HEAD --oneline` for the commit list
   - `git diff <target>...HEAD` for the full picture
4. Sort the entries under: Added, Changed, Fixed, Removed
5. Drop it in right below the file header, dated today
6. Heading shape: `## [X.Y.Z] - YYYY-MM-DD`

**Don't make the user narrate the changes.** Read them out of the diff and commits.

## Step 10: Journal (background)

**Skip when:** `--skip-journal` is set.

Capture this ship as a technical journal entry. Send it to the **background** so the pipeline isn't held up.

1. Kick off `/tkm:write-journal` through the `journal-writer` subagent, in the background:
   - Topic: a recap of what shipped (drawn from commit messages and diff stats)
   - Cover: what went out, the calls that mattered, the snags you hit
   - Lands in: `./docs/journals/`
2. Don't linger for it — straight on to the next step.

## Step 11: Docs Update (conditional, background)

**Skip when:** `--skip-docs` is set OR the mode is `beta`.

For official releases, bring the project docs current. Run it in the **background**.

1. Kick off `/tkm:manage-docs update` through the `doc-writer` subagent, in the background:
   - Reads the code changes since the last release
   - Refreshes the affected files under `./docs/`
2. Don't linger for it — straight on to the next step.

## Step 12: Evidence Gate

If an active plan has a `{plan}/evidence/` directory, run the hard pre-push gate before committing:

```bash
node claude/skills/_shared/lib/evidence-gate.cjs --evidence-dir "<abs {plan}/evidence>" --stage hard
```

- **Exit 0:** carry on.
- **Exit 2:** surface the reasons and **STOP** before commit/push.
- **No active plan/evidence dir:** skip and note that no evidence gate ran.
- **`--skip-tests` or `--skip-review`:** downgrade the gate to advisory because required artifacts are intentionally absent.

## Step 13: Commit

1. Stage everything: `git add -A`
2. Sweep the staged diff for secrets (API keys, tokens, passwords)
   - Find any? **STOP**, flag it to the user, point them at `.gitignore`
3. Write the commit message:
   - Shape: `type(scope): description`
   - Read the type off the changes (feat/fix/refactor/chore)
   - Roll the version and changelog edits into this same commit when they exist
4. Commit:

```bash
git commit -m "$(cat <<'EOF'
type(scope): description

Brief body describing the changes.
EOF
)"
```

## Step 14: Push

```bash
git push -u origin $(git branch --show-current)
```

- **Force push is off the table.**
- Pushed back? Suggest `git pull --rebase` and give it one more try.

## Step 15: Create PR

Confirm the `gh` CLI is on the machine:
```bash
which gh 2>/dev/null || echo "MISSING"
```

Not there: print "Install GitHub CLI (gh) to auto-create PRs" and finish after the push.

Open the PR against the right branch:
```bash
gh pr create --base <target-branch> --title "<type>: <summary>" --body "$(cat <<'EOF'
<PR body from pr-template.md>
EOF
)"
```

**Wire in the issues** gathered back in Step 2:
```bash
# If issues were found/created, add closing keywords in PR body
# e.g., "Closes #42, Relates to #43"
```

**Print the PR URL** — that link is the last thing the user sees.

If a PR is already open on this branch, edit it rather than opening another:
```bash
gh pr edit --title "<type>: <summary>" --body "$(cat <<'EOF'
<PR body>
EOF
)"
```
