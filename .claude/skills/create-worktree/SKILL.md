---
name: tkm:create-worktree
description: "Open a parallel workbench without disturbing the main branch — create isolated git worktrees for feature and fix development in monorepos."
argument-hint: "[feature-description] OR [project] [feature]"
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: git-version-control
triggers: ["worktree", "isolated branch", "work in parallel", "don't touch main branch", "separate workspace"]
---

# The Separate Bench

Some jobs cannot share one surface — start them side by side and they get in each other's way. So the craftsman sets up a second bench.
A worktree is that second bench. Same workshop, same tools, but its own space — so one piece of work can move forward without jostling the other.

## Workflow

### Step 1: Get Repo Info

```bash
node .claude/skills/create-worktree/scripts/worktree.cjs info --json
```

Parse JSON response for: `repoType`, `baseBranch`, `projects`, `worktreeRoot`, `worktreeRootSource`.

### Step 2: Detect Branch Naming Mode

**Look for an explicit branch name before anything else.**
Sometimes the caller already hands you a finished branch name — you can tell because it carries uppercase letters, an issue-tracker key such as `ABC-1234`, slashes for a multi-segment convention like `user/type/feature`, or a plain instruction to "use this exact branch name". When that happens:
→ Use `--no-prefix` flag — skip Step 3, pass name directly as slug.
Examples:
- `"ND-1377-cleanup-docs"` → `--no-prefix` → branch `ND-1377-cleanup-docs`
- `"kai/feat/604-startup-option"` → `--no-prefix` → branch `kai/feat/604-startup-option`

**No explicit name? Then read the prefix off the description:**
- "fix", "bug", "error", "issue" → `fix`
- "refactor", "restructure", "rewrite" → `refactor`
- "docs", "documentation", "readme" → `docs`
- "test", "spec", "coverage" → `test`
- "chore", "cleanup", "deps" → `chore`
- "perf", "performance", "optimize" → `perf`
- Default → `feat`

### Step 3: Convert to Slug

**Skip if `--no-prefix` was chosen in Step 2.**

Boil the description down to a short kebab-case handle:
"add authentication system" → `add-auth`
"fix login bug" → `login-bug`
Max 50 chars, kebab-case.

### Step 4: Handle Monorepo

A monorepo with no project named yet means you don't know where to put the bench — ask. When `repoType === "monorepo"` and project not specified, use AskUserQuestion:
```javascript
AskUserQuestion({
  questions: [{
    header: "Project",
    question: "Which project for the worktree?",
    options: projects.map(p => ({ label: p.name, description: p.path })),
    multiSelect: false
  }]
})
```

### Step 5: Execute

**Monorepo:**
```bash
node .claude/skills/create-worktree/scripts/worktree.cjs create "<PROJECT>" "<SLUG>" --prefix <TYPE>
```

**Standalone:**
```bash
node .claude/skills/create-worktree/scripts/worktree.cjs create "<SLUG>" --prefix <TYPE>
```

**Options:**
- `--prefix` - Branch type: feat|fix|refactor|docs|test|chore|perf
- `--no-prefix` - Skip branch prefix and preserve original case and slashes (for Jira keys, multi-segment branches like `user/type/feature`)
- `--worktree-root <path>` - Override default location (only if needed)
- `--json` - JSON output
- `--dry-run` - Preview

### Step 6: Install Dependencies

The new bench starts empty — give it its dependencies. Read the lockfile present and run the matching install in the background:
- `bun.lock` → `bun install`
- `pnpm-lock.yaml` → `pnpm install`
- `yarn.lock` → `yarn install`
- `package-lock.json` → `npm install`
- `poetry.lock` → `poetry install`
- `requirements.txt` → `pip install -r requirements.txt`
- `Cargo.toml` → `cargo build`
- `go.mod` → `go mod download`

## Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `create` | `create [project] <feature>` | Create worktree |
| `remove` | `remove <name-or-path>` | Remove worktree |
| `info` | `info` | Repo info with worktree location |
| `list` | `list` | List worktrees |

## Notes

- The script sorts out superproject, monorepo, and standalone layouts on its own
- It also picks a sensible spot for the worktree: superproject first, then monorepo, then a sibling directory
- Reach for `--worktree-root` only when you need to override that default
- Any `.env*.example` templates ride along automatically, with the `.example` suffix stripped off
