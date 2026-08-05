# Harder Cases and the Awkward Corners

## Multi-Language Documentation

**The problem:** the docs come in more than one language.

**How to handle it:**
1. Pin down which language the user actually wants
2. Look for a language-tagged llms.txt
   - `llms-es.txt`, `llms-ja.txt`
3. Drop back to English when the localized file is missing
4. Flag any language gaps in the report

## Version-Specific Documentation

**Latest (the default):**
- Use the base llms.txt URL
- No version specifier needed

**A pinned version:**
```
WebSearch: "[library] v[version] llms.txt"
Check paths:
- /v2/llms.txt
- /docs/v2/llms.txt
- /{version}/llms.txt

For repos:
git checkout v[version] or tags/[version]
```

## Framework with Plugins

**The problem:** a core framework trailing 50 plugins behind it.

**How to handle it:**
1. Cover the core framework before anything else
2. Ask the user which plugins actually matter
3. Run a narrow search for just those plugins
4. List the plugins that exist in the report
5. Resist documenting the whole catalog up front

## Documentation Under Construction

**Tell-tale signs:**
- A fresh release whose docs aren't finished
- A trail of "Coming soon" pages
- Open GitHub issues asking for docs

**How to handle it:**
1. Say so at the top of the report
2. Stitch together what docs exist plus a code read
3. Look inside tests/ and examples/
4. Label anything you derived as "inferred from code"
5. Link the GitHub issues so the reader can track progress

## Conflicting Information

**When two sources disagree:**
1. Decide which is the primary official source
2. Note where the versions diverge
3. Lay out both approaches with their context
4. Point the reader at the official/latest one
5. Explain where the disagreement comes from

**Order of trust:**
1. Official docs (latest version)
2. Official docs (versioned)
3. GitHub README
4. Community tutorials
5. Stack Overflow

## Rate Limiting

**When the API starts pushing back:**
- Supply CONTEXT7_API_KEY from .env
- Back off exponentially between retries
- Hold results in the session so you don't re-fetch
- Group requests together where you can
