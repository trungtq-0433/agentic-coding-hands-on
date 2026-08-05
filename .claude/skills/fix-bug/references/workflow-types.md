# Type Error Fix Workflow

The fast lane for TypeScript and type errors.

## Commands
```bash
bun run typecheck
tsc --noEmit
npx tsc --noEmit
```

## Rules
- Clear EVERY type error — never stop at the first
- **NEVER reach for `any` just to silence the compiler** — track down the real type
- Keep going until the count hits zero

## Common Fixes
- Missing type imports
- Wrong property access
- Null/undefined handling
- Generic type parameters
- Narrowing a union type

## Workflow
1. Run the typecheck command
2. Resolve errors one at a time
3. Run typecheck again
4. Repeat until the output is clean

## Tips
- Bundle errors that share a root cause and fix them together
- Look in `@types/*` packages for the library's own types
- Prefer `unknown` plus type guards over `any`
