# Canonical Fcode + Slug Schema

Authoritative spec for the `_canonical-fcodes.json` artifact emitted by Wave 5 alongside `feature-list.md`. Consumed by Wave 5.5 / FS.2 validators and as the slug source for FS.1 fan-out.

## Purpose

- **Single writer**: Wave 5 researcher (the only producer of `feature-list.md`) co-emits canonical JSON in the same step → cannot drift.
- **Single reader contract**: validators + orchestrator parse JSON; they do NOT re-derive slugs from feature names at validation time.
- **Folder lifecycle**: Wave 5 pre-creates `artifacts/features/{slug}/` and writes a `.pending` marker per feature. Wave 6 researcher removes `.pending` on successful `spec.md` write. Wave 7b reviewer treats lingering `.pending` as `MISSING`.

## Schema

File path: `plans/<active-plan>/artifacts/_canonical-fcodes.json`

```json
{
  "generated_at": "2026-05-15T15:33:00Z",
  "plan": "260515-1533-rebuild-spec-validator-hardening",
  "features": [
    {
      "fcode": "F001",
      "name": "Authentication",
      "slug": "F001_Auth",
      "priority": "P0",
      "type": "ui",
      "related": {
        "screens": ["SCR001_LoginForm"],
        "user_stories": ["US001_Login"],
        "routes": ["POST /login"],
        "models": ["User"],
        "bl": [],
        "perms": ["PERM001_AuthRequired"]
      }
    }
  ]
}
```

### Field rules

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `generated_at` | ISO-8601 string | yes | UTC timestamp of W5 emit |
| `plan` | string | yes | Active plan slug (matches plan dir name) |
| `features` | array | yes | Sorted by `fcode` ascending |
| `features[].fcode` | string | yes | Format `F\d{3}` |
| `features[].name` | string | yes | Verbatim from FeatureList `## Feature Details` heading |
| `features[].slug` | string | yes | Derived per § Slug Grammar; matches `^F\d{3}_[A-Za-z0-9]+$` |
| `features[].priority` | string | yes | One of `P0`, `P1`, `P2`, `P3` |
| `features[].type` | string | yes | One of `ui`, `background`, `mixed` |
| `features[].related` | object | yes | Empty arrays allowed; keys: `screens`, `user_stories`, `routes`, `models`, `bl`, `perms` |

## Slug Grammar

Slug = `F{NNN}_{CamelCaseName}` where `CamelCaseName` is derived from `features[].name`:

1. Strip leading/trailing whitespace.
2. Replace `&` with `And`.
3. Split on any run of `[^A-Za-z0-9]+` (whitespace, hyphen, underscore, slash, punctuation).
4. For each token: keep alnum chars only; capitalize first char, lowercase remainder.
5. Concatenate tokens (CamelCase).
6. If resulting CamelCase exceeds **36 chars**, truncate to 36.
7. Final slug: `{fcode}_{CamelCase}` (max length 41 = 4 (fcode) + 1 (`_`) + 36 (CamelCase)).

Regex contract: `^F\d{3}_[A-Za-z0-9]+$` — slug MUST match this regex after derivation.

### Examples

| Input name | Derived slug |
|-----------|--------------|
| `Authentication` | `F001_Authentication` |
| `User Profile & Settings` | `F042_UserProfileAndSettings` |
| `Order checkout / payment` | `F015_OrderCheckoutPayment` |
| `2FA flow` | `F008_2faFlow` |
| `Reset-password (email)` | `F022_ResetPasswordEmail` |
| `Inventory  bulk   import` (extra spaces) | `F030_InventoryBulkImport` |

## Collision Rule

If two features in the same plan derive the **same slug**, Wave 5 MUST:

1. Emit `[ERROR] SLUG_COLLISION: F### "name-a" and F### "name-b" both derive slug "F###_X"` to stdout.
2. Abort BEFORE writing `_canonical-fcodes.json` and BEFORE creating any folders.
3. Do NOT silently append a suffix. The user resolves by renaming one feature in `feature-list.md`, then reruns Wave 5.

This is a HARD halt — no partial writes, no implicit recovery.

## Folder Lifecycle

Per-feature folder under `plans/<active-plan>/artifacts/features/{slug}/`:

| Stage | Action | Marker state |
|-------|--------|--------------|
| W5 emit | `mkdir -p features/{slug}/` + `touch features/{slug}/.pending` | `.pending` present |
| FS.1 dispatch | TaskCreate prompt prepends `mkdir -p features/{slug}/` (idempotent guard in case W5 skipped) | `.pending` present |
| FS.1 researcher writes 4 files | researcher contract: `rm features/{slug}/.pending` on successful write | `.pending` removed |
| FS.1 researcher failure | `.pending` remains | `.pending` present (signals partial) |
| FS.5 reviewer | reads each `features/{slug}/`; if `.pending` present → emit `MISSING` (counts toward `failed`) | — |

`.pending` is a zero-byte sentinel. Its sole purpose is to mark partial writes so downstream stages can detect them deterministically.

## Migration / Fallback

Legacy plans without `_canonical-fcodes.json`:

- Validators (W5.5, FS.2) tolerate absence — when JSON is missing, they emit `[WARN] canonical_missing` and fall back to regex-parsing `feature-list.md` `## Feature Hierarchy` table rows.
- Fallback regex: `^\|\s*(F\d{3}_\w+)\s*\|` against hierarchy table lines.
- Orchestrator emits `[WARN]` advisory once per run; validation still proceeds.
- The fallback path is intentionally lossy (no priority/type/related fields surfaced) — re-run Wave 5 in a fresh plan to regenerate canonical JSON for full validation depth.

## Security

- `slug` is interpolated into shell `mkdir -p` and into file paths. The regex `^F\d{3}_[A-Za-z0-9]+$` filters all shell metacharacters before any subprocess call.
- All path interpolations use list-form `subprocess.run(["mkdir", "-p", str(path)])` or Python `pathlib` — never `shell=True`, never `os.system`.
- Slug derivation strips non-alnum chars first, so feature names containing `;`, `|`, `$`, backticks, or path separators cannot escape into shell commands.

## See also

- `references/pipeline-w5x-w6.md` — Wave 5 emit step, Wave 6 fan-out mkdir guard, Wave 5.5 / 6.5 validator gates
- `references/feature-spec-researcher-contract.md` — `rm .pending` post-write step
- `templates/feature-list-template.md` — co-emission note
- `scripts/_slug_lib.py` — Python helpers (load_canonical, parse_feature_list_fallback, derive_slug, git_root)
