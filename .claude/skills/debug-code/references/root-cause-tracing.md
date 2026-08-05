# Root Cause Tracing

Follow a bug back up the call stack, step by step, until you reach the thing that first set it off.

## Core Principle

**Walk backward through the call chain to the original trigger, then repair it there.**

A bug usually shows itself deep in the stack (a git init in the wrong directory, a file written where it shouldn't be). The reflex is to patch where the error surfaced — but that's chasing the symptom.

## When to Use

**Reach for this when:**
- The error fires deep in execution, not at the entry point
- The stack trace runs through a long call chain
- You can't tell where the invalid data came from
- You need to pin down which test or code path sets the problem off

## The Tracing Process

### 1. Observe the Symptom
```
Error: git init failed in /Users/jesse/project/packages/core
```

### 2. Find Immediate Cause
Which line directly produces this?
```typescript
await execFileAsync('git', ['init'], { cwd: projectDir });
```

### 3. Ask: Who Called It?
```typescript
WorktreeManager.createSessionWorktree(projectDir, sessionId)
  → called by Session.initializeWorkspace()
  → called by Session.create()
  → called by test at Project.create()
```

### 4. Keep Tracing Up
What value got handed in?
- `projectDir = ''` (an empty string!)
- An empty string for `cwd` falls through to `process.cwd()`
- And that's the source code directory!

### 5. Find Original Trigger
Where did that empty string come from?
```typescript
const context = setupCoreTest(); // Returns { tempDir: '' }
Project.create('name', context.tempDir); // Accessed before beforeEach!
```

## Adding Stack Traces

When tracing by hand stalls, instrument the code:

```typescript
async function gitInit(directory: string) {
  const stack = new Error().stack;
  console.error('DEBUG git init:', {
    directory,
    cwd: process.cwd(),
    stack,
  });

  await execFileAsync('git', ['init'], { cwd: directory });
}
```

**Critical:** Reach for `console.error()` in tests — the logger may stay silent

**Run and capture:**
```bash
npm test 2>&1 | grep 'DEBUG git init'
```

**Read the stack traces:**
- Scan for test file names
- Find the line number that fires the call
- Spot the pattern (same test? same argument?)

## Finding Which Test Causes Pollution

When something shows up during a test run but you can't say which test left it behind:

Lean on the bisection script: `scripts/find-polluter.sh`

```bash
./scripts/find-polluter.sh '.git' 'src/**/*.test.ts'
```

It runs the tests one at a time and halts at the first offender.

## Key Principle

**NEVER settle for a fix where the error surfaced.** Trace back to the trigger that started it.

Once you have the immediate cause:
- One level further up to go? → Keep tracing backward
- Is this the source? → Fix it here
- Then layer in validation at every checkpoint (see defense-in-depth.md)

## Real Example

**Symptom:** `.git` created in `packages/core/` (source code)

**Trace chain:**
1. `git init` runs in `process.cwd()` ← empty cwd parameter
2. WorktreeManager called with empty projectDir
3. Session.create() passed empty string
4. Test accessed `context.tempDir` before beforeEach
5. setupCoreTest() returns `{ tempDir: '' }` initially

**Root cause:** A top-level variable read its value before that value existed

**Fix:** Turned tempDir into a getter that throws when touched before beforeEach

**Defense-in-depth added on top:**
- Layer 1: Project.create() validates the directory
- Layer 2: WorkspaceManager rejects an empty value
- Layer 3: NODE_ENV guard refuses git init outside tmpdir
- Layer 4: Stack trace logging just before git init
