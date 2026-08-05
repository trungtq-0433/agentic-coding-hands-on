# Takumi (匠)

The master craftsman does not measure success by speed.
Every piece that leaves the workshop has been examined, tested, refined.

Takumi brings this discipline to software:
no feature ships without a blueprint,
no blueprint is cut without review,
no session ends without a record.

## Usage

```bash
/tkm:takumi <task OR plan path>
```

The workshop reads what you bring and selects the appropriate discipline.

## Working Disciplines

| Discipline | Pattern | When to Use |
|------------|---------|-------------|
| interactive | Study → Draft → Forge → Temper → Inspect | Default — full control, full craft |
| auto | All stages, no rest points | Trusted, hands-off sessions |
| fast | Scout → Draft → Forge | Quick fixes and clear tasks |
| parallel | Multi-agent concurrent | 3+ independent features |
| no-test | Skip tempering | Speed-critical situations |
| code | Execute existing blueprint | Blueprint already exists |

## Reading Intent

The workshop reads what you bring to it:
1. **Explicit discipline flags** — `--fast`, `--auto`, `--parallel`, `--no-test`
2. **Blueprint paths** — `./plans/*`, `plan.md`, `phase-*.md`
3. **Keywords** — "fast", "quick", "trust me", "auto", "no test"
4. **Feature count** — 3+ distinct features → parallel discipline

## Examples

```bash
# Interactive (default) — full craft, full control
/tkm:takumi implement user authentication

# Execute an existing blueprint
/tkm:takumi plans/260120-auth

# Fast discipline — scout and forge, skip deep research
/tkm:takumi quick fix for login bug
/tkm:takumi implement feature --fast

# Auto discipline — continuous, no rest points
/tkm:takumi implement dashboard trust me
/tkm:takumi implement feature --auto

# Parallel discipline — many hands, many pieces
/tkm:takumi implement auth, payments, notifications
/tkm:takumi implement feature --parallel

# Skip tempering — forge only
/tkm:takumi implement feature --no-test
```

## The Seven Stages

```
[Read Material] → [Study?] → [Blueprint] → [Forge] → [Temper?] → [Inspect] → [Deliver]
```

0. **Read the Material** — detect discipline and intent
1. **Study the Craft** — research patterns and constraints
2. **Draft the Blueprint** — plan before cutting
3. **Forge the Piece** — implement with precision
4. **Temper the Edge** — test without shortcuts
5. **Master's Inspection** — review with rigor
6. **Deliver the Work** — finalize, document, commit

## Workshop Structure

```
takumi/
├── SKILL.md                            # The craftsman's manual
├── README.md                           # This guide
└── references/
    ├── intent-detection.md             # Material reading rules
    ├── workflow-steps.md               # Detailed stage definitions
    ├── review-cycle.md                 # Inspection protocol
    └── subagent-patterns.md            # Workshop delegation patterns
```

## Version

2.1.1 — Shokunin discipline: every stage intentional
2.1.0 — Rest points added for human-in-the-loop disciplines
2.0.0 — Smart material reading (hybrid detection)
