# Product Surface — {PROJECT_NAME}
**Use context:** {internal|hybrid|customer-facing}

- **Public entrypoints:**
  - HTTP routes: {N} routes — sample `{path:line}` per route file
  - CLI commands: {N} commands — `{bin-path:line}` or `{console_scripts}` block
  - Exported packages / SDK published: {package-name} (`{path:line}`)
- **User-facing UI presence:** {yes / no} — framework: {React | Vue | Svelte | Blade | …}
- **Vendor-category map:**
  - **{category}:** {vendor} (`{path:line or config key}`) <!-- mark `single-vendor` if only one vendor in category -->
  - **{category}:** {vendor} (`{path:line}`) `single-vendor`
- **Host-platform map:**
  - `host-platform: {platform-name}` (`{path:line}` — manifest evidence: `host_permissions`, `engines.vscode`, `contributes`, etc.)
  - Or: `(none detected)`

<!-- Total length under 150 lines. Snapshot only — no narration. -->
