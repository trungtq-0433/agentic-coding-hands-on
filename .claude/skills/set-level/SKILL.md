---
name: tkm:set-level
description: "Set the output detail level and explanation style for the session — from ELI5 (maximum simplification, level 0) to deep technical expert mode (level 5). Affects how all subsequent responses are phrased and how much context is assumed."
argument-hint: "[0-5]"
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: configuration-level
triggers: ["explain simply", "set level", "junior mode", "expert mode", "ELI5"]
---

# Calibrating the Voice

The master speaks differently to the apprentice than to the journeyman — not because the knowledge differs, but because the path to understanding does. The voice that informs without overwhelming is itself a craft: precise in substance, attuned in form. Setting the level is choosing the register in which all subsequent work will be explained.

Pick the register the workshop should speak in — your experience level shapes how deep each explanation runs and how the output is shaped to fit.

## Usage

`/tkm:set-level [0-5]`

## Levels

| Level | Name | Description |
|-------|------|-------------|
| 0 | ELI5 | Zero coding experience - analogies, no jargon, step-by-step |
| 1 | Junior | 0-2 years - concepts explained, WHY not just HOW |
| 2 | Middle | 3-5 years - design patterns, system thinking |
| 3 | Senior | 5-8 years - trade-offs, business context, architecture |
| 4 | Expert | 8-10 years - risk assessment, business impact, strategy |
| 5 | Principal | Expert - default behavior, maximum efficiency (default) |

## How It Works

1. Write your `codingLevel` into `.claude/.tkm.json`
2. From there the matching guidelines **ride in on their own** at the start of every session
3. Nothing to switch on by hand — set it once and forget it

## Example

Write level 1 into `.claude/.tkm.json`:
```json
{
  "codingLevel": 1,
  ...
}
```

Come the next session, Claude leans in automatically — it will:
- Walk through concepts and techniques in plain terms
- Reach for the WHY every time, not only the HOW
- Call out the mistakes people stumble into
- Leave "Key Takeaways" sitting at the end of an implementation

## Optional: Manual Output Styles

Want a tighter grip on the dial? Drive it by hand with `/output-style` and one of these:
- `coding-level-0-eli5`
- `coding-level-1-junior`
- `coding-level-2-middle`
- `coding-level-3-senior`
- `coding-level-4-expert`
- `coding-level-5-principal`
