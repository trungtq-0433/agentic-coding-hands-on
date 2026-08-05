#!/usr/bin/env bash
# codex-companion.sh — single entrypoint for the --codex-companion flag across skills.
#
# WHY a Bash entrypoint instead of the /codex:* slash-commands:
#   The plugin's /codex:review and /codex:adversarial-review declare
#   `disable-model-invocation: true` — the model CANNOT call them from inside a
#   skill. Their /codex:status and /codex:result are disabled too. Only Bash is
#   reliably model-invokable, so every companion call goes through this script,
#   which drives the plugin's own runtime (codex-companion.mjs) or the codex CLI
#   directly. This is the plugin's real engine — same code the slash-commands run.
#
# Subcommands:
#   probe [sub]                          -> AVAILABLE | UNAVAILABLE:<reason>
#   review <scope> [--base <ref>] [focus...]   git-diff adversarial review (review-code)
#   counterview <file|->                 free-text design challenge   (brainstorm)
#   plan-review <plan-dir>               repo-grounded plan red-team  (create-plan)
#   rescue <prompt>                      read-only investigation/fix  (fix-bug)
#   install-plugin                       install codex-plugin-cc (consented; needs restart)
#
# Reasons: no-cli | not-authed | plugin-missing | no-timeout | timeout |
#          codex-failed | empty-output | secrets-in-diff | repo-secrets |
#          no-grounded-findings
# Always prints signals to stdout; diagnostic text to stderr.
set -uo pipefail

# --- secret patterns (shared by review + plan-review gates) ------------------
# Names that are secret-bearing by convention.
SECRET_NAME_RE='(^|/)(\.env([.-][^/]*)?|[^/]*\.(pem|key|p12|pfx)|id_rsa|credentials?|secrets?)$'
# Non-secret template/example variants that must NOT trip the name gate.
SAFE_NAME_RE='\.(example|sample|template|dist)(\.[^/]*)?$'
# Content signatures: keyword-assignments (need := to cut doc-text noise) PLUS
# known credential value formats (GitHub/OpenAI/AWS/Slack/JWT/Google/PEM).
SECRET_CONTENT_RE='(api[_-]?key|apikey|secret|token|passwd|password|credential|private[_-]?key|access[_-]?key|secret[_-]?key|client[_-]?secret|aws_(access|secret)_key(_id)?|auth(orization)?)["'"'"' ]*[:=]|-----BEGIN [A-Z ]*PRIVATE KEY-----|(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{10,}|github_pat_[A-Za-z0-9_]{10,}|sk-[A-Za-z0-9]{10,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{5,}|eyJ[A-Za-z0-9_-]{8,}[.]eyJ[A-Za-z0-9_-]{8,}|AIza[0-9A-Za-z_-]{20,}'

# --- resolve the installed plugin runtime (version-proof: pick highest) ------
resolve_plugin_script() {
  local base="${HOME}/.claude/plugins/cache/openai-codex/codex"
  [ -d "$base" ] || return 1
  local root
  root="$(ls -d "$base"/*/ 2>/dev/null | sort -V | tail -1)"
  [ -n "$root" ] || return 1
  local script="${root}scripts/codex-companion.mjs"
  [ -f "$script" ] || return 1
  printf '%s' "$script"
}

# Echo an available timeout implementation (Linux/WSL: timeout; macOS: gtimeout).
_timeout_cmd() {
  if command -v timeout  >/dev/null 2>&1; then echo timeout
  elif command -v gtimeout >/dev/null 2>&1; then echo gtimeout
  fi
}

# _bounded <seconds> <cmd...>: run cmd under a HARD wall-clock bound so a hung
# service call degrades instead of stalling the skill.
# returns: 0 ok | 124 timed out | 125 no timeout utility | else the cmd's exit code
_bounded() {
  local secs="$1"; shift
  case "$secs" in ''|*[!0-9]*) secs=300 ;; esac; [ "$secs" -lt 1 ] && secs=300
  local to; to="$(_timeout_cmd)"
  [ -z "$to" ] && return 125
  "$to" --kill-after=30s "$secs" "$@"
  local rc=$?
  { [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; } && return 124
  return "$rc"
}

# Install the codex-plugin-cc plugin (marketplace + plugin). Idempotent. Only run
# after user consent (the skill asks via AskUserQuestion on UNAVAILABLE:plugin-missing).
# NOTE: the plugin's /codex:* commands + runtime register only AFTER a session
# restart — it cannot be used in the current session.
install_plugin() {
  command -v claude >/dev/null 2>&1 || { echo "ERROR: claude CLI not found on PATH" >&2; return 1; }
  claude plugin marketplace add openai/codex-plugin-cc || { echo "ERROR: marketplace add failed" >&2; return 1; }
  claude plugin install codex@openai-codex --scope user   || { echo "ERROR: plugin install failed" >&2; return 1; }
  echo "INSTALLED: restart the Claude Code session to activate /codex:* and the companion runtime."
}

# probe [counterview|plan-review|review|rescue|all]
#   counterview/plan-review need only an authenticated CLI (use `codex exec` directly).
#   review/rescue additionally need the plugin runtime (codex-companion.mjs).
probe() {
  local need="${1:-all}"
  command -v codex >/dev/null 2>&1 || { echo "UNAVAILABLE:no-cli"; return 0; }
  codex login status >/dev/null 2>&1 || { echo "UNAVAILABLE:not-authed"; return 0; }
  case "$need" in
    counterview|plan-review) : ;;   # CLI-only, no plugin runtime required
    *) resolve_plugin_script >/dev/null 2>&1 || { echo "UNAVAILABLE:plugin-missing"; return 0; } ;;
  esac
  echo "AVAILABLE"
}

# Scan a NUL-delimited path list on stdin for secret names or secret content.
# Returns 0 on first hit. `./` prefix + `-e <pat> --` keep filenames (incl. `-`,
# leading-dash, spaces) as real paths, never grep options/stdin. `-I` skips binary.
_scan_paths_secrets() {
  local f
  while IFS= read -r -d '' f; do
    if printf '%s\n' "$f" | grep -qiE "$SECRET_NAME_RE" \
       && ! printf '%s\n' "$f" | grep -qiE "$SAFE_NAME_RE"; then return 0; fi
    grep -lIiE -e "$SECRET_CONTENT_RE" -- "./$f" >/dev/null 2>&1 && return 0
  done
  return 1
}

# True if the review scope's changed files/diff carry secrets, so we never egress
# .env / keys / credentials to Codex. Conservative: a hit degrades to Claude-only.
_diff_has_secrets() {
  local scope="$1" base="$2" names content
  if [ "$scope" = "branch" ] && [ -n "$base" ]; then
    names="$(git diff --name-only "$base"...HEAD 2>/dev/null)"
    content="$(git diff "$base"...HEAD 2>/dev/null)"
    printf '%s\n' "$names" | grep -iE "$SECRET_NAME_RE" | grep -qivE "$SAFE_NAME_RE" && return 0
    printf '%s\n' "$content" | grep -qiE "$SECRET_CONTENT_RE" && return 0
  else
    names="$(git status --porcelain --untracked-files=all 2>/dev/null | awk '{print $NF}')"
    content="$(git diff 2>/dev/null; git diff --cached 2>/dev/null)"
    printf '%s\n' "$names" | grep -iE "$SECRET_NAME_RE" | grep -qivE "$SAFE_NAME_RE" && return 0
    printf '%s\n' "$content" | grep -qiE "$SECRET_CONTENT_RE" && return 0
    # Untracked files are sent to Codex too but never appear in `git diff` — scan them.
    _scan_paths_secrets < <(git ls-files -z --others --exclude-standard 2>/dev/null) && return 0
  fi
  return 1
}

# True if the repository carries secret-bearing FILES that Codex could read during
# a plan-review (which grants read access to the whole tree). Detection is by NAME
# and INCLUDES gitignored files (e.g. `.env`) — the real egress vector. It does NOT
# content-scan tracked source: credential-shaped strings in the codebase are not a
# leak (they are already the code the user develops, and Codex reads tracked files
# by design here), and content-scanning would false-positive on any security repo.
_repo_has_secrets() {
  local root; root="$(git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$PWD")"
  # Scan the WHOLE tree (no depth cap — deep secrets must not slip through). Prune
  # ONLY dependency/VCS internals that never hold the user's own secrets and are the
  # real perf cost (node_modules, .git, .venv); do NOT prune build/dist/target/etc —
  # a user can legitimately keep secret files there, so skipping them would leak.
  # Secret-bearing FILES by name, incl. gitignored ones Codex can still read;
  # templates/examples are allowlisted.
  find "$root" \
      \( -name node_modules -o -name .git -o -name .venv \) -prune -o \
      -type f \
      \( -name '.env' -o -name '.env.*' -o -name '*.pem' -o -name '*.key' -o -name '*.p8' \
         -o -name '*.p12' -o -name '*.pfx' -o -name '*.jks' -o -name '*.keystore' \
         -o -name '*.ppk' -o -name '*.der' -o -name 'id_rsa' -o -name 'id_dsa' \
         -o -name 'id_ecdsa' -o -name 'id_ed25519' -o -name '.npmrc' -o -name '.pgpass' \
         -o -name '.netrc' -o -name '.htpasswd' -o -iname 'credentials' \
         -o -iname 'credentials.json' -o -iname 'credentials.yml' -o -iname 'credentials.yaml' \
         -o -iname 'secrets.json' -o -iname 'secrets.yml' -o -iname 'secrets.yaml' \) \
      ! -name '*.example' ! -name '*.sample' ! -name '*.template' ! -name '*.dist' \
      -print 2>/dev/null | head -1 | grep -q . && return 0
  return 1
}

# Map _bounded's return code to a degradation signal on stderr. Echoes nothing on
# success (rc 0). $1 = rc, $2 = timeout-signal word (e.g. "timeout" or "TIMEOUT").
_degrade_from_rc() {
  case "$1" in
    0)   return 0 ;;
    125) echo "UNAVAILABLE:no-timeout" >&2; return 2 ;;
    124) echo "${2:-UNAVAILABLE:timeout}" >&2; return 124 ;;
    *)   echo "UNAVAILABLE:codex-failed" >&2; return 3 ;;
  esac
}

# --- review-code: adversarial review over a git diff -------------------------
# Usage: review <auto|working-tree|branch> [--base <ref>] [focus text...]
review() {
  local script; script="$(resolve_plugin_script)" || { echo "UNAVAILABLE:plugin-missing" >&2; return 2; }
  local scope="${1:-working-tree}"; shift || true
  local base_args=() base=""
  if [ "${1:-}" = "--base" ]; then base_args=(--base "$2"); base="$2"; shift 2; fi
  local focus="$*"
  # Secret pre-scan: never send .env/keys/credentials in the diff to Codex.
  if _diff_has_secrets "$scope" "$base"; then echo "UNAVAILABLE:secrets-in-diff" >&2; return 2; fi
  # Bounded so a hung service call degrades. node prints the rendered review to stdout.
  # `--` terminates options so focus text starting with `-` stays literal.
  _bounded "${CODEX_REVIEW_TIMEOUT:-300}" \
    node "$script" adversarial-review --wait --scope "$scope" "${base_args[@]}" -- ${focus:+"$focus"}
  _degrade_from_rc "$?"
}

# --- brainstorm: challenge a design decision (no git diff exists) ------------
# The plugin's adversarial-review is git-diff-bound, so a design proposal must
# go through the codex CLI directly with an adversarial design prompt.
counterview() {
  local approach
  if [ "${1:-}" != "-" ] && [ -f "${1:-}" ]; then approach="$(cat "$1")"; else approach="$(cat)"; fi
  [ -n "${approach// }" ] || { echo "ERROR: empty approach" >&2; return 1; }
  command -v codex >/dev/null 2>&1 || { echo "UNAVAILABLE:no-cli" >&2; return 2; }

  local prompt="You are an adversarial reviewer challenging a chosen DESIGN decision (no code yet). \
Question the approach itself: hidden risks, failure modes under load, scaling/operational traps, cost \
blowups, false assumptions, cases the author likely missed. Do NOT restate the plan, agree, or rewrite \
the solution. Output 4-6 objections, one line each, each naming a concrete scenario (inputs/state -> \
what breaks). Output ONLY a markdown bullet list.

CHOSEN APPROACH:
${approach}"

  local out; out="$(mktemp)"; trap 'rm -f "$out"' RETURN
  _bounded "${CODEX_COUNTERVIEW_TIMEOUT:-300}" \
    codex exec -s read-only --skip-git-repo-check --color never -o "$out" "$prompt" >/dev/null 2>&1
  _degrade_from_rc "$?" || return
  [ -s "$out" ] || { echo "UNAVAILABLE:empty-output" >&2; return 3; }
  cat "$out"
}

# Validate one `path:line` / `path:start-end` citation against the repo: the file
# must exist and the line (and range end, if any) must be within bounds. This is a
# LOCATION check only — it proves the citation points at real code, not that the
# code supports the claim; semantic merit is still adjudicated downstream (Step 6/7).
# Returns 0/1.
_valid_citation() {
  local cite="$1" path rest start end total root real
  case "$cite" in *:*) ;; *) return 1 ;; esac
  path="${cite%%:*}"; rest="${cite#*:}"; start="${rest%%-*}"
  [ -n "$path" ] || return 1
  # Confine to the repo: no absolute paths, no `..` traversal.
  case "$path" in /*|*..*) return 1 ;; esac
  # Citations are repo-root-relative — resolve them against the repo root, NOT the
  # helper's cwd, so validation works when invoked from any subdirectory.
  # Canonicalize + require the file strictly beneath the root; this also closes
  # in-repo symlinks to external files. FAIL CLOSED if we cannot canonicalize.
  command -v realpath >/dev/null 2>&1 || return 1
  root="$(git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$PWD")"
  root="$(realpath -- "$root" 2>/dev/null)" || return 1
  [ -f "$root/$path" ] || return 1
  real="$(realpath -- "$root/$path" 2>/dev/null)" || return 1
  case "$real" in "$root"/*) ;; *) return 1 ;; esac
  case "$start" in ''|*[!0-9]*) return 1 ;; esac
  total="$(wc -l < "$real" 2>/dev/null || echo 0)"
  [ "$start" -ge 1 ] && [ "$start" -le "$total" ] || return 1
  # If a range end is present, it must be numeric, >= start, and within bounds.
  if [ "$rest" != "$start" ]; then
    end="${rest#*-}"
    case "$end" in ''|*[!0-9]*) return 1 ;; esac
    [ "$end" -ge "$start" ] && [ "$end" -le "$total" ] || return 1
  fi
  return 0
}

# True if the text after `label` on `line` has any non-whitespace content — so an
# empty field like `- **Location:**` does not count as present.
_nonempty_after() { local v="${1#*"$2"}"; v="${v//[[:space:]]/}"; [ -n "$v" ]; }

# Read Codex finding blocks on stdin; print only blocks that match the FULL persona
# schema — a `## Finding` header plus every required field with non-empty content
# (Severity as a valid enum, Location, Flaw, Failure scenario, Evidence as a
# resolvable citation, Suggested fix). Off-schema / hallucinated blocks are dropped
# so garbage never reaches the red-team pool. Kept -> stdout; counts/degrade -> stderr.
# Returns 0 if >=1 block kept, 4 if none.
_filter_finding_blocks() {
  local kept=0 dropped=0 block="" cite="" sev="" line v
  local has_head=0 has_loc=0 has_flaw=0 has_scen=0 has_fix=0
  _reset() { block=""; cite=""; sev=""; has_head=0; has_loc=0; has_flaw=0; has_scen=0; has_fix=0; }
  _flush() {
    [ -n "${block// }" ] || return 0
    if [ "$has_head" -eq 1 ] && [ "$has_loc" -eq 1 ] && [ "$has_flaw" -eq 1 ] \
       && [ "$has_scen" -eq 1 ] && [ "$has_fix" -eq 1 ] \
       && [ -n "$cite" ] && _valid_citation "$cite" \
       && { [ "$sev" = "Critical" ] || [ "$sev" = "High" ] || [ "$sev" = "Medium" ]; }; then
      printf '%s' "$block"; kept=$((kept+1))
    else dropped=$((dropped+1)); fi
  }
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      "## Finding"*) _flush; _reset; block="$line"$'\n'; has_head=1 ;;
      *) block+="$line"$'\n'
         case "$line" in
           *'**Location:**'*)          _nonempty_after "$line" '**Location:**'         && has_loc=1 ;;
           *'**Flaw:**'*)              _nonempty_after "$line" '**Flaw:**'             && has_flaw=1 ;;
           *'**Failure scenario:**'*)  _nonempty_after "$line" '**Failure scenario:**' && has_scen=1 ;;
           *'**Suggested fix:**'*)     _nonempty_after "$line" '**Suggested fix:**'    && has_fix=1 ;;
           *'**Evidence:**'*)
             cite="$(printf '%s' "$line" | grep -oE '[A-Za-z0-9_./-]+:[0-9]+(-[0-9]+)?' | head -1)" ;;
           *'**Severity:**'*)
             # Value AFTER the label; trim ONLY surrounding whitespace (not inner —
             # "H i g h" must fail) and require an EXACT enum match.
             v="${line#*'**Severity:**'}"
             v="${v#"${v%%[![:space:]]*}"}"   # ltrim
             v="${v%"${v##*[![:space:]]}"}"   # rtrim
             case "$v" in Critical|High|Medium) sev="$v" ;; *) sev="" ;; esac ;;
         esac ;;
    esac
  done
  _flush
  if [ "$kept" -eq 0 ]; then echo "UNAVAILABLE:no-grounded-findings (dropped $dropped)" >&2; return 4; fi
  [ "$dropped" -gt 0 ] && echo "note: dropped $dropped finding(s) off-schema (missing/empty field, bad severity, or unresolvable citation)" >&2
  return 0
}

# --- create-plan: repo-grounded red-team of an implementation plan ----------
# Codex reviews WITH repo access (no --skip-git-repo-check), emits the persona
# finding schema, and the helper drops any finding whose citation does not resolve.
plan_review() {
  local dir="${1:-}"
  [ -n "$dir" ] && [ -d "$dir" ] || { echo "ERROR: plan dir not found: ${dir:-<none>}" >&2; return 1; }
  command -v codex >/dev/null 2>&1 || { echo "UNAVAILABLE:no-cli" >&2; return 2; }
  # Plan-review grants Codex read access to the whole repo — refuse if secrets are present.
  if _repo_has_secrets; then echo "UNAVAILABLE:repo-secrets" >&2; return 2; fi

  local plan_text; plan_text="$(cat "$dir"/plan.md "$dir"/phase-*.md 2>/dev/null)"
  [ -n "${plan_text// }" ] || { echo "ERROR: empty plan (no plan.md/phase-*.md in $dir)" >&2; return 1; }

  local prompt="You are a HOSTILE red-team reviewer of an implementation PLAN. Read the ACTUAL repository \
(read-only) to ground every claim in real code. Do NOT open, read, or quote secret-bearing files \
(.env, credentials, *.pem, *.key, id_rsa, .npmrc, tokens) — skip them entirely. Find where the plan is \
wrong, risky, incomplete, sequenced \
badly, or built on false assumptions about the codebase. Do NOT praise, agree, or restate the plan. \
EVERY finding MUST cite a real, existing file:line from the repo in the **Evidence:** field (e.g. \
src/auth/guard.ts:42 or a range src/auth/guard.ts:42-58) — a finding you cannot ground that way is \
worthless, omit it. Output 3-8 findings, each EXACTLY in this block format and nothing else:

## Finding {N}: {short title}
- **Severity:** Critical|High|Medium
- **Location:** {plan phase/section the flaw sits in}
- **Flaw:** {what is wrong}
- **Failure scenario:** {concrete way it fails}
- **Evidence:** {real file:line from the repo}
- **Suggested fix:** {concrete fix}

PLAN UNDER REVIEW:
${plan_text}"

  local out; out="$(mktemp)"; trap 'rm -f "$out"' RETURN
  _bounded "${CODEX_PLAN_TIMEOUT:-300}" \
    codex exec -s read-only --color never -o "$out" "$prompt" >/dev/null 2>&1
  _degrade_from_rc "$?" || return
  [ -s "$out" ] || { echo "UNAVAILABLE:empty-output" >&2; return 3; }
  _filter_finding_blocks < "$out"
}

# --- fix-bug: delegate investigation/fix (read-only; codex proposes) --------
rescue() {
  local script; script="$(resolve_plugin_script)" || { echo "UNAVAILABLE:plugin-missing" >&2; return 2; }
  local prompt="$*"
  [ -n "${prompt// }" ] || { echo "ERROR: empty rescue prompt" >&2; return 1; }
  # No --write => read-only sandbox: codex investigates and PROPOSES a fix.
  # `-- "$prompt"` keeps a prompt containing --write/--cwd literal (no sandbox escape).
  # Bounded: status/result slash-cmds are model-disabled, so a hung job can't be polled.
  _bounded "${CODEX_RESCUE_TIMEOUT:-300}" node "$script" task -- "$prompt"
  _degrade_from_rc "$?" "TIMEOUT"
}

case "${1:-}" in
  probe)          shift; probe "$@" ;;
  review)         shift; review "$@" ;;
  counterview)    shift; counterview "$@" ;;
  plan-review)    shift; plan_review "$@" ;;
  rescue)         shift; rescue "$@" ;;
  install-plugin) shift; install_plugin "$@" ;;
  *) echo "usage: codex-companion.sh {probe|review|counterview|plan-review|rescue|install-plugin} ..." >&2; exit 64 ;;
esac
