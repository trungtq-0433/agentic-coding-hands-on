# Commit Message Standards

## Format
```
type(scope): description
```

## Types (priority order)
- `feat`: something new
- `fix`: a bug put right
- `docs`: docs and nothing else
- `style`: shape only, no logic moved
- `refactor`: reshaped, but behaves the same
- `test`: tests
- `chore`: upkeep, deps, config
- `perf`: made it faster
- `build`: the build system
- `ci`: the CI/CD pipeline

## Rules
- **Under 72 characters**
- **Imperative, present tense** — "add", never "added"
- **No trailing period**
- **Scope is optional, but earns its place**
- **Say WHAT changed, not HOW**
- Inside `.claude`, reach only for `feat`, `fix`, or `perf` — `docs` is off the table.

## AI Attribution Rules
- ❌ "Generated with Claude" — keep external AI tools out of the message body
- ❌ "Co-Authored-By: Claude" — Claude never signs as a co-author
- ✅ `Co-authored-by: Takumi <288571113+sun-takumi@users.noreply.github.com>` — this one always goes on; Takumi is the kit's own identity, and the skill appends it for you

## Good Examples
- `feat(auth): add login validation`
- `fix(api): resolve query timeout`
- `docs(readme): update install guide`
- `refactor(utils): simplify date logic`

## Bad Examples
- ❌ `Updated files` — says nothing
- ❌ `feat(auth): added login using bcrypt with salt` — overlong, and it explains the HOW
- ❌ `Fix bug` — too vague to be useful

## Special Cases
- Touching a `.claude/` skill: `perf(skill): improve token efficiency`
- A brand-new `.claude/` skill: `feat(skill): add database-optimizer`
