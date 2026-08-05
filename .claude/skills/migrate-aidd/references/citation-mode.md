# Citation Mode — migrate-aidd

migrate-aidd invokes `validate_source_citations.py --mode spec-driven` because its
feature specs cite spec sections, not source-code line ranges.

## Validator invocation

```
validate_source_citations.py \
  --spec <feature>/spec.md --project-root <root> \
  --mode spec-driven --specs-root <speckit_root>
```

## Valid citation forms (spec-driven mode)

### 1. spec:// URI — logical reference, no file-existence check

Grammar: `spec://<NNN-feature-slug>/<file>.md[#section]`

- `NNN` — one or more digits (e.g. `001`)
- `<feature-slug>` — word chars / hyphens (e.g. `auth`, `user-profile`)
- `#section` — optional free-form anchor; not validated

```
**Source:** `spec://001-auth/spec.md`
**Source:** `spec://042-billing/data-model.md#payment-states`
**Source:** `spec://010-user-profile/spec.md#validation-rules`
```

### 2. specsRoot-relative path — real file, no line-range required

A path that resolves to an existing file under `--specs-root`. No `:N-M` needed.

```
**Source:** `001-auth/spec.md:1`    # accepted if file exists under specs-root
```

### 3. Source path with line range — unchanged from source mode

```
**Source:** `src/auth/login.ts:42-58`   # real file, valid line range
```

## [FROM_CODE] tag

Lines containing `[FROM_CODE]` are **always** validated as real source paths with a
valid line range — the spec-driven relaxation does NOT apply.

```
**Source:** `src/auth/login.ts:10-20` [FROM_CODE]   # validated strictly
**Source:** `spec://001-auth/spec.md` [FROM_CODE]    # FAILS — no line range
```

Use `[FROM_CODE]` when a citation was extracted programmatically and must maintain
strong traceability.

## Security

`..`, absolute paths, and null bytes are rejected in all citation forms before any
file resolution — both in `source` and `spec-driven` modes.
