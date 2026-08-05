# Source-Code Security Audit — {PROJECT_NAME}
**Use context:** {internal|hybrid|customer-facing}

<!-- Findings come from `tkm:audit-security` in `full` mode, invoked via the Skill tool.
     Severity threshold: Critical | High | Medium only. Low/Info dropped — count noted in ## Truncated.
     Cite exact `path:line` for every finding. NEVER quote secret values. -->

## Summary

- Audit-security mode: `full`
- Audit-security source: `tkm:audit-security` via Skill tool
- Findings (post-cap): {X critical, Y high, Z medium}
- Files scanned: {N} (as reported by audit-security)

## Findings

- **[{Critical|High|Medium}] {A01:Broken Access Control | A02:Cryptographic Failures | A03:Injection | A04:Insecure Design | A05:Security Misconfiguration | A06:Vulnerable Components | A07:Auth Failures | A08:Data Integrity Failures | A09:Logging Failures | A10:SSRF}** — {one-line summary ≤120 chars} (`{path}:{line}`)
  <!-- OWASP category labels MUST match `claude/skills/audit-security/references/stride-owasp-checklist.md` §OWASP Top 10 Quick Reference verbatim. -->
- **[High] A03:Injection** — {example: SQL string concatenation in users query} (`{path}:{line}`)
- ...

<!-- When audit-security returns zero findings, replace the bullet list with:
     _None — audit-security found no STRIDE/OWASP issues at or above Medium severity._ -->

## Truncated

{N} low/info findings omitted (below severity threshold).

<!-- Omit this section entirely when no low/info findings were dropped. -->

## Notes

<!-- Use this section ONLY for degradation / failure annotations. Examples:
     - [AUDIT_FALLBACK] tkm:audit-security unavailable via Skill tool — no STRIDE/OWASP findings collected
     - [AUDIT_FORMAT_DRIFT] audit-security output format unexpected
     - [AUDIT_TIMEOUT] audit-security exceeded reasonable wall time
     Omit the section entirely when no degradation occurred. -->

## Raw Output

<!-- Only present when [AUDIT_FORMAT_DRIFT] fires. Fenced code block with the raw audit-security
     output so a future run can re-parse. Omit otherwise. -->

## Unresolved Questions

<!-- Optional — list any findings the subagent could not cite cleanly (path-escape, ambiguous line, etc.).
     Omit the section entirely when nothing is unresolved. -->

<!-- Total length under 300 lines. Snapshot only — no narration. -->
