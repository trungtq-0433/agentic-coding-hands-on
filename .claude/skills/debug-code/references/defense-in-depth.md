# Defense-in-Depth Validation

Check the data at every layer it crosses so the bug has nowhere left to live.

## Core Principle

**Validate at EVERY layer the data passes through. Make the bug structurally impossible.**

After fixing a bug born from bad data, one check at one spot feels like enough. It isn't — a different code path, a later refactor, or a mock can slip right past it.

## Why Multiple Layers

One check says: "We fixed the bug."
Layered checks say: "We made the bug impossible."

Each layer catches a different kind of miss:
- Entry validation stops the bulk of them
- Business logic catches the edge cases
- Environment guards block dangers tied to a specific context
- Debug logging earns its keep when the other layers fail

## The Four Layers

### Layer 1: Entry Point Validation
**Purpose:** Turn away plainly invalid input right at the API boundary

```typescript
function createProject(name: string, workingDirectory: string) {
  if (!workingDirectory || workingDirectory.trim() === '') {
    throw new Error('workingDirectory cannot be empty');
  }
  if (!existsSync(workingDirectory)) {
    throw new Error(`workingDirectory does not exist: ${workingDirectory}`);
  }
  if (!statSync(workingDirectory).isDirectory()) {
    throw new Error(`workingDirectory is not a directory: ${workingDirectory}`);
  }
  // proceed
}
```

### Layer 2: Business Logic Validation
**Purpose:** Confirm the data actually makes sense for this operation

```typescript
function initializeWorkspace(projectDir: string, sessionId: string) {
  if (!projectDir) {
    throw new Error('projectDir required for workspace initialization');
  }
  // proceed
}
```

### Layer 3: Environment Guards
**Purpose:** Block dangerous operations in the contexts where they'd do harm

```typescript
async function gitInit(directory: string) {
  // In tests, refuse git init outside temp directories
  if (process.env.NODE_ENV === 'test') {
    const normalized = normalize(resolve(directory));
    const tmpDir = normalize(resolve(tmpdir()));

    if (!normalized.startsWith(tmpDir)) {
      throw new Error(
        `Refusing git init outside temp dir during tests: ${directory}`
      );
    }
  }
  // proceed
}
```

### Layer 4: Debug Instrumentation
**Purpose:** Capture the context you'll want when something still slips through

```typescript
async function gitInit(directory: string) {
  const stack = new Error().stack;
  logger.debug('About to git init', {
    directory,
    cwd: process.cwd(),
    stack,
  });
  // proceed
}
```

## Applying the Pattern

Once you've found the bug:

1. **Trace the data flow** - Where is the bad value born, and where does it get used?
2. **Map every checkpoint** - List each point the data passes through
3. **Add a check at each layer** - Entry, business, environment, debug
4. **Probe each layer** - Try to slip past layer 1 and confirm layer 2 catches what got through

## Example from Real Session

Bug: an empty `projectDir` triggered `git init` inside the source tree

**Data flow:**
1. Test setup → empty string
2. `Project.create(name, '')`
3. `WorkspaceManager.createWorkspace('')`
4. `git init` runs in `process.cwd()`

**Four layers added:**
- Layer 1: `Project.create()` validates not empty/exists/writable
- Layer 2: `WorkspaceManager` validates projectDir not empty
- Layer 3: `WorktreeManager` refuses git init outside tmpdir in tests
- Layer 4: Stack trace logging before git init

**Result:** all 1847 tests green, and the bug could no longer be reproduced

## Key Insight

Every one of the four layers earned its place. Across testing, each caught what the others let slip:
- Different code paths walked past entry validation
- Mocks slid past the business-logic checks
- Platform-specific edge cases needed the environment guards
- Debug logging exposed the structural misuse

**One checkpoint is never enough.** Put a check at every layer.
