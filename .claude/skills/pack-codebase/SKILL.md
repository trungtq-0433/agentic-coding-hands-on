---
name: tkm:pack-codebase
description: Fold a whole repository into one Repomix file an LLM can read (XML, Markdown, or plain text). Reach for it when you need a codebase snapshot, want to hand a model full context, are prepping a security audit, or studying someone else's library.
argument-hint: "[path] [--style xml|markdown|plain|json]"
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: specialized-output
triggers: ["pack codebase", "repomix", "LLM context", "codebase snapshot"]
---

# Bundling the Work

Handing a codebase to a reader who wasn't there when it was written is its own small craft. Pack too little and the structure falls apart in transit; pack too much and the signal drowns. The aim is a single artifact that carries exactly what the recipient needs to follow the work — and Repomix is the tool that flattens an entire tree into that one readable file.

Repomix collapses a whole repository into a single file shaped for machines to read. It is what you want when the recipient is Claude, ChatGPT, Gemini, or any other model that needs the codebase in one piece.

## When to Use

Reach for it when you are:
- Handing a codebase to a model for analysis
- Freezing a repository into a snapshot for LLM context
- Reading through a third-party library
- Setting up a security audit
- Assembling context for documentation work
- Chasing a bug that spans a large tree
- Producing a code representation a model can digest

## Quick Start

### Check Installation
```bash
repomix --version
```

### Install
```bash
# npm
npm install -g repomix

# Homebrew (macOS/Linux)
brew install repomix
```

### Basic Usage
```bash
# Package current directory (generates repomix-output.xml)
repomix

# Specify output format
repomix --style markdown
repomix --style json

# Package remote repository
npx repomix --remote owner/repo

# Custom output with filters
repomix --include "src/**/*.ts" --remove-comments -o output.md
```

## Core Capabilities

### Repository Packaging
- Formatting tuned for models, with unambiguous separators
- Four output shapes: XML, Markdown, JSON, plain text
- Honors Git rules out of the box (reads .gitignore)
- Counts tokens so you can stay inside a context window
- Scans for secrets before you ship the bundle

### Remote Repository Support
Pull and pack a remote repository without ever cloning it yourself:
```bash
# Shorthand
npx repomix --remote yamadashy/repomix

# Full URL
npx repomix --remote https://github.com/owner/repo

# Specific commit
npx repomix --remote https://github.com/owner/repo/commit/hash
```

### Comment Removal
Strip comments out of the languages Repomix understands (HTML, CSS, JavaScript, TypeScript, Vue, Svelte, Python, PHP, Ruby, C, C#, Java, Go, Rust, Swift, Kotlin, Dart, Shell, YAML):
```bash
repomix --remove-comments
```

## Common Use Cases

### Code Review Preparation
```bash
# Package feature branch for AI review
repomix --include "src/**/*.ts" --remove-comments -o review.md --style markdown
```

### Security Audit
```bash
# Package third-party library
npx repomix --remote vendor/library --style xml -o audit.xml
```

### Documentation Generation
```bash
# Package with docs and code
repomix --include "src/**,docs/**,*.md" --style markdown -o context.md
```

### Bug Investigation
```bash
# Package specific modules
repomix --include "src/auth/**,src/api/**" -o debug-context.xml
```

### Implementation Planning
```bash
# Full codebase context
repomix --remove-comments --copy
```

## Command Line Reference

### File Selection
```bash
# Include specific patterns
repomix --include "src/**/*.ts,*.md"

# Ignore additional patterns
repomix -i "tests/**,*.test.js"

# Disable .gitignore rules
repomix --no-gitignore
```

### Output Options
```bash
# Output format
repomix --style markdown  # or xml, json, plain

# Output file path
repomix -o output.md

# Remove comments
repomix --remove-comments

# Copy to clipboard
repomix --copy
```

### Configuration
```bash
# Use custom config file
repomix -c custom-config.json

# Initialize new config
repomix --init  # creates repomix.config.json
```

## Token Management

Repomix tallies tokens three ways: per file, across the whole repository, and per output format.

Rough ceilings you are packing against:
- Claude Sonnet 4.5: ~200K tokens
- GPT-4: ~128K tokens
- GPT-3.5: ~16K tokens

### Token Count Optimization
Before you tune what goes in the bundle, it helps to know where the weight sits. The --token-count-tree option draws that picture for you:

```bash
repomix --token-count-tree
```
The result is a tree of your codebase annotated with token counts at each node:

```
🔢 Token Count Tree:
────────────────────
└── src/ (70,925 tokens)
    ├── cli/ (12,714 tokens)
    │   ├── actions/ (7,546 tokens)
    │   └── reporters/ (990 tokens)
    └── core/ (41,600 tokens)
        ├── file/ (10,098 tokens)
        └── output/ (5,808 tokens)
```
Pass a number to hide everything below a token floor and keep only the heavy hitters in view:

```bash
repomix --token-count-tree 1000  # Only show files/directories with 1000+ tokens
```

What this buys you:

- Spotting the files heavy enough to blow past a context window
- Tightening file selection through --include and --ignore patterns
- Aiming compression at the directories that actually move the number
- Trading content against context as you assemble code for a model

## Security Considerations

Under the hood Repomix runs Secretlint, which flags sensitive material: API keys, passwords, credentials, private keys, AWS secrets.

How to stay safe:
1. Read the output yourself before it leaves your machine
2. Park sensitive files in `.repomixignore`
3. Keep security checks on when the codebase is unfamiliar
4. Never let `.env` files into the bundle
5. Watch for credentials hardcoded into the source

When you genuinely need to turn the checks off:
```bash
repomix --no-security-check
```

## Implementation Workflow

When someone asks for a repository to be packed:

1. **Assess Requirements**
   - Pin down the target — local tree or remote repo
   - Decide which output format fits the job
   - Note any sensitive-data worries up front

2. **Configure Filters**
   - Set include patterns for the files that matter
   - Add ignore patterns for the noise
   - Decide whether comments stay or go

3. **Execute Packaging**
   - Run repomix with the options you settled on
   - Keep an eye on the token totals
   - Confirm the security scan ran

4. **Validate Output**
   - Read back through the generated file
   - Make sure nothing sensitive slipped in
   - Check the totals against your target model's ceiling

5. **Deliver Context**
   - Hand the packed file over
   - Pass along the token summary with it
   - Call out any warnings the run surfaced

## Reference Documentation

For the deeper material, see:
- [Configuration Reference](./references/configuration.md) - Config files, include/exclude patterns, output formats, advanced options
- [Usage Patterns](./references/usage-patterns.md) - AI analysis workflows, security audit preparation, documentation generation, library evaluation

## Additional Resources

- GitHub: https://github.com/yamadashy/repomix
- Documentation: https://repomix.com/guide/
- MCP Server: Available for AI assistant integration
