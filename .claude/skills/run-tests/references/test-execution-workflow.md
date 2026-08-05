# Test Execution Workflow

## Step 1: Identify Scope

Read the diff first — what changed dictates what to run:
- Shipped a new feature → run everything, and add fresh cases to cover it
- Patched a bug → lean on the regression suite, then prove the fix at the spot it broke
- Refactored only → re-run the suite you already have; write new tests only where it exposes a hole
- Just checking coverage → whole suite, coverage flags on

## Step 2: Pre-flight Checks

Send the syntax/type checks ahead of the tests so a compile error surfaces early:

```bash
# JavaScript/TypeScript
npx tsc --noEmit          # TypeScript check
npx eslint .              # Lint check

# Python
python -m py_compile file.py
flake8 .

# Flutter
flutter analyze

# Go
go vet ./...

# Rust
cargo check
```

After syntax and type checks, run `/tkm:lint-code` for the SunLint quality preflight. It uses changed-aware scanning by default and writes `.takumi/reports/sunlint.json`.

Do not run `/tkm:audit-licenses` during ordinary test runs; license compliance belongs to shipping, security audits, or an explicit license audit.

## Step 3: Execute Tests

### JavaScript/TypeScript
```bash
npm test                    # or yarn test / pnpm test / bun test
npm run test:coverage       # with coverage
npx vitest run              # Vitest
npx jest --coverage         # Jest with coverage
```

### Python
```bash
pytest                      # basic
pytest --cov=src --cov-report=term-missing  # with coverage
python -m unittest discover # unittest
```

### Go / Rust / Flutter
```bash
go test ./... -cover        # Go with coverage
cargo test                  # Rust
flutter test --coverage     # Flutter
```

## Step 4: Analyze Results

Where to look:
1. **Failing tests** — sit with the error message and the stack trace, don't skim them
2. **Flaky tests** — a test that flips between pass and fail is pointing at a race or leaked state
3. **Slow tests** — hunt the bottleneck (anything over 5s per test earns a second look)
4. **Skipped tests** — make sure a skip is a choice, not a failure tucked out of sight

## Step 5: Coverage Analysis

Thresholds:
- **80%+** line coverage — the floor to clear
- **70%+** branch coverage — good enough on most projects
- Spend the attention where it counts: auth, payment, data mutations

Where the holes hide:
- Error handlers no test ever entered
- Edge-case branches left untaken
- Utility functions nobody exercised

## Step 6: Build Verification

```bash
npm run build               # JS/TS production build
python setup.py build       # Python
go build ./...              # Go
cargo build --release       # Rust
flutter build               # Flutter
```

Watch for:
- Warnings or deprecation notices the build coughs up
- Dependencies that never resolved
- Production config that doesn't line up

## Quality Checklist

- [ ] Every test green (zero failures)
- [ ] Coverage at or above the project threshold
- [ ] Nothing flaky in the run
- [ ] Build finishes clean
- [ ] Failure scenarios exercised
- [ ] Isolation confirmed — no shared state between tests
- [ ] Test data swept up once the run ends
- [ ] Mocks/stubs wired correctly
- [ ] Environment variables set right
