# MoMorph Awareness Rules

## Detecting MoMorph

Recognize MoMorph from **any** of these sources:

- **User message**: URL `https://momorph.ai/files/{fileKey}/screens/{screenId}`, explicit `screenId`/`fileKey` values, or keyword "momorph" / "figma"
- **Active plan**: `plan.md` or any phase file references MoMorph URL, fileKey, or screenId
- **Task prompt**: the spawned task description contains MoMorph references

## Delegation Protocol

**When spawning ANY sub-agent for a MoMorph task, task description, phase plan, MUST append this block to the prompt:**

```
## MoMorph refs:
- {screen name}: https://momorph.ai/files/{fileKey}/screens/{screenId}
- Clarifications: {path to clarifications.md}
```
