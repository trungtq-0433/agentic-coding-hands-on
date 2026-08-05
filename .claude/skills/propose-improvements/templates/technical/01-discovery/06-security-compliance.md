# Security & Compliance Surface — {PROJECT_NAME}
**Use context:** {internal|hybrid|customer-facing}

<!-- CVE + EOL lookup is DUAL-SOURCE, results deduped by advisory ID:
       1. OSV.dev /v1/querybatch — CVE/GHSA/RUSTSEC/OSV across npm/PyPI/Go/Maven/etc.
       2. nyx-cli `sdo nyx lookup vuln|eol` — Sun*-internal CVE feed (:package) + runtime/framework EOL (:techstack, endoflife.date).
     Cite exact `path:line` from a lockfile/manifest. Every CVE/EOL bullet MUST carry [src: osv|nyx|both].
     If one source is unreachable, surviving-source bullets ship as-is; unilateral entries get `needs-network-verify`.
     If both unreachable, every dual-source bullet is tagged `needs-network-verify`.
     NEVER invent CVE/GHSA IDs or EOL dates — every value MUST come from a real API response. -->

<!-- Source status (emit once at top of Known-bad when relevant):
     nyx-cli: not-ready — continuing OSV-only | nyx-cli: unreachable
     osv-api: unreachable
     dual-source: both unreachable -->

## Known-bad version flags

<!-- One bullet per UNIQUE advisory ID across both sources. CVSS preferred from nyx (numeric),
     fallback to OSV severity string. Show both inline if they disagree. -->

- **{ecosystem}:** `{package}@{version}` → {CVE-XXXX-NNNN | GHSA-xxxx-xxxx-xxxx} [{severity}|CVSS={n.n}] [src: both] — {summary} (`{path:line}`)
- **{ecosystem}:** `{package}@{version}` → {CVE-XXXX-NNNN} [CVSS={n.n}] [src: nyx] — {nyx title} (`{path:line}`)
- **{ecosystem}:** `{package}@{version}` → {GHSA-xxxx-xxxx-xxxx} [{severity}] [src: osv] — {osv summary} (`{path:line}`)
- **{ecosystem}:** `{package}@{version}` → `possible-concern — manual verification needed (dual-source unreachable)` `needs-network-verify` (`{path:line}`)

## Runtime / framework EOL

<!-- Authoritative via nyx-cli `lookup eol` (type: techstack, endoflife.date source).
     `eolFrom` reproduced verbatim as YYYY-MM-DD. matched=<normalized version>.
     EOL = vendor support has ended. SUPPORTED = upcoming `eolFrom` is the horizon. -->

### Runtimes

- `{runtime}@{declared-version}` → eolFrom=`{YYYY-MM-DD}` [matched={matchedVersion}, source={source}] — **{EOL|SUPPORTED}** [src: nyx] (cite `{manifest:line}`)
  - Example: `nodejs@16.0.0` → eolFrom=`2023-09-11` [matched=16, source=endoflife.date] — **EOL** [src: nyx] (cite `package.json:5`)
  - Example: `python@3.11` → eolFrom=`2027-10-31` [matched=3.11, source=endoflife.date] — **SUPPORTED** [src: nyx] (cite `pyproject.toml:8`)

### Frameworks

- `{framework}@{declared-version}` → eolFrom=`{YYYY-MM-DD}` [matched={matchedVersion}, source={source}] — **{EOL|SUPPORTED}** [src: nyx] (cite `{manifest:line}`)
  - Example: `nextjs@12` → eolFrom=`2022-11-21` [matched=12, source=endoflife.date] — **EOL** [src: nyx] (cite `package.json:24`)
  - Example: `django@4.2` → eolFrom=`2028-04-01` [matched=4.2, source=endoflife.date] — **SUPPORTED** [src: nyx] (cite `requirements.txt:3`)

### Unscannable runtimes / frameworks

<!-- nyx-cli returned `resolved: false` — likely name normalization needed or genuinely unknown tech. -->

- `{name}@{version}` — nyx-coverage: none (cite `{manifest:line}`)

## Unscannable ecosystems (CVE)

<!-- OSV cannot index AND nyx-cli could not resolve as :package. -->

- **{ecosystem}:** manifest detected at `{path}`, CVE evaluation requires external scan.

## Dependency-vulnerability tooling presence

- {`.github/dependabot.yml` | `renovate.json` | `.snyk` | `npm audit` in CI | `pip-audit` | `cargo audit` | `govulncheck` | `trivy` | `grype` | `osv-scanner`} — `{path:line}`
- Or: `no vulnerability tooling configured`

## Secret-management posture

- `.env` files committed: {yes / no} — paths: `{path:line}` (NEVER quote values)
- Env-loading libraries: {dotenv | python-dotenv | viper | godotenv} (`{path:line}`)
- Secret-manager references: {AWS Secrets Manager | GCP Secret Manager | Vault | Doppler | 1Password} (`{path:line}`)

## License manifest

- `LICENSE` presence: {yes / no} — `{path}`
- Top-dep licenses (when discoverable): `{package} → {license}` (`{lockfile-path:line}` or `package.json#license`)

## Supply-chain hygiene

- Unpinned/loose ranges: {N} occurrences in `{lockfile-path}` (cite a few `path:line`)
- Git-ref / tarball / local-path installs: {N} occurrences (cite `path:line`)
- Lifecycle scripts (`postinstall` / `preinstall` / `install`) in third-party deps: {N} (cite `path:line`)
- Pre-release versions in production manifests: `{package}@{version}` (`{path:line}`)

<!-- Total length under 300 lines. Snapshot only — no narration. -->
