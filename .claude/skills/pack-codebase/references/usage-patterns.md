# Usage Patterns

Recipes for putting Repomix to work across the situations you'll actually hit.

## AI Analysis Workflows

### Full Repository
```bash
repomix --remove-comments --style markdown -o full-repo.md
```
**Use:** Onboarding to an unfamiliar repo, reviewing the architecture, handing a model the whole picture, planning
**Tips:** Drop comments, lean on markdown, watch the token ceiling, read it over before you share

### Focused Module
```bash
repomix --include "src/auth/**,src/api/**" -o modules.xml
```
**Use:** Studying one feature, debugging a corner of the tree, refactoring a known area
**Tips:** Pull in only the files that relate, hold under the token ceiling, pick XML for the model

### Incremental Analysis
```bash
git checkout feature-branch && repomix --include "src/**" -o feature.xml
git checkout main && repomix --include "src/**" -o main.xml
```
**Use:** Reviewing a feature branch, gauging the blast radius of a change, before/after diffs, migration planning

### Cross-Repository
```bash
npx repomix --remote org/repo1 -o repo1.xml
npx repomix --remote org/repo2 -o repo2.xml
```
**Use:** Spanning microservices, weighing one library against another, checking consistency, reasoning about integration

## Security Audit

### Third-Party Library
```bash
npx repomix --remote vendor/library --style xml -o audit.xml
```
**Workflow:** Pack the library → leave security checks on → read the flagged spots → hunt for suspicious patterns → hand to a model
**Check for:** Leaked API keys, credentials baked into source, outbound network calls, obfuscated code, anything that smells malicious

### Pre-Deployment
```bash
repomix --include "src/**,config/**" --style xml -o pre-deploy-audit.xml
```
**Checklist:** Nothing sensitive in the bundle, no test credentials left behind, env vars set right, sound security practices, no stray debug code

### Dependency Audit
```bash
repomix --include "**/package.json,**/package-lock.json" -o deps.md --style markdown
repomix --include "node_modules/suspicious-package/**" -o dep-audit.xml
```
**Use:** Vetting a suspicious dependency, chasing a security advisory, checking license compliance, assessing vulnerabilities

### Compliance
```bash
repomix --include "src/**,LICENSE,README.md,docs/**" --style markdown -o compliance.md
```
**Include:** The source, license files, docs, configs. **Exclude:** Test fixtures and dependencies

## Documentation

### Doc Context
```bash
repomix --include "src/**,docs/**,*.md" --style markdown -o doc-context.md
```
**Use:** Drafting API docs, architecture writeups, user guides, onboarding material
**Tips:** Fold in the docs you already have, bring the source along, reach for markdown

### API Documentation
```bash
repomix --include "src/api/**,src/routes/**,src/controllers/**" --remove-comments -o api-context.xml
```
**Include:** The routes, controllers, schemas, and middleware
**Workflow:** Pack → feed to a model → OpenAPI/Swagger → endpoint docs → worked examples

### Architecture
```bash
repomix --include "src/**/*.ts,*.md" -i "**/*.test.ts" --style markdown -o architecture.md
```
**Focus:** How the modules are laid out, what depends on what, the design patterns in play, the data flow

### Examples
```bash
repomix --include "examples/**,demos/**,*.example.js" --style markdown -o examples.md
```

## Library Evaluation

### Quick Assessment
```bash
npx repomix --remote owner/library --style markdown -o library-eval.md
```
**Evaluate:** How clean the code is, the architecture, its dependencies, the test coverage, the docs, how actively it's maintained

### Feature Comparison
```bash
npx repomix --remote owner/lib-a --style xml -o lib-a.xml
npx repomix --remote owner/lib-b --style xml -o lib-b.xml
```
**Compare:** Their feature sets, API design, performance, bundle size, dependency weight, and maintenance health

### Integration Feasibility
```bash
npx repomix --remote vendor/library --include "src/**,*.md" -o library.xml
repomix --include "src/integrations/**" -o our-integrations.xml
```
Weigh how well the target library lines up with the seams you'd plug it into

### Migration Planning
```bash
repomix --include "node_modules/old-lib/**" -o old-lib.xml
npx repomix --remote owner/new-lib -o new-lib.xml
```
Set the library you have beside the one you want, and trace how it's used

## Workflow Integration

### CI/CD
```yaml
# GitHub Actions
- name: Generate Snapshot
  run: |
    npm install -g repomix
    repomix --style markdown -o release-snapshot.md
- name: Upload Artifact
  uses: actions/upload-artifact@v3
  with: {name: repo-snapshot, path: release-snapshot.md}
```
**Use:** Release documentation, compliance archives, tracking what changed, leaving an audit trail

### Git Hooks
```bash
#!/bin/bash
# .git/hooks/pre-commit
git diff --cached --name-only > staged-files.txt
repomix --include "$(cat staged-files.txt | tr '\n' ',')" -o .context/latest.xml
```

### IDE (VS Code)
```json
{"version": "2.0.0", "tasks": [{"label": "Package for AI", "type": "shell", "command": "repomix --include 'src/**' --remove-comments --copy"}]}
```

### Claude Code
```bash
repomix --style markdown --copy  # Then paste into Claude
```

## Language-Specific Patterns

### TypeScript
```bash
repomix --include "**/*.ts,**/*.tsx" --remove-comments --no-line-numbers
```
**Exclude:** `**/*.test.ts`, `dist/`, `coverage/`

### React
```bash
repomix --include "src/**/*.{js,jsx,ts,tsx},public/**" -i "build/,*.test.*"
```
**Include:** The components, hooks, utilities, and public assets

### Node.js Backend
```bash
repomix --include "src/**/*.js,config/**" -i "node_modules/,logs/,tmp/"
```
**Focus:** The routes, controllers, models, middleware, and config

### Python
```bash
repomix --include "**/*.py,requirements.txt,*.md" -i "**/__pycache__/,venv/"
```
**Exclude:** `__pycache__/`, `*.pyc`, `venv/`, `.pytest_cache/`

### Monorepo
```bash
repomix --include "packages/*/src/**" -i "packages/*/node_modules/,packages/*/dist/"
```
**Consider:** Patterns that vary per package, shared dependencies, references that cross packages, the workspace layout

## Troubleshooting

### Output Too Large
**Problem:** Blows past the model's token ceiling
**Fix:**
```bash
repomix -i "node_modules/**,dist/**,coverage/**" --include "src/core/**" --remove-comments --no-line-numbers
```

### Missing Files
**Problem:** Files you expected never showed up
**Debug:**
```bash
cat .gitignore .repomixignore  # Check ignore patterns
repomix --no-gitignore --no-default-patterns --verbose
```

### Sensitive Data Warnings
**Problem:** The scanner caught something that looks like a secret
**Actions:** Read the flagged files → add them to `.repomixignore` → strip the sensitive data → move it to env vars
```bash
repomix --no-security-check  # Use carefully for false positives
```

### Performance Issues
**Problem:** Crawls on a big repo
**Optimize:**
```bash
repomix --include "src/**/*.ts" -i "node_modules/**,dist/**,vendor/**"
```

### Remote Access
**Problem:** Can't reach the remote repo
**Fix:**
```bash
npx repomix --remote https://github.com/owner/repo  # Full URL
npx repomix --remote https://github.com/owner/repo/commit/abc123  # Specific commit
# For private: clone first, run locally
```

## Best Practices

**Planning:** Set the scope → name the files → check token limits → think about security

**Execution:** Open wide, then narrow → pick the format that fits → keep security checks on → watch the token count

**Review:** Confirm nothing sensitive leaked → check it's complete → validate the format → try it against a model

**Iteration:** Sharpen the patterns → adjust the format → trim tokens → write down what worked
