# Skills

This is the skill library of an installed Takumi kit. After `tkm init` it sits at `.claude/skills/` in
your project, and Claude reads from it on demand: a skill stays out of context until something in your
request matches what it declares itself for, at which point its instructions, references and scripts
become available.

58 skills ship here, covering the delivery lifecycle — planning, implementation, review, testing,
shipping, documentation — plus specialised ground such as frontend and backend work, databases,
deployment, design, media processing and threat intelligence. `/tkm:help` routes a task to the right one
when you are unsure which applies.

## How a skill is laid out

```
skills/<name>/
  SKILL.md          # required — frontmatter (name, description, when_to_use) + instructions
  references/       # optional — depth loaded only when the task needs it (47 skills have one)
  scripts/          # optional — code the skill runs rather than describes (24 skills have one)
```

The frontmatter decides whether your request reaches the skill at all, so it is written as a routing
signal: what the skill can do, in the words someone would actually type when they want it.

`_shared/` holds material several skills depend on — the canonical docs mapping, the processing levels,
the confidence taxonomy. Treat it as a library rather than a skill; nothing in it is invoked directly.

## Dependencies

Some skills call external tools: FFmpeg and ImageMagick for media, a few Node CLIs, and a Python virtual
environment for the document and scanning scripts. Install them once:

```bash
# Linux / macOS
cd .claude/skills && ./install.sh
```

```powershell
# Windows, PowerShell as Administrator
cd .claude\skills; .\install.ps1
```

`INSTALLATION.md` in this folder covers the manual route, the per-platform commands, and what to do when
a tool refuses to install.

## Adding a skill

A new skill needs its directory, a `SKILL.md` with valid frontmatter, and a catalog entry — the module
mapping in `claude/catalog/modules.json` is generated, and CI fails on drift:

```bash
npm run gen:catalog     # regenerate after adding, renaming or removing a skill
npm run check:catalog   # what CI runs; must report no drift
npm run check:skills    # frontmatter and structure validation
```

Write the description for the router, not for a reader who already knows the skill exists. A skill
nothing routes to is a skill nobody uses, however good its instructions are.

`agent_skills_spec.md` in this folder is the format specification the kit validates against.

## `document-skills/` is not ours

The `document-skills/` subdirectory — `docx`, `pdf`, `pptx`, `xlsx` — is Anthropic's work, carried here as
a reference for handling binary document formats. It is source-available rather than open source, it is a
point-in-time snapshot that Anthropic does not maintain for downstream users, and versions of these
skills ship inside Claude itself.

Attribution and licence terms for it and for every other third-party component are recorded in
`THIRD_PARTY_NOTICES.md`. Read that file before redistributing anything from this tree.

## Further reading

Anthropic's documentation on the skill system this library is built against:

- [What are skills?](https://support.claude.com/en/articles/12512176-what-are-skills)
- [Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
- [Creating custom skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)
- [Equipping agents for the real world with Agent Skills](https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
