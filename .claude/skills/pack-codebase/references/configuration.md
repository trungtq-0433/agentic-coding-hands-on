# Configuration Reference

The full set of knobs Repomix exposes.

## Configuration File

Drop a `repomix.config.json` at the project root:

```json
{
  "output": {
    "filePath": "repomix-output.xml",
    "style": "xml",
    "removeComments": false,
    "showLineNumbers": true,
    "copyToClipboard": false
  },
  "include": ["**/*"],
  "ignore": {
    "useGitignore": true,
    "useDefaultPatterns": true,
    "customPatterns": ["additional-folder", "**/*.log", "**/tmp/**"]
  },
  "security": {
    "enableSecurityCheck": true
  }
}
```

### Output Options

- `filePath`: Where the bundle is written (default: `repomix-output.xml`)
- `style`: Output shape — `xml`, `markdown`, `json`, `plain` (default: `xml`)
- `removeComments`: Drop comments (default: `false`). Covers HTML, CSS, JS/TS, Vue, Svelte, Python, PHP, Ruby, C, C#, Java, Go, Rust, Swift, Kotlin, Dart, Shell, YAML
- `showLineNumbers`: Prepend line numbers (default: `true`)
- `copyToClipboard`: Send output straight to the clipboard (default: `false`)

### Include/Ignore

- `include`: Glob patterns naming what to pull in (default: `["**/*"]`)
- `useGitignore`: Obey .gitignore (default: `true`)
- `useDefaultPatterns`: Apply the built-in ignore list (default: `true`)
- `customPatterns`: Extra ignore rules, written the same way as .gitignore

### Security

- `enableSecurityCheck`: Run Secretlint over the bundle for sensitive data (default: `true`)
- Catches: API keys, passwords, credentials, private keys, AWS secrets, DB connections

## Glob Patterns

**Wildcards:**
- `*` - Any chars except `/`
- `**` - Any chars including `/`
- `?` - Single char
- `[abc]` - Char from set
- `{js,ts}` - Either extension

**Examples:**
- `**/*.ts` - All TypeScript
- `src/**` - Specific dir
- `**/*.{js,jsx,ts,tsx}` - Multiple extensions
- `!**/*.test.ts` - Exclude tests

### CLI Options

```bash
# Include patterns
repomix --include "src/**/*.ts,*.md"

# Ignore patterns
repomix -i "tests/**,*.test.js"

# Disable .gitignore
repomix --no-gitignore

# Disable defaults
repomix --no-default-patterns
```

### .repomixignore File

When the rules are specific to Repomix rather than Git, put them in a `.repomixignore` (same syntax as .gitignore):

```
# Build artifacts
dist/
build/
*.min.js
out/

# Test files
**/*.test.ts
**/*.spec.ts
coverage/
__tests__/

# Dependencies
node_modules/
vendor/
packages/*/node_modules/

# Large files
*.mp4
*.zip
*.tar.gz
*.iso

# Sensitive files
.env*
secrets/
*.key
*.pem

# IDE files
.vscode/
.idea/
*.swp

# Logs
logs/
**/*.log
```

### Pattern Precedence

When two rules disagree, the higher one wins:
1. CLI ignore patterns (`-i`)
2. `.repomixignore` file
3. Custom patterns in config
4. `.gitignore` (if enabled)
5. Default patterns (if enabled)

### Pattern Examples

**TypeScript:**
```json
{"include": ["**/*.ts", "**/*.tsx"], "ignore": {"customPatterns": ["**/*.test.ts", "dist/"]}}
```

**React:**
```json
{"include": ["src/**/*.{js,jsx,ts,tsx}", "*.md"], "ignore": {"customPatterns": ["build/"]}}
```

**Monorepo:**
```json
{"include": ["packages/*/src/**"], "ignore": {"customPatterns": ["packages/*/dist/"]}}
```

## Output Formats

### XML (Default)
```bash
repomix --style xml
```
Built for a model to chew on. Carries tags, hierarchy, metadata, and separators tuned for AI.
Reach for it when: feeding LLMs, doing structured analysis, parsing programmatically.

### Markdown
```bash
repomix --style markdown
```
Readable by people, with syntax highlighting. Carries highlighting, headers, a TOC.
Reach for it when: writing docs, reviewing code, sharing with a teammate.

### JSON
```bash
repomix --style json
```
For pipelines that consume the output. Carries structured data, parses cleanly, keeps metadata.
Reach for it when: wiring into an API, building custom tooling, crunching data.

### Plain Text
```bash
repomix --style plain
```
Files concatenated, nothing more. No formatting, almost no overhead.
Reach for it when: the analysis is simple and you want the least processing possible.

## Advanced Options

```bash
# Verbose - show processing details
repomix --verbose

# Custom config file
repomix -c /path/to/custom-config.json

# Initialize config
repomix --init

# Disable line numbers - smaller output
repomix --no-line-numbers
```

### Performance

**Worker Threads:** Work is split across threads, so big trees pack fast (facebook/react, for instance: 29x faster, 123s → 4s)

**Optimization:**
```bash
# Exclude unnecessary files
repomix -i "node_modules/**,dist/**,*.min.js"

# Specific directories only
repomix --include "src/**/*.ts"

# Remove comments, disable line numbers
repomix --remove-comments --no-line-numbers
```
