# Policy Management

Read this before creating, showing, or editing `licenseal.policy.toml`.

## Policy File

`licenseal.policy.toml` lives at the project root and is owned by the project. It is separate from `licenseal.review.toml`, which remains licenseal's audit trail.

To create the file, copy the bundled template to the project root:

```bash
cp .claude/skills/audit-licenses/references/licenseal.policy.template.toml licenseal.policy.toml
```

If the project is using the kit source tree directly, the template path is `claude/skills/audit-licenses/references/licenseal.policy.template.toml`.

Do not overwrite an existing policy file.

## Supported Policy Entries

| Entry | Meaning |
|-------|---------|
| `licenses.allow` | SPDX identifiers accepted by policy |
| `licenses.deny` | SPDX identifiers blocked by policy |
| `risks.allow` | Licenseal risk categories accepted by policy |
| `risks.deny` | Licenseal risk categories blocked by policy |
| `[[packages.allow]]` | Ecosystem/package exceptions allowed by policy |
| `[[packages.deny]]` | Ecosystem/package entries blocked by policy |

Package entries use:

- `ecosystem`: package ecosystem, for example `npm`, `python`, `go`, `maven`.
- `package`: package name exactly as reported.
- `reason`: required for package allow/deny edits.
- `expires`: recommended for package allow entries; use `YYYY-MM-DD`.

## Supported Requests

```bash
/tkm:audit-licenses create license policy
/tkm:audit-licenses show license policy
/tkm:audit-licenses allow npm sharp because "Approved internal use" until 2026-12-31
/tkm:audit-licenses deny python pymupdf because "AGPL/proprietary not approved"
/tkm:audit-licenses allow MIT license
/tkm:audit-licenses deny AGPL-3.0-only license
/tkm:audit-licenses allow weak-copyleft risk
/tkm:audit-licenses deny network-copyleft risk
/tkm:audit-licenses remove npm sharp from policy
/tkm:audit-licenses remove MIT license from policy
/tkm:audit-licenses remove network-copyleft risk from policy
```

## Precedence

Apply policy findings in this order:

1. `packages.deny` blocks first.
2. `licenses.deny` blocks next.
3. `risks.deny` blocks next.
4. `packages.allow` can pass a finding only when `reason` exists; `expires` is recommended.
5. In strict policy mode, `licenses.allow` turns unlisted licenses into "needs review".
6. In strict policy mode, `risks.allow` turns unlisted risk categories into "needs review".

The deny side always wins over allow. Refuse to add an allow entry while the same exact package, license, or risk still exists in deny; ask the user to remove the deny first.

## Edit Rules

- If the policy is missing and the mode is `--init-policy`, create it from `references/licenseal.policy.template.toml`.
- If the policy is missing and the user adds an entry, create a minimal policy file containing that entry.
- Read the existing file before writing. Preserve unrelated entries and comments where practical.
- Use a TOML-aware parser when available; otherwise make the smallest safe patch.
- Adding a license to `licenses.deny` removes it from `licenses.allow`, and vice versa.
- Adding a risk to `risks.deny` removes it from `risks.allow`, and vice versa.
- `--remove-package` removes matching entries from both package allow and deny lists.
- `--remove-license` removes the SPDX id from both license lists.
- `--remove-risk` removes the risk id from both risk lists.
- Prefer exact SPDX identifiers. If the requested identifier is ambiguous, ask before editing.
- Do not auto-whitelist a finding just because licenseal failed. Policy edits require explicit user intent.
- After editing, re-open the file, summarize the change, and recommend rerunning `/tkm:audit-licenses`.

## Show Policy Output

When showing policy, report:

- allowed and denied licenses
- allowed and denied risks
- allowed and denied package entries with ecosystem, package, reason, and expires
- expired allow entries
- entries shadowed by higher-precedence denies
