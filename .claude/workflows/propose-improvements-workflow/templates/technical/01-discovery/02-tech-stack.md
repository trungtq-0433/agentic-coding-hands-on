# Tech Stack — {PROJECT_NAME}
**Use context:** {internal|hybrid|customer-facing}

- **Frameworks:** {web/UI/backend/ORM} — `{path:line}` per detected framework
- **Major libraries (up to 50 by weight/usage; cap = 50):**
  - `{package}@{version}` — `{path:line}`
  - … (up to 50 entries, ordered by import frequency / direct-dep priority)
- **Build tooling:** {webpack | vite | turbo | cargo | go build | gradle | …} (`{path:line}`)
- **Package manager + lockfile status:**
  - {ecosystem} — manifest `{path}`, lockfile `{path}`
  - {ecosystem} — manifest `{path}`, lockfile `{path}` or `(no lockfile)`
- **Database(s) / caches / queues / search / object storage:**
  - {service} — referenced in `{path:line}`
- **Declared runtime versions:** (EOL judgement is owned by step 4.1.06 — nyx-cli `lookup eol`)
  - `nodejs@{N}` — cite `package.json#engines.node`, `.nvmrc`, `package.json:line`
  - `python@{N.N}` — cite `pyproject.toml`, `.python-version`, `requirements.txt:line`
  - `go@{N.NN}` — cite `go.mod:line`
  - `rust@{N.NN}` — cite `rust-toolchain*:line`
  - `ruby@{N.N}` — cite `Gemfile`, `.ruby-version:line`
  - `php@{N.N}` — cite `composer.json#require.php:line`
  - `dotnet@{N.N}` — cite `*.csproj#<TargetFramework>:line`
  - `java@{N}` — cite `pom.xml#java.version`, `build.gradle:line`
  - {other runtime}@{version} — cite `{manifest:line}`
- **Declared framework versions:** (feeds step 4.1.06 nyx EOL batch)
  - `nextjs@{N}` — cite `package.json:line`
  - `django@{N.N}` — cite `requirements.txt:line`, `pyproject.toml:line`
  - `spring-boot@{N.N}` — cite `pom.xml:line`, `build.gradle:line`
  - `rails@{N.N}` — cite `Gemfile:line`
  - `laravel@{N.N}` — cite `composer.json:line`
  - {other framework}@{version} — cite `{manifest:line}`

<!-- Total length under 400 lines (cap raised to fit up-to-50 library list). Snapshot only — no narration.
     NEVER add EOL dates here — that field is owned by 4.1.06. -->
