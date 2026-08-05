---
description: Initialize a new Takumi Agent Kit project (or update existing)
argument-hint: [target-dir, default current]
---

Delegate to `sk init` CLI for project initialization.

<target>${ARGUMENTS:-.}</target>

Steps the CLI performs:
1. Ensure target directory exists
2. Download latest kit from GitHub release asset
3. Merge into target .claude/ (preserving user files like .env, settings.local.json)
4. Report protected files skipped
5. Offer to run skill dependency installer
