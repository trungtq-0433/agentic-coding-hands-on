# Coordinating Survey Agents with Tasks

When several survey agents run side by side, the Claude Native Tasks trio — TaskCreate, TaskUpdate, TaskList — is what gives you a window into the lineup.

## When to Create Tasks

The choice comes down to how many agents are in flight. A pair finishes before bookkeeping earns its keep; a crowd is where tracking starts paying for itself.

| Agents | Create Tasks? | Rationale |
|--------|--------------|-----------|
| ≤ 2    | No           | Done before the bookkeeping pays off |
| ≥ 3    | Yes          | Enough parts in motion to warrant a watch |

## Task Registration Flow

```
TaskList()                          // Check for existing scout tasks
  → Found tasks?  → Skip creation, reuse existing
  → Empty?        → TaskCreate per agent (see schema below)
```

## Metadata Schema

```
TaskCreate(
  subject: "Scout {directory} for {target}",
  activeForm: "Scouting {directory}",
  description: "Search {directories} for {patterns}",
  metadata: {
    agentType: "Explore",        // "Explore" (internal) or "Bash" (external)
    scope: "src/auth/,src/middleware/",
    scale: 6,
    agentIndex: 1,               // 1-indexed position
    totalAgents: 6,
    toolMode: "internal",        // "internal" or "external"
    priority: "P2",              // Always P2 for scout coordination
    effort: "3m"                 // Fixed timeout per agent
  }
)
```

### Required Fields

- `agentType` — Flavor of subagent driving this slot: `"Explore"` on the internal path, `"Bash"` on the external one
- `scope` — This agent's patch of the tree, directories separated by commas
- `scale` — Carry over the SCALE number you settled on in Step 1
- `agentIndex` / `totalAgents` — Its seat in the row — the 3rd of 6, and so on
- `toolMode` — `"internal"` or `"external"`
- `priority` — Hold it at `"P2"`; a survey assists the real work, it isn't the real work
- `effort` — Stays `"3m"`, the per-agent ceiling

### Optional Fields

- `searchPatterns` — Whatever patterns this agent went after — worth keeping when a trace goes sideways
- `externalTool` — Only on the external path: `"gemini"` or `"opencode"`

## Task Lifecycle

```
Step 3: TaskCreate per agent     → status: pending
Step 4: Before spawning agent    → TaskUpdate → status: in_progress
Step 5: Agent returns report     → TaskUpdate → status: completed
Step 5: Agent times out (3m)     → Keep in_progress, add error metadata
```

### Timeout Handling

```
TaskUpdate(taskId, {
  metadata: { ...existing, error: "timeout" }
})
// Task stays in_progress — distinguishes timeout from incomplete
// Log in final report's "Unresolved Questions" section
```

## Examples

### Internal Scouting (SCALE=6)

```
// Step 3: Register 6 tasks
TaskCreate(subject: "Scout src/auth/ for auth files",
  activeForm: "Scouting src/auth/",
  metadata: { agentType: "Explore", scope: "src/auth/", scale: 6,
              agentIndex: 1, totalAgents: 6, toolMode: "internal",
              priority: "P2", effort: "3m" })  // → taskId1

// Repeat for agents 2-6 with different scopes

// Step 4: Spawn agents
TaskUpdate(taskId1, { status: "in_progress" })
// ... spawn all Explore subagents in single Task tool call

// Step 5: Collect
TaskUpdate(taskId1, { status: "completed" })  // report received
TaskUpdate(taskId3, { metadata: { error: "timeout" } })  // timed out
```

### External Scouting (SCALE=3, gemini)

```
TaskCreate(subject: "Scout db/ for migrations via gemini",
  activeForm: "Scouting db/ via gemini",
  metadata: { agentType: "Bash", scope: "db/,migrations/", scale: 3,
              agentIndex: 1, totalAgents: 3, toolMode: "external",
              externalTool: "gemini", priority: "P2", effort: "3m" })
```

## Integration with Takumi/Planning

Survey tasks live in their own bucket — they are **not** hung beneath the takumi/planning phase tasks as children.

**Why:** the two move to different rhythms. A survey is already finished by the time takumi advances, so braiding the two together only clutters what you read back from the TaskList.

**How it plays out when takumi sets off a survey:**
1. Takumi Step 2 → hands off to the planner → planner sets off the survey
2. The survey registers its own slate of tasks (Step 3), then drives them through (Step 4-5)
3. One consolidated report goes back → the planner resumes its thread
4. Takumi Step 3 fills in the phase tasks — held separate from the survey's

## Quality Check Output

Once registered: `✓ Registered [N] scout tasks ([internal|external] mode, SCALE={scale})`

## Error Handling

If `TaskCreate` trips: note the warning and press on untracked. Nothing downstream breaks — the tasks hand you a view into the run, not the run itself.
