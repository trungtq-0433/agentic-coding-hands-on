# Reading the Project's Setup

Let the files on disk tell you the test runner, the version source, and the changelog style.

## Test Runner Detection

Walk the list top to bottom — the first thing that matches wins:

| Check | Test Command |
|-------|-------------|
| `package.json` → `scripts.test` exists | `npm test` |
| `Makefile` → has `test:` target | `make test` |
| `pytest.ini` OR `pyproject.toml` has `[tool.pytest]` | `pytest` |
| `Cargo.toml` exists | `cargo test` |
| `go.mod` exists | `go test ./...` |
| `Gemfile` + `Rakefile` with test task | `bundle exec rake test` |
| `build.gradle` or `build.gradle.kts` | `./gradlew test` |
| `pom.xml` | `mvn test` |
| `mix.exs` | `mix test` |
| `deno.json` | `deno test` |

**Detection script:**
```bash
if [ -f package.json ] && grep -q '"test"' package.json 2>/dev/null; then
  echo "npm test"
elif [ -f Makefile ] && grep -q '^test:' Makefile 2>/dev/null; then
  echo "make test"
elif [ -f pytest.ini ] || ([ -f pyproject.toml ] && grep -q '\[tool.pytest' pyproject.toml 2>/dev/null); then
  echo "pytest"
elif [ -f Cargo.toml ]; then
  echo "cargo test"
elif [ -f go.mod ]; then
  echo "go test ./..."
else
  echo "NONE"
fi
```

**Came up empty:** ask via `AskUserQuestion` — "No test runner detected. Options: A) Skip tests, B) Provide test command"

## Version File Detection

Same drill, top to bottom:

| Check | Read Pattern |
|-------|-------------|
| `VERSION` file | Read as semver string |
| `package.json` → `version` field | `jq -r .version package.json` |
| `pyproject.toml` → `version` | grep `version = "..."` |
| `Cargo.toml` → `version` | grep `version = "..."` |
| `mix.exs` → `@version` | grep `@version "..."` |

**Nothing matched:** skip the version bump quietly — plenty of projects don't version at all.

**How to size the bump:**
```
Lines changed < 50  → patch (X.Y.Z → X.Y.Z+1)
Lines changed >= 50 → patch (safe default)
User explicitly says "breaking" or "major feature" → AskUserQuestion for minor/major
```

## Changelog Detection

| Check | Format |
|-------|--------|
| `CHANGELOG.md` | Keep-a-changelog format |
| `CHANGES.md` | Same |
| `HISTORY.md` | Same |

**Nothing matched:** skip the changelog quietly.

**What an entry looks like:**
```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- Whatever the `feat:` commits introduced

### Changed
- Whatever the `refactor:` and `perf:` commits reshaped

### Fixed
- Whatever the `fix:` commits put right

### Removed
- Anything the commit messages say was taken out
```

**Where the categories come from:**
1. The conventional-commit prefixes in `git log main..HEAD --oneline`
2. The kinds of files touched (tests → test improvements, docs → documentation)
3. The diff itself (a new function reads as Added, a changed one as Changed)

## Main Branch Detection

```bash
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'
```

If that comes up dry, fall back to testing for `main`, then `master`:
```bash
git rev-parse --verify origin/main 2>/dev/null && echo "main" || echo "master"
```
