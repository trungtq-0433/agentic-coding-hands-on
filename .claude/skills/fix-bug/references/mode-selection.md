# Mode Selection

Open the fixing workflow with `AskUserQuestion`.

## AskUserQuestion Format

```json
{
  "questions": [{
    "question": "How should I handle the fix workflow?",
    "header": "Fix Mode",
    "options": [
      {
        "label": "Autonomous (Recommended)",
        "description": "Auto-approve if quality high, only ask when stuck"
      },
      {
        "label": "Human-in-the-loop",
        "description": "Pause for approval at each major step"
      },
      {
        "label": "Quick fix",
        "description": "Fast debug-fix-review cycle for simple issues"
      }
    ],
    "multiSelect": false
  }]
}
```

## Mode Recommendations

| Issue Type | Recommended Mode |
|------------|------------------|
| Type errors, lint errors | Quick |
| Single-file bugs | Quick or Autonomous |
| Multi-file, root cause unclear | Autonomous |
| Production/critical code | Human-in-the-loop |
| System-wide/architecture | Human-in-the-loop |
| Security holes | Human-in-the-loop |

## Skip Mode Selection When

- The issue is plainly trivial (a type-error keyword shows up) → default to Quick
- The user already named a mode in the prompt
- Earlier context has already pinned the mode
