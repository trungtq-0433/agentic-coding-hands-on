<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Pipeline: Waves W0 → W5
Loaded by orchestrator before W0–W5 dispatch. See `pipeline.md` for wave dep graph + incremental preamble.

> **Profile dispatch + canonical gates extracted.** The `profile` / `produce()` binding, Wave 0.6
> structural extraction, and the canonical **Renumber+Contiguity Gate** now live in
> [`pipeline-dispatch-and-gates.md`](pipeline-dispatch-and-gates.md). The orchestrator loads that file
> **alongside** this one before W0–W5 dispatch (see `SKILL.md` § On-demand pipeline loading). The task
> chain below references `produce()` and applies the canonical gate by name — both are defined there.

---

## Task chain pattern

> One continuous orchestration program (single variable scope). The `### Wave` sub-blocks below are
> navigation only — `profile`/`produce()` and the task-id chain (`scoutTaskId` → `w15Blocker` →
> `w2TaskIds`/`w3BlockedBy` → `permissionsTaskId` → `w45Blocker` → `featureListTaskId`) thread across
> them top to bottom. Do not load or execute a sub-block in isolation.

### Wave 0 — Scout dispatch

```
// Wave 0 — [GRAPHIFY-INTEGRATION] deterministic scout from the knowledge graph.
// If graphify-out/graph.json exists, FIRST generate the scout report for $0 (no LLM):
//   bash: .claude/skills/.venv/bin/python3 \
//     .claude/skills/rebuild-spec/scripts/graph_to_scout.py \
//     --graph graphify-out/graph.json --repo . \
//     --out plans/<active-plan>/artifacts/scout-report.md
// On exit 0: scout-report.md is contract-complete (File Inventory + BL inventory) —
//   create the Scout task and IMMEDIATELY TaskUpdate(status=completed) WITHOUT dispatching
//   any scout subagent (the 1-3M-token LLM scan is the single most expensive discovery step
//   and is fully replaced by the generator). Proceed straight to Wave 0.5.
// On non-zero exit (no graph / generator failed): dispatch the LLM scout below as usual.
//
// Also (best-effort, same condition) generate W1 starting drafts — structure-only skeletons
// that W1 researchers VERIFY & COMPLETE instead of building from scratch:
//   bash: .claude/skills/.venv/bin/python3 \
//     .claude/skills/rebuild-spec/scripts/graph_to_drafts.py \
//     --graph graphify-out/graph.json --outdir plans/<active-plan>/artifacts/_graph-drafts
// Failure here is non-fatal: researchers simply work from the templates as before.
TaskCreate({ subject: "Scout: discovery scan",
  description: "[GRAPHIFY-INTEGRATION] GRAPH-FIRST: If a file graphify-out/graph.json exists, FIRST read graphify-out/GRAPH_REPORT.md and use `graphify query`/`graphify explain` via Bash to map routes, data models, screens, background logic and their relationships, and build the ENTIRE scout-report (including the File Inventory) from the graph — do NOT cat/read source files one-by-one for discovery; use Read ONLY to confirm a specific detail the graph omits. If no graphify-out/graph.json exists, proceed with the textual scan below. Scan routing, data models, screens, bg logic, permissions. Detect project language from manifest (package.json → JS/TS; composer.json → PHP; Gemfile → Ruby; pyproject.toml → Python; pom.xml/build.gradle → Java; go.mod → Go; Cargo.toml → Rust). Scan all non-test, non-vendor source dirs relevant to the detected stack (e.g. pages/, views/, components/, features/, modules/ for JS/TS; app/Http/, resources/views/ for Laravel; app/controllers/, app/views/ for Rails; adapt accordingly). Multi-manifest rule: if multiple manifests coexist at root level (e.g. package.json + composer.json), the root-level manifest wins; priority order JS/TS > PHP > Ruby > Python > Java > Go > Rust if tied at same depth. Emit [MULTI_STACK] note in scout-report.md Notes section listing all detected stacks. For desktop/legacy stacks (Delphi/VCL): classify each .dfm by its ROOT-OBJECT kind, read from the first non-blank line `object <Name>: <BaseClass>` — TForm/descendant → tag `screen`, TFrame → tag `screen-embedded`, TDataModule → tag `datamodule` (+ trailing `[reachable]` token when it hosts a TActionList/TAction or report component). NEVER classify a .dfm by extension; a binary/unreadable .dfm → tag `screen [UNVERIFIED]` and flag for the researcher (do not guess). See the File Inventory type legend in scout-report-template.md. Output MUST follow templates/scout-report-template.md. File Inventory is the contract for Wave 2 content-completeness and Wave 7 reviewer cross-validation — every source file must appear. After File Inventory: emit `## Background Logic Source Inventory` section. To do this: (1) read references/bl-source-patterns.md; (2) for Mode A stacks apply the folder-convention globs for the detected stack row; (3) for Mode B stacks apply the annotation/decorator grep markers from bl-source-patterns.md § Mode B Grep Markers; (4) emit one entry per file (Mode A) or per decorator hit (Mode B) sorted by category then path; (5) for any category with no matches emit `_(none found)_`; (6) for stacks/libraries not in the table use [SIGNAL_INFERRED] protocol (see bl-source-patterns.md § Signal Inference Fallback); (7) for [MULTI_STACK] projects emit one subsection per detected stack. Output: plans/<active-plan>/artifacts/scout-report.md" })

```

### Wave 1 — SystemOverview · Architecture · DataModel · RouteList (deferred)

```
// Wave 1 — 4 tasks in parallel, each addBlockedBy: [scoutTaskId]
// In incremental mode, system-overview + architecture are NEVER in affected_waves — always use hydrated copy.
const sysOverviewTaskId = resolveWaveTaskId("Wave1: system-overview", () =>
  TaskCreate({ subject: "Wave1: system-overview",
    description: "Session context: read `plans/<active-plan>/artifacts/_session-context.md` FIRST.\nSynthesize SystemOverview. Template: system-overview-template.md. Schema: references/code-formats.md. Draft: plans/<active-plan>/artifacts/system-overview.md",
    addBlockedBy: [scoutTaskId] }))
const architectureTaskId = resolveWaveTaskId("Wave1: architecture", () =>
  TaskCreate({ subject: "Wave1: architecture",
    description: "Session context: read `plans/<active-plan>/artifacts/_session-context.md` FIRST.\nSynthesize Architecture (Mermaid diagrams + tech stack) from scout-report.md. If plans/<active-plan>/artifacts/_graph-drafts/architecture-draft.md exists, START from it (machine-true module/import graph) — verify it and complete ALL sections of the template; do not re-derive the module graph from scratch. Template: architecture-template.md. Draft: plans/<active-plan>/artifacts/architecture.md",
    addBlockedBy: [scoutTaskId] }))
// W1 route-list TaskCreate is deferred to after Wave 0.4 probe (below) so routeListProbeNote
// can be injected into the task description. Placeholder declared here for scoping.
var routeListTaskId  // assigned after Wave 0.4 block

// --- W1 data-model: pre-gen estimate gate (shard when >=40 models) ---
// Runs BEFORE creating the research task. Over threshold → chunked path.
// Read references/artifact-sharding.md for merge recipe + fragment contract.
const dmEstimate = JSON.parse(bash(`.claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/estimate_artifact_loc.py \
  --artifact data-model \
  --scout-report plans/<active-plan>/artifacts/scout-report.md \
  --plan-dir plans/<active-plan> \
  --max-loc ${docs_maxLoc ?? 800}`).stdout)
console.log(`[INFO] W1 data-model pre-gen estimate: ${dmEstimate.unit_count} models, shard=${dmEstimate.shard}`)

if (dmEstimate.shard) {
  // SHARD BRANCH: shell (preamble + MODEL### ranges + per-domain anchors) → fan-out → merge
  // Shell researcher writes skeleton with {POPULATED_BY_FRAGMENTS} per domain.
  // Fan-out researchers write entity blocks per assigned MODEL### range.
  // Merge: ls|sort → inject → rm -rf. Then W1.5 gate runs on merged file (UNCHANGED).
  // See references/artifact-sharding.md § Descriptor Table (data-model row).
  var dataModelTaskId = TaskCreate({ subject: "Wave1: data-model (shard: shell→fan-out→merge)",
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
SHARD MODE for DataModel (${dmEstimate.unit_count} models >= 40 threshold).
Read references/artifact-sharding.md for merge recipe + fragment contract.

1. Shell step: write data-model.md skeleton (preamble, ERD, Polymorphic/Discriminator anchors, per-domain {POPULATED_BY_FRAGMENTS} anchors). Assign disjoint MODEL### ranges per domain to _fragments/data-model/_slice-plan.json.
2. Fan-out: one researcher per domain (SEQUENTIAL BATCHES of REBUILD_SHARD_MAX_PARALLEL=5, batch i+1 only after ALL of batch i — counts toward the global 5-agent cap), each writes entity blocks using ONLY their assigned MODEL### range → _fragments/data-model/NN-<domain>.md.
3. Merge: ls|sort → inject per anchor → rm -rf.
Template: data-model-template.md. Draft: plans/<active-plan>/artifacts/data-model.md`,
    addBlockedBy: [scoutTaskId] })
} else {
  var dataModelTaskId = resolveWaveTaskId("Wave1: data-model", () =>
    TaskCreate({ subject: "Wave1: data-model",
      description: "Session context: read `plans/<active-plan>/artifacts/_session-context.md` FIRST.\nSynthesize DataModel. If plans/<active-plan>/artifacts/_graph-drafts/data-model-draft.md exists, START from it (machine-true class inventory: every class listed exists in code at the given file:line) — fill fields/types for every TO-VERIFY line by reading those files, and complete ALL sections of the template; do not re-derive the class list from scratch. Template: data-model-template.md. Draft: plans/<active-plan>/artifacts/data-model.md",
      addBlockedBy: [scoutTaskId] }))
}

// Extract detected stack from scout report (Wave 0 output, available at this point)
const scoutReportPath = `plans/<active-plan>/artifacts/scout-report.md`
const scoutContent = existsNonEmpty(scoutReportPath) ? readFile(scoutReportPath) : ''
const detectedLangMatch = scoutContent.match(/^## Detected Language\s*\n\s*(\S[^\n]*)/m)
const detectedStack = detectedLangMatch ? detectedLangMatch[1].trim() : 'JS/TS'
const isMultiStack = scoutContent.includes('[MULTI_STACK]')

// Enumerate every root-level manifest present so reviewer/researcher know exactly
// which stacks' signal rows to OR-merge in H-rule tables.
// Bare filenames are intentional — these manifests live at the repo root (CWD).
const manifestMap = {
  'package.json': 'JS/TS',
  'composer.json': 'PHP',
  'Gemfile': 'Ruby',
  'pyproject.toml': 'Python',
  'pom.xml': 'Java',
  'build.gradle': 'Java',
  'go.mod': 'Go',
  'Cargo.toml': 'Rust'
}
const uniqueFoundStacks = [...new Set(
  Object.entries(manifestMap)
    .filter(([file]) => existsNonEmpty(file))
    .map(([, stack]) => stack)
)]
let stackNote = detectedStack
if (isMultiStack) {
  stackNote = uniqueFoundStacks.length > 1
    ? `${detectedStack} [MULTI_STACK — all stacks: ${uniqueFoundStacks.join(', ')}; apply union of signals for all listed stacks in H-rule tables (consult each stack's row in every H-rule table; OR-merge signals before counting)]`
    : `${detectedStack} [MULTI_STACK — scout flagged multi-stack but root manifest scan found ${uniqueFoundStacks.length} stack(s); cannot enumerate union — emit [STACK_LIST_MISSING] advisory in classification justification per composite-screen-detection.md § Stack Probe]`
}

```

### Wave 0.4 — Route-probe gate

```
// Wave 0.4 — Route probe gate (runs before W1 dispatch, after scout data is in memory)
// Trigger: auto whenever a bootable stack + lister binary detected, OR explicit --probe-routes flag.
// Checkpoint: check probe_gate in .rebuild-state.json — if prior decision/manifest exists AND
// not --full → reuse sidecar, skip prompt entirely (Phase 05 persists the gate answer).
// --full re-prompts + re-probes fresh ONLY when hasBootableStack || explicitProbeRoutes.
const probeSidecarPath = `plans/<active-plan>/artifacts/_route-probe.json`
const priorProbeGate = readStateField("probe_gate") // null if no state or probe_gate key absent (legacy behavior)

// Resume-at-gate guard: if a prior run was halted at the bootability gate (user chose "Need to
// set up app first"), treat this run as a resume — re-issue the gate without re-running scout.
// Scout-report already exists on disk and is reused by the W1 route-list task via resolveWaveTaskId
// (which checks output-on-disk before creating a new task). The --artifact route-list standalone
// entry point also satisfies this path: resolveWaveTaskId hydrates scout-report from disk if
// present; no scout re-run is dispatched. NOTE: if scout-report is somehow absent on resume, the
// W1 task will ABORT per the --artifact upstream-missing guard — user must run a full rebuild.
const isResumingFromHalt = priorProbeGate?.status === "awaiting_user" && !flags.includes("--full")

// Determine bootable stacks using the same lockfile-presence logic as probe_routes.py
const bootableLockfiles = {
  'Gemfile.lock': 'rails',
  'composer.lock': 'laravel',
  // symfony also maps to composer.lock — both are emitted when that file is present.
  // probe_routes.py disambiguates: symfony requires bin/console (detect_binary); laravel
  // uses php artisan. A project with only artisan → laravel wins; only bin/console → symfony
  // wins; both → both attempted (graceful fallback to tier1_failed per missing entrypoint).
  'mix.lock': 'phoenix',
  // Django is NOT auto-detected via bootableLockfiles because manage.py is not a lockfile.
  // Django probes are only triggered via explicit --probe-routes flag. See _probe_routes_lib.py.
}
// Build bootable stack list. composer.lock → both laravel AND symfony are candidates;
// probe_routes.py disambiguates by entrypoint presence (artisan → laravel, bin/console → symfony).
const bootableFoundStacks = Object.entries(bootableLockfiles)
  .filter(([file]) => existsNonEmpty(file))
  .flatMap(([file, stack]) => {
    if (file === 'composer.lock') {
      const candidates = ['laravel']
      if (existsNonEmpty('bin/console')) candidates.push('symfony')
      return candidates
    }
    return [stack]
  })
  .filter((s, i, arr) => arr.indexOf(s) === i) // deduplicate
const hasBootableStack = bootableFoundStacks.length > 0
const explicitProbeRoutes = flags.includes("--probe-routes")

// v11.0.0 profile gate: a non-bootable profile (legacy non-web: Delphi/Oracle) skips Wave 0.4 entirely.
// profile.probe.bootable === false ⇒ no route-probe prompt, no Tier-1 probe, no sidecar.
if (profile.probe?.bootable === false) {
  console.log(`[SKIP] route-probe (profile ${profile.id}: probe.bootable=false)`)
}
// Enter the gate prompt if: profile is bootable AND ((a) resume from halt, OR (b) first-time trigger
// (bootable stack or explicit flag) AND no prior gate decision, OR (c) --full forces a fresh prompt).
else if (isResumingFromHalt || ((hasBootableStack || explicitProbeRoutes) && (!priorProbeGate || flags.includes("--full")))) {
  if (isResumingFromHalt) {
    console.log("[INFO] Wave 0.4 route probe: resuming from awaiting_user halt — re-issuing bootability gate (scout-report reused)")
  }
  // AskUserQuestion is ORCHESTRATOR-ONLY — spawned agents cannot call it.
  // Three-option modal: Yes (run probe) / No (skip to Tier 2) / Need setup (HALT + checkpoint).
  const bootAnswer = await AskUserQuestion({
    header: "Wave 0.4 — Route Probe: App Bootability",
    question: `Tier-1 CLI route probe detected bootable stack(s): ${bootableFoundStacks.join(", ") || "unknown"}.\n\nThe probe runs the framework's own route lister (e.g. bin/rails routes, php artisan route:list --json) to produce an authoritative route manifest. This requires the app to be bootable — dependencies installed, env configured.\n\nNo install commands are run. The probe is non-fatal: if it fails, the pipeline falls back to Tier-2 static parse.`,
    options: [
      {
        label: "Yes, app is bootable — run CLI probe",
        description: `Runs: ${bootableFoundStacks.map(s => ({rails:"bin/rails routes", laravel:"php artisan route:list --json", phoenix:"mix phx.routes", symfony:"php bin/console debug:router --format=json", django:"python manage.py show_urls"})[s] || s).join("; ")}. Writes route-manifest.json used by W1 route-list (authoritative, macros pre-expanded).`,
      },
      {
        label: "No / not sure — skip to Tier 2 (static parse)",
        description: "Route list will be inferred from source files. CLI probe skipped. W1 route-list uses Tier-2 static analysis only.",
      },
      {
        label: "Need to set up app first",
        description: "Pipeline halts with a checkpoint. Set up app deps locally (do NOT commit lockfile/dep churn), then re-run /tkm:rebuild-spec --artifact route-list to resume at this gate. Scout output is preserved — no re-scan needed.",
      },
    ],
  })

  if (bootAnswer.startsWith("Yes")) {
    // Run probe — exit 0 always (advisory), never halts pipeline on failure
    // stdout contract: probe_routes.py emits pure JSON (no preamble, no trailing text).
    // If JSON.parse fails (unexpected output), treat as tier1_failed — log and continue; NEVER halt.
    const probeResult = JSON.parse(bash(
      `.claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/probe_routes.py \
  --project-root . \
  --plan-dir plans/<active-plan> \
  --stacks "${bootableFoundStacks.join(",")}"`
    ).stdout)
    // Write sidecar (orchestrator owns this file — scout-report.md stays read-only)
    writeFile(probeSidecarPath, JSON.stringify(probeResult, null, 2))
    // Flip probe_gate to passed so a stale awaiting_user never blocks future runs
    writeStateField("probe_gate", {
      status: "passed",
      checkpoint_wave: "Wave1: route-list",
      probe_result: probeResult.status ?? "tier1_ok",
      manifest_path: probeResult.manifest_path ?? null,
    })
    console.log(`[INFO] Wave 0.4 route probe: status=${probeResult.status}, stacks=${probeResult.stacks_probed?.join(",") ?? "none"}`)
  } else if (bootAnswer.startsWith("No")) {
    // User declined — write skipped sidecar so W1 knows not to re-prompt
    writeFile(probeSidecarPath, JSON.stringify({ status: "skipped", manifest_path: null, stacks_probed: [] }, null, 2))
    // Flip probe_gate to skipped so a stale awaiting_user never blocks future runs
    writeStateField("probe_gate", {
      status: "skipped",
      checkpoint_wave: "Wave1: route-list",
      probe_result: "skipped",
      manifest_path: null,
    })
    console.log("[INFO] Wave 0.4 route probe: skipped by user — W1 will use Tier-2 static parse")
  } else {
    // User chose "Need to set up app first" — write checkpoint + HALT
    // WARNING: do NOT commit lockfile/dep churn from local setup to the repository.
    writeStateField("probe_gate", {
      status: "awaiting_user",
      checkpoint_wave: "Wave1: route-list",
      probe_result: null,
      manifest_path: null,
    })
    throw new Error(
      "HALT — set up app deps locally (do NOT commit lockfile/dep churn), " +
      "then re-run /tkm:rebuild-spec --artifact route-list to resume at the route probe gate."
    )
  }
} else if (priorProbeGate && !flags.includes("--full")) {
  // Incremental run with a prior decision: reuse sidecar, skip prompt entirely
  console.log(`[INFO] Wave 0.4 route probe: reusing prior gate (probe_gate.status=${priorProbeGate.status}) — use --full to re-probe`)
}

// Build W1 route-list task-description manifest injection
// If manifest present: W1 formats RouteList FROM the manifest (authoritative, macros expanded).
// If absent/skipped: W1 uses Tier-2 static parse only.
const probeManifestPath = existsNonEmpty(probeSidecarPath)
  ? JSON.parse(readFile(probeSidecarPath)).manifest_path
  : null
// Manifest JSON is a plain array normally; when the probe hit MAX_MANIFEST_ROUTES (5000)
// it is an object {routes: [...], truncated: true, total_routes: N} — the list is INCOMPLETE.
const probeManifest = probeManifestPath ? JSON.parse(readFile(probeManifestPath)) : null
const manifestTruncated = probeManifest && !Array.isArray(probeManifest) && probeManifest.truncated
const routeListProbeNote = probeManifestPath
  ? `Tier1 manifest: ${probeManifestPath} — format RouteList FROM this file (authoritative, macros already expanded). Do NOT invent. Tier2 static parse only for routes absent from manifest.`
    + (manifestTruncated
        ? ` WARNING: manifest TRUNCATED (${probeManifest.routes.length} of ${probeManifest.total_routes} routes) — you MUST supplement the missing routes via Tier-2 static parse of the route source files.`
        : ``)
  : `Tier2 static parse (no manifest — probe skipped or failed; infer routes from source files).`

// --- W1 route-list: pre-gen estimate gate (deferred here so routeListProbeNote is available) ---
// PROFILE GUARD (RT-F1): skip route-list dispatch entirely when the profile maps it to "skip"
// (legacy non-web stacks). Sentinel id is filtered from downstream addBlockedBy (SKIPPED: convention).
if (!produce("route-list")) {
  routeListTaskId = "SKIPPED:route-list (profile)"
  console.log(`[SKIP] route-list (profile ${profile.id})`)
} else {
// Shard by path prefix when est_loc > max_loc.
const rlEstimate = JSON.parse(bash(`.claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/estimate_artifact_loc.py \
  --artifact route-list \
  --scout-report plans/<active-plan>/artifacts/scout-report.md \
  --max-loc ${docs_maxLoc ?? 800}`).stdout)
console.log(`[INFO] W1 route-list pre-gen estimate: ${rlEstimate.unit_count} routes, est_loc=${rlEstimate.est_loc}, shard=${rlEstimate.shard}`)

if (rlEstimate.shard) {
  // SHARD BRANCH: shell (preamble + per-path-prefix anchors) → fan-out → merge.
  // Reuse same path-prefix slice logic as api-contracts resource namespace (DRY).
  routeListTaskId = TaskCreate({ subject: "Wave1: route-list (shard: shell→fan-out→merge)",
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
SHARD MODE for RouteList (${rlEstimate.unit_count} routes, est_loc=${rlEstimate.est_loc} > ${docs_maxLoc ?? 800}).
Read references/artifact-sharding.md for merge recipe + fragment contract.
${routeListProbeNote}

1. Shell: write route-list.md skeleton (preamble, ## Backend Routes header with table header row, per-path-prefix {POPULATED_BY_FRAGMENTS} anchors, ## Frontend Routes, ## Summary). Write _fragments/route-list/_slice-plan.json.
2. Fan-out: one researcher per path prefix (SEQUENTIAL BATCHES of REBUILD_SHARD_MAX_PARALLEL=5, batch i+1 only after ALL of batch i — counts toward the global 5-agent cap). Each writes table-body rows ONLY (no header row, no preamble) → _fragments/route-list/NN-<prefix>.md.
3. Merge: ls|sort → inject → rm -rf.
Template: route-list-template.md (read the Completeness Contract note under ## Backend Routes — emit one row per leaf route, expand all resource macros, no resource-summary tables or approximation markers). Draft: plans/<active-plan>/artifacts/route-list.md`,
    addBlockedBy: [scoutTaskId] })
} else {
  routeListTaskId = resolveWaveTaskId("Wave1: route-list", () =>
    TaskCreate({ subject: "Wave1: route-list",
      description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.\nSynthesize RouteList. Template: route-list-template.md (read the Completeness Contract note under ## Backend Routes — emit one row per leaf route, expand all resource macros, no resource-summary tables or approximation markers). Draft: plans/<active-plan>/artifacts/route-list.md\n${routeListProbeNote}`,
      addBlockedBy: [scoutTaskId] }))
}
} // end profile guard: route-list

```

### Wave 0.5 — Shared session-context emit

```
// Wave 0.5 — Emit shared session-context file (read by all W1-W9 subagents)
// v11.0.0: pass the resolved profile id + source encoding so subagents get the ## Source Encoding
// block, and so a profile-set run aborts (exit 2) rather than silently writing detectedStack=JS/TS (RT-F2).
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/build_session_context.py \
  --plan-dir plans/<active-plan> \
  --scout-report plans/<active-plan>/artifacts/scout-report.md \
  --stack-note "${stackNote}" \
  --profile-id "${profile.id}" \
  --encoding "${profile.source_encoding.primary}"

// Also extract BL inventory fragment for W7a (avoids loading full scout-report)
bash: .claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/extract_scout_section.py \
  --scout-report plans/<active-plan>/artifacts/scout-report.md \
  --section "Background Logic Source Inventory" \
  --out plans/<active-plan>/artifacts/_scout-bl-inventory.md

```

### Wave 1 gates — DataModel renumber · W1.5 structural · W1.1 route-list completeness

```
// --- W1 data-model: renumber + contiguity gate ---
// Runs after W1 data-model task completes, BEFORE W1.5 structural gate.
// Ensures MODEL### codes are contiguous before the W1.5 reviewer sees them.
// NOTE: --artifact run must NOT renumber (would diverge artifacts/ from docs/generated/).
{
  // F2: async-TaskCreate guard — TaskCreate returns before the agent writes the file.
  if (!existsNonEmpty("plans/<active-plan>/artifacts/data-model.md")) {
    throw new Error("W1 data-model HALT — data-model.md not written (async TaskCreate guard)")
  }
  if (fileContains("plans/<active-plan>/artifacts/data-model.md", "{POPULATED_BY_FRAGMENTS}")) {
    throw new Error("W1 data-model HALT — data-model.md still has {POPULATED_BY_FRAGMENTS} (partial merge)")
  }
  // Apply "Renumber+Contiguity Gate (canonical)" with artifact=data-model
  const isFull = mode === "full"
  if (isFull) {
    bash: .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/renumber_artifact_ids.py \
      --artifact data-model --plan-dir plans/<active-plan>
    bash: .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
      --artifact data-model --plan-dir plans/<active-plan> \
      --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
  } else {
    bash: .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
      --artifact data-model --plan-dir plans/<active-plan> --report-only \
      --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
    console.log("[INFO] W1 data-model renumber skipped (incremental: IDs frozen)")
  }
}

// --- Wave 1.5: DataModel structural gate (before W2 dispatch) ---
// Runs after W1 data-model task completes. Single reviewer, DataModel-scoped.
// W2 dispatches ONLY after W1.5 reports passed: true.
// Incremental: skip W1.5 if data-model.md not re-generated this run.

let w15TaskId = null
const w15_reran = mode === "full" || affected_waves.includes("Wave1: data-model")
if (w15_reran) {
  w15TaskId = TaskCreate({
    subject: "Wave1.5: data-model-review",
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

Fast structural review of DataModel ONLY — do NOT review other artifacts (that is Wave 7a's scope).

INPUT: plans/<active-plan>/artifacts/data-model.md

CHECKS (run all, report each separately):

**Check 1 — Entity completeness:**
- Each entity block has: name, description, at least one field with name+type
- Fail: entity with no fields, or entity with fields but no types documented

**Check 2 — DISC-### scope:**
- Each DISC-### entry in a discriminator table should have ≥2 enum values with DISTINCT behavioral outcomes
- DISC-### with only \`true\`/\`false\` values → critical (boolean flags belong in Business Rules)
- DISC-### with only 1 value → critical (not a discriminator, remove or expand)
- Cross-check: each DISC-### code references an actual entity field in the same entity block

**Check 3 — MODEL### uniqueness:**
- No duplicate MODEL### codes across the document
- Fail: MODEL001 appears in two different entity blocks

**Check 4 — DISC-### orphan check:**
- Each DISC-### code in the document is anchored to a specific entity's field
- Fail: DISC003 appears in Polymorphic section but no entity has a field mapped to DISC003

**Check 5 — Relationship completeness:**
- Each relationship entry has: source entity, target entity, cardinality
- Missing cardinality → warning

OUTPUT: plans/<active-plan>/artifacts/data-model-review.md

Use this exact frontmatter:
\`\`\`yaml
---
passed: true   # true = W2 can proceed; false = halt
issues: 0
warnings: 0
---
\`\`\`

Passed Checks: ONE LINE per check (\`✓ <check_name>\`). NO prose.

TOKEN BUDGET: Load data-model.md only — self-contained, no cross-artifact loading needed.`,
    addBlockedBy: [dataModelTaskId]
  })
} else {
  console.log("[INFO] W1.5 skipped — data-model not re-generated (incremental: prior DataModel carries forward)")
  w15TaskId = `SKIPPED:W1.5`
}

// Halt on W1.5 failure before W2 dispatch
if (w15TaskId && !w15TaskId.startsWith("SKIPPED:")) {
  if (!existsNonEmpty("plans/<active-plan>/artifacts/data-model-review.md")) {
    throw new Error("W1.5 HALT — gate output missing: data-model-review.md was not written. Check W1.5 task for errors.")
  }
  const w15Content = readFile("plans/<active-plan>/artifacts/data-model-review.md")
  const w15fm = parseFrontmatter(w15Content)
  if (w15fm.passed === "false" || w15fm.passed === false) {
    throw new Error(
      `W1.5 HALT — DataModel has ${w15fm.issues} critical issue(s). ` +
      `Fix data-model.md, then re-run Wave 1 (--artifact data-model) or restart from W1. ` +
      `Review: plans/<active-plan>/artifacts/data-model-review.md`
    )
  }
  console.log(`[INFO] W1.5 passed (issues: ${w15fm.issues ?? 0}, warnings: ${w15fm.warnings ?? 0})`)
}

const w15Blocker = (w15TaskId && !w15TaskId.startsWith("SKIPPED:")) ? w15TaskId : dataModelTaskId

// --- W1.1: RouteList completeness gate ---
// W2 dispatches ONLY after W1.1 passes. Await completion of routeListTaskId before evaluating this block.
// Mirrors the W1.5 halt-check pattern — a timing violation becomes a loud halt, not a silent pass.
// Incremental: skip if route-list was not re-generated this run.
// PROFILE GUARD (RT-F1): a profile that skips route-list runs no W1.1 gate.
const rl_reran = produce("route-list") && (mode === "full" || affected_waves.includes("Wave1: route-list"))
if (!produce("route-list")) {
  console.log(`[SKIP] W1.1 route-list gate (profile ${profile.id})`)
} else if (rl_reran) {
  if (!existsNonEmpty("plans/<active-plan>/artifacts/route-list.md")) {
    throw new Error("W1.1 HALT — route-list.md not on disk. The Wave1 route-list task has not completed; await its completion before running this gate.")
  }
  bash: .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/validate_route_list.py \
    --plan-dir plans/<active-plan> \
    --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json

  // exit 0 → status PASS or WARN → proceed to W2 dispatch
  // exit 1 → status FAIL → HALT pipeline; surface JSON issues to user; prompt fix; NO W2 dispatch
  // exit 2 → internal validator error → surface stderr; halt
} else {
  console.log("[INFO] W1.1 skipped — route-list not re-generated (incremental: prior validation carries forward)")
}

```

### Wave 2 — ScreenList · ScreenFlow · BehaviorLogic (threshold gate + shard)

```
// PROFILE GUARD (RT-F1, screen_source-aware v21.0.0) for Wave 2 screen artifacts.
// `produce("screen-list")` is now driven by the profile's `screen_source` (see pipeline-dispatch-
// and-gates.md): TRUE for any stack with a screen source — web (route-view) AND Delphi (dfm-form) —
// and FALSE only for screen_source:none (oracle-plsql, generic-source: no screens at all).
// When TRUE → run the W2 threshold gate + branches; the screen SOURCE differs by stack (see the
// stack-aware source note in the W2 task descriptions below). When FALSE → take the `else` branch
// at the end of this block: skip screen-list/screen-flow/W2a.1 entirely and dispatch behavior-logic
// (universal) directly. (Oracle PL/SQL logic surfaces there + in feature-list, never as a screen.)
if (produce("screen-list")) {
// Wave 2 — threshold gate: merge W2a+W2b for small projects
bash: screen_count=$(.claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/count_screen_files.py \
  --scout-report plans/<active-plan>/artifacts/scout-report.md)
const W2_MERGE_THRESHOLD = parseInt(process.env.REBUILD_W2_MERGE_THRESHOLD ?? '30')

if (screen_count < W2_MERGE_THRESHOLD) {
  // Small project: merge W2a+W2b into a single researcher task.
  // Check BOTH individual W2 subjects (planner never emits "combined-screen-bg").
  const needsW2 = mode === "full"
    || affected_waves.includes("Wave2: screen-list + screen-flow")
    || affected_waves.includes("Wave2: behavior-logic")
  const combinedW2TaskId = needsW2
    ? TaskCreate({ subject: "Wave2: combined-screen-bg",
      description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST (single source for shared session inputs).

Generate ScreenList + ScreenFlow + BehaviorLogic in a SINGLE session.
Templates: screen-list-template.md, screen-flow-template.md, behavior-logic-template.md.
Drafts: plans/<active-plan>/artifacts/.
Context: references/composite-screen-detection.md (H1-H6 rules), references/verification-checklist-core-artifacts.md (Composite Detection Rules + Failure Trap Assertions).
Detected stack: \${stackNote}.

EMIT ORDER: ScreenList FIRST (BL needs its service-call inventory), ScreenFlow second, BehaviorLogic last.
SCREEN SOURCE (stack-aware, v21.0.0) — branch on the profile's screen_source:
  • route-view (web): Route-first enumeration — cross-reference the RouteList artifact for screen URLs.
  • dfm-form (Delphi/VCL): there is NO RouteList. Enumerate screens from File-Inventory \`screen\`-tagged
    .dfm TForm units (TFrame=screen-embedded, TDataModule=datamodule are NOT screens). Source the nav map
    + reachability from the form-nav digest \`plans/<active-plan>/artifacts/_digest_extract_form_nav.json\`
    (forms[] + edges[]); a form with reach:unverified is listed and marked [UNVERIFIED], never dropped.
    Follow the STACK-AWARE SECTIONS directive in screen-list-template.md / screen-flow-template.md:
    OMIT web-only sections (Routes/URLs, Authentication Flow, Guard Logic, Deep-Link, Unsaved-Changes,
    Extraction Signatures); use the caller-based Invocation/Entry-form shape. Every screen + edge cites file:line.
  • cobol-screen (COBOL SCREEN SECTION + CICS BMS): there is NO RouteList. Enumerate screens from
    \`plans/<active-plan>/artifacts/_digest_extract_cobol_screen.json\` (screens[] — one entry per screen,
    each \`{screen, kind, reachable, entry_citation, flow_edges[], unverified, raw}\`; \`kind\` is
    \`screen-section\` or \`cics-bms\`, both may appear in one repo). Flow edges come from \`flow_edges[]\`
    directly (already file:line-cited, no separate join needed). Follow the STACK-AWARE SECTIONS directive
    (omit web-only sections; caller-based Invocation shape); a screen with \`unverified: true\` is listed
    and marked [UNVERIFIED], never dropped.
  • ui-sniff (Track D accept-path, generic unrecognized-stack fallback): there is NO RouteList. Enumerate
    screens from \`plans/<active-plan>/artifacts/_digest_extract_ui_sniff.json\` (same ScreenRec shape as
    cobol-screen above). EVERY entry is \`unverified: true\` by design — these are sniffed leads the user
    explicitly accepted, not extracted facts; render every row [UNVERIFIED], never claim confidence the
    digest doesn't have. Follow the STACK-AWARE SECTIONS directive (omit web-only sections).
Apply composite-screen detection unconditionally.
Import chain rule: follow imports one level deep using language-specific mechanism.
CARDINALITY CONTRACT: read behavior-logic-template.md § Cardinality Contract. Read scout-report.md § Background Logic Source Inventory for authoritative file list.
Schema: references/code-formats.md (canonical 10 BL types + Source File/Source Symbol field schema).`,
      addBlockedBy: [routeListTaskId, w15Blocker] })
    : `HYDRATED:Wave2: combined-screen-bg`
  var w2TaskIds = [combinedW2TaskId]

  // --- W2a.1 (combined path): ScreenList composite guard ---
  // On FAIL this gate halts the orchestrator before W3 dispatch (W3 TaskCreates below are never reached);
  // task-graph ordering itself comes from w2TaskIds (which contains combinedW2TaskId).
  // Await completion of combinedW2TaskId before evaluating this block.
  // Mirrors the W1.5 halt-check pattern — a timing violation becomes a loud halt, not a silent pass.
  // Skipped on incremental if not re-generated.
  const needsW2a1_combined = mode === "full"
    || affected_waves.includes("Wave2: screen-list + screen-flow")
    || affected_waves.includes("Wave2: behavior-logic")
  if (needsW2a1_combined) {
    // --- W2 combined: renumber + contiguity gate ---
    // Both screen-list and behavior-logic from the SAME completed combined task; no cross-task race.
    // Exception: run for EACH artifact in order (SCR renumber first so screen-flow sibling is consistent).
    {
      // F2: async-TaskCreate guard
      if (!existsNonEmpty("plans/<active-plan>/artifacts/screen-list.md")) {
        throw new Error("W2a.1 (combined) HALT — screen-list.md not on disk. Await completion of the combined W2 task before running this gate.")
      }
      if (fileContains("plans/<active-plan>/artifacts/screen-list.md", "{POPULATED_BY_FRAGMENTS}")) {
        throw new Error("W2a.1 (combined) HALT — screen-list.md still has {POPULATED_BY_FRAGMENTS} (partial merge)")
      }
      // Apply "Renumber+Contiguity Gate (canonical)" for screen-list THEN behavior-logic
      const isFull = mode === "full"
      if (isFull) {
        bash: .claude/skills/.venv/bin/python3 \
          claude/skills/rebuild-spec/scripts/renumber_artifact_ids.py \
          --artifact screen-list --plan-dir plans/<active-plan>
        bash: .claude/skills/.venv/bin/python3 \
          claude/skills/rebuild-spec/scripts/renumber_artifact_ids.py \
          --artifact behavior-logic --plan-dir plans/<active-plan>
        bash: .claude/skills/.venv/bin/python3 \
          claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
          --artifact screen-list --plan-dir plans/<active-plan> \
          --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
        bash: .claude/skills/.venv/bin/python3 \
          claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
          --artifact behavior-logic --plan-dir plans/<active-plan> \
          --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
      } else {
        bash: .claude/skills/.venv/bin/python3 \
          claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
          --artifact screen-list --plan-dir plans/<active-plan> --report-only \
          --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
        bash: .claude/skills/.venv/bin/python3 \
          claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
          --artifact behavior-logic --plan-dir plans/<active-plan> --report-only \
          --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
        console.log("[INFO] W2 combined renumber skipped (incremental: IDs frozen)")
      }
    }

    bash: .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/validate_screen_list.py \
      --plan-dir plans/<active-plan> \
      --screen-source "${profile.screen_source ?? 'route-view'}" \
      --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
    // exit 0 → PASS/WARN → proceed; exit 1 → FAIL → HALT; exit 2 → internal error → halt
  } else {
    console.log("[INFO] W2a.1 (combined) skipped — screen-list not re-generated (incremental: prior validation carries forward)")
  }
} else {
  // Large project: existing W2a + W2b split path

// --- W2a screen-list + screen-flow: pre-gen estimate gate ---
const slEstimate = JSON.parse(bash(`.claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/estimate_artifact_loc.py \
  --artifact screen-list \
  --scout-report plans/<active-plan>/artifacts/scout-report.md \
  --plan-dir plans/<active-plan> \
  --max-loc ${docs_maxLoc ?? 800}`).stdout)
const sfEstimate = JSON.parse(bash(`.claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/estimate_artifact_loc.py \
  --artifact screen-flow \
  --scout-report plans/<active-plan>/artifacts/scout-report.md \
  --plan-dir plans/<active-plan> \
  --max-loc ${docs_maxLoc ?? 800}`).stdout)
console.log(`[INFO] W2a pre-gen: screen-list=${slEstimate.unit_count} SCR shard=${slEstimate.shard}, screen-flow=${sfEstimate.unit_count} SCR shard=${sfEstimate.shard}`)

if (slEstimate.shard || sfEstimate.shard) {
  // SHARD BRANCH for W2a: shared SCR### module/route-group slice plan drives both.
  var screenListAndFlowTaskId = TaskCreate({ subject: "Wave2: screen-list + screen-flow (shard: shell→fan-out→merge)",
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
SHARD MODE for ScreenList+ScreenFlow (${slEstimate.unit_count} SCR, screen-list shard=${slEstimate.shard}, screen-flow shard=${sfEstimate.shard}).
SCREEN SOURCE (stack-aware, v21.0.0): route-view → slice by module/route-group keyed on RouteList. dfm-form (Delphi) → there is NO RouteList; slice by .dfm \`screen\`-tagged TForm units, source nav/reachability from _digest_extract_form_nav.json, and follow the STACK-AWARE SECTIONS directive in screen-list-template.md/screen-flow-template.md (omit web-only sections; caller-based Invocation shape; cite file:line; reach:unverified → [UNVERIFIED], never dropped). cobol-screen (COBOL) → there is NO RouteList; slice by the screens[] entries in _digest_extract_cobol_screen.json (kind: screen-section or cics-bms), flow edges come from each entry's flow_edges[] directly; same STACK-AWARE SECTIONS/unverified handling. ui-sniff (Track D fallback) → there is NO RouteList; slice by the screens[] entries in _digest_extract_ui_sniff.json (same shape); EVERY entry is unverified: true by design, render every row [UNVERIFIED].
Read references/artifact-sharding.md for merge recipe.

1. Shell: compute ONE module/route-group slice plan (keyed by SCR###) shared by both. Write screen-list.md + screen-flow.md skeletons with per-module {POPULATED_BY_FRAGMENTS} anchors. Write _fragments/screen-list/_slice-plan.json and _fragments/screen-flow/_slice-plan.json.
2. Fan-out: one researcher per module (SEQUENTIAL BATCHES of REBUILD_SHARD_MAX_PARALLEL=5, batch i+1 only after ALL of batch i — counts toward the global 5-agent cap). Each writes SCR+REG blocks for screen-list AND flow blocks for screen-flow within their module. SCR+child REGs always co-located.
3. Merge screen-list: ls|sort → inject per module → rm -rf. Merge screen-flow same pattern.
Templates: screen-list-template.md, screen-flow-template.md. Context: composite-screen-detection.md. Detected stack: ${stackNote}.`,
    addBlockedBy: [routeListTaskId, w15Blocker] })
} else {
  // Wave 2a — ScreenList runs first (single-task, unchanged)
  var screenListAndFlowTaskId = resolveWaveTaskId("Wave2: screen-list + screen-flow", () =>
    TaskCreate({ subject: "Wave2: screen-list + screen-flow",
      description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Generate ScreenList + ScreenFlow. Templates: screen-list-template.md, screen-flow-template.md. Drafts: plans/<active-plan>/artifacts/. Context: references/composite-screen-detection.md (H1-H6 rules — read this file before classifying any screen), references/verification-checklist-core-artifacts.md (Composite Detection Rules + Failure Trap Assertions). Detected stack: ${stackNote} — pre-extracted from scout-report.md § ## Detected Language by the orchestrator; use this for per-stack signal selection in H-rule tables, do not re-read scout-report.md for stack detection. SCREEN SOURCE (stack-aware, v21.0.0) — FIRST resolve the profile's screen_source, then follow EXACTLY ONE of the four enumeration branches; never run more than one:
  • BRANCH dfm-form (Delphi, screen_source=dfm-form): there is NO RouteList. Enumerate screens from .dfm \`screen\`-tagged TForm units (TFrame/TDataModule are NOT screens); source the nav map + reachability from _digest_extract_form_nav.json; follow the STACK-AWARE SECTIONS directive in the screen-list/screen-flow templates (omit web-only sections; caller-based Invocation shape; cite file:line; reach:unverified → [UNVERIFIED], never dropped). DO NOT read or reference RouteList — it does not exist for this stack. Then apply H1-H6 over the enumerated forms and skip the other BRANCH paragraphs entirely.
  • BRANCH cobol-screen (COBOL, screen_source=cobol-screen): there is NO RouteList. Enumerate screens directly from \`plans/<active-plan>/artifacts/_digest_extract_cobol_screen.json\` (screens[] — one entry per screen, \`{screen, kind, reachable, entry_citation, flow_edges[], unverified, raw}\`; \`kind\` is \`screen-section\` or \`cics-bms\`, both may coexist in one repo). Flow edges come from each entry's \`flow_edges[]\` directly (already file:line-cited — no separate join/H-rule pass needed to establish reachability, the digest already resolved it). Follow the STACK-AWARE SECTIONS directive (omit web-only sections; caller-based Invocation shape); reach:unverified → [UNVERIFIED], never dropped. DO NOT read or reference RouteList. Skip the other BRANCH paragraphs entirely.
  • BRANCH ui-sniff (Track D fallback, screen_source=ui-sniff): there is NO RouteList. Enumerate screens directly from \`plans/<active-plan>/artifacts/_digest_extract_ui_sniff.json\` (same ScreenRec shape as cobol-screen above). EVERY entry is \`unverified: true\` by design — these are sniffed leads the user explicitly accepted, not extracted facts; render every row [UNVERIFIED], never claim confidence the digest doesn't carry. Follow the STACK-AWARE SECTIONS directive (omit web-only sections). DO NOT read or reference RouteList. Skip the other BRANCH paragraphs entirely.
  • BRANCH route-view (web, screen_source=route-view): Route-first enumeration — before applying H-rules, cross-reference the RouteList artifact (Wave 1, already complete). Map each distinct URL pattern to its page/component file. Each file serving a distinct URL path = one SCR candidate. Multiple URL patterns mapping to the SAME file = same SCR. Different files → separate SCR candidates. Then apply H1-H6 (full execution order: H6 → H4 → H5 → H2 → H3 → H1 → 2-of-3 gate) within each candidate. Apply composite-screen detection unconditionally to every screen file per references/composite-screen-detection.md. Import chain rule: if scout-report.md exists, use its flat file inventory to identify screen files (do not re-glob); if absent (e.g. --artifact entry point), emit [WARN] scout-report.md not found — skip content-completeness check and mark service coverage N/A. When scout-report exists: (1) resolve path aliases first (read tsconfig.json paths or package.json workspaces — unresolvable → treat as compliant, log [UNRESOLVED_ALIAS]); (2) follow imports one level deep using language-specific mechanism (ES6 import for JS/TS; use/require for PHP; require for Ruby; import for Python; import for Java/Kotlin/Go; use for Rust); (3) extract all service calls, API hooks, and helper functions in those immediate imports; (4) Known Limitation: barrel/re-export files (e.g. index.ts) re-exporting service modules at depth 2 are not followed — flag screens importing ONLY barrel files as [BARREL_IMPORT] advisory. The extracted service-call inventory is consumed by BehaviorLogic (Wave 2b) and confirms RouteList coverage.`,
      addBlockedBy: [routeListTaskId, w15Blocker] }))
}

// --- W2a.1: ScreenList composite guard (large-project path) ---
// W2b dispatches ONLY after W2a.1 passes. Await completion of screenListAndFlowTaskId before evaluating this block.
// Mirrors the W1.5 halt-check pattern — a timing violation becomes a loud halt, not a silent pass.
// Skipped on incremental if not re-generated.
const sl_reran = mode === "full" || affected_waves.includes("Wave2: screen-list + screen-flow")
if (sl_reran) {
  // --- W2a screen-list: renumber + contiguity gate ---
  {
    // F2: async-TaskCreate guard
    if (!existsNonEmpty("plans/<active-plan>/artifacts/screen-list.md")) {
      throw new Error("W2a.1 HALT — screen-list.md not on disk. Await completion of screenListAndFlowTaskId before running this gate.")
    }
    if (fileContains("plans/<active-plan>/artifacts/screen-list.md", "{POPULATED_BY_FRAGMENTS}")) {
      throw new Error("W2a.1 HALT — screen-list.md still has {POPULATED_BY_FRAGMENTS} (partial merge)")
    }
    // Apply "Renumber+Contiguity Gate (canonical)" with artifact=screen-list
    const isFull = mode === "full"
    if (isFull) {
      bash: .claude/skills/.venv/bin/python3 \
        claude/skills/rebuild-spec/scripts/renumber_artifact_ids.py \
        --artifact screen-list --plan-dir plans/<active-plan>
      bash: .claude/skills/.venv/bin/python3 \
        claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
        --artifact screen-list --plan-dir plans/<active-plan> \
        --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
    } else {
      bash: .claude/skills/.venv/bin/python3 \
        claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
        --artifact screen-list --plan-dir plans/<active-plan> --report-only \
        --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
      console.log("[INFO] W2a screen-list renumber skipped (incremental: IDs frozen)")
    }
  }

  bash: .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/validate_screen_list.py \
    --plan-dir plans/<active-plan> \
    --screen-source "${profile.screen_source ?? 'route-view'}" \
    --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
  // exit 0 → status PASS or WARN → proceed to W2b dispatch
  // exit 1 → status FAIL (e.g. ScreenList.no_wildcard_route critical) → HALT pipeline; surface JSON issues to user; prompt fix; NO W2b dispatch
  // exit 2 → internal validator error → surface stderr; halt
} else {
  console.log("[INFO] W2a.1 (large-project) skipped — screen-list not re-generated (incremental: prior validation carries forward)")
}

// --- W2b behavior-logic: pre-gen estimate gate ---
const blEstimate = JSON.parse(bash(`.claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/estimate_artifact_loc.py \
  --artifact behavior-logic \
  --scout-report plans/<active-plan>/artifacts/scout-report.md \
  --plan-dir plans/<active-plan> \
  --max-loc ${docs_maxLoc ?? 800}`).stdout)
console.log(`[INFO] W2b behavior-logic pre-gen estimate: ${blEstimate.unit_count} BL, shard=${blEstimate.shard}`)

if (blEstimate.shard) {
  // SHARD BRANCH for W2b: shell (preamble + per-category anchors) → fan-out → merge.
  // 1-BL-per-inventory-entry cardinality preserved (fragments are disjoint by source file).
  // validate_behavior_logic.py wired into W2b/W7a review.
  var behaviorLogicTaskId = TaskCreate({ subject: "Wave2: behavior-logic (shard: shell→fan-out→merge)",
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
SHARD MODE for BehaviorLogic (${blEstimate.unit_count} BL, est_loc=${blEstimate.est_loc} > ${docs_maxLoc ?? 800}).
Read references/artifact-sharding.md for merge recipe.

1. Shell: write behavior-logic.md skeleton (preamble, Index table, per-category {POPULATED_BY_FRAGMENTS} anchors). Write _fragments/behavior-logic/_slice-plan.json grouping BL inventory entries by category.
2. Fan-out: one researcher per category (SEQUENTIAL BATCHES of REBUILD_SHARD_MAX_PARALLEL=5, batch i+1 only after ALL of batch i — counts toward the global 5-agent cap). Each writes ## BL### blocks for their category, honoring 1-BL-per-inventory-entry (Rule C1). → _fragments/behavior-logic/NN-<category>.md.
3. Merge: ls|sort → inject per category → rm -rf. Coverage check: every scout BL inventory entry → exactly one BL.
Template: behavior-logic-template.md. Schema: references/code-formats.md.`,
    addBlockedBy: [screenListAndFlowTaskId] })
} else {
  var behaviorLogicTaskId = resolveWaveTaskId("Wave2: behavior-logic", () =>
    TaskCreate({ subject: "Wave2: behavior-logic",
      description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Generate BehaviorLogic. Template: behavior-logic-template.md. Schema: references/code-formats.md (canonical 10 BL types + Source File/Source Symbol field schema). Context: screen-list.md (service-call references extracted by Wave 2a). CARDINALITY CONTRACT (read template § Cardinality Contract before writing any BL item): (1) Read scout-report.md § Background Logic Source Inventory — this is the authoritative file list; (2) For each inventory entry emit exactly 1 BL item (Mode A: 1 file = 1 BL; Mode B: 1 decorator hit = 1 BL; multiple hits in same file = multiple BL items); (2a) Sentinel handling — entries shaped \`- {category}: _(none found)_\` (value field is the sentinel) are scout markers for empty categories; SKIP them, never emit a BL; (3) Set Source File = inventory entry path and Source Symbol = class or method name (single symbol only — see template Rule C2 for forbidden multi-symbol delimiters); (4) Aggregation is a critical violation — do NOT combine multiple source files into one BL item; (5) For per-stack signal context (what counts as each BL type per stack) read references/bl-source-patterns.md. Draft: plans/<active-plan>/artifacts/behavior-logic.md`,
      addBlockedBy: [screenListAndFlowTaskId] }))
}

  var w2TaskIds = [screenListAndFlowTaskId, behaviorLogicTaskId]

  // --- W2b behavior-logic: renumber + contiguity gate ---
  // Runs after W2b behavior-logic task completes (large-project split path only). BEFORE W3 dispatch.
  {
    // F2: async-TaskCreate guard
    if (!existsNonEmpty("plans/<active-plan>/artifacts/behavior-logic.md")) {
      throw new Error("W2b HALT — behavior-logic.md not written (async TaskCreate guard)")
    }
    if (fileContains("plans/<active-plan>/artifacts/behavior-logic.md", "{POPULATED_BY_FRAGMENTS}")) {
      throw new Error("W2b HALT — behavior-logic.md still has {POPULATED_BY_FRAGMENTS} (partial merge)")
    }
    // Apply "Renumber+Contiguity Gate (canonical)" with artifact=behavior-logic
    const isFull = mode === "full"
    if (isFull) {
      bash: .claude/skills/.venv/bin/python3 \
        claude/skills/rebuild-spec/scripts/renumber_artifact_ids.py \
        --artifact behavior-logic --plan-dir plans/<active-plan>
      bash: .claude/skills/.venv/bin/python3 \
        claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
        --artifact behavior-logic --plan-dir plans/<active-plan> \
        --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
    } else {
      bash: .claude/skills/.venv/bin/python3 \
        claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
        --artifact behavior-logic --plan-dir plans/<active-plan> --report-only \
        --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
      console.log("[INFO] W2b behavior-logic renumber skipped (incremental: IDs frozen)")
    }
  }
} // end W2 threshold gate (produce("screen-list") branch)
else {
  // PROFILE GUARD (RT-F1): legacy non-web profile skips screen-list/screen-flow + W2a.1 entirely.
  var screenListAndFlowTaskId = "SKIPPED:screen-list+flow (profile)"
  console.log(`[SKIP] screen-list (profile ${profile.id})`)
  console.log(`[SKIP] screen-flow (profile ${profile.id})`)
  console.log(`[SKIP] W2a.1 composite guard (profile ${profile.id})`)
  // behavior-logic is universal — STILL produced. It normally blocks on the screen task; here it
  // blocks on w15Blocker (data-model gate) instead, since there is no screen task to wait on.
  // Reuse the same pre-gen estimate + shard logic as the produce path (behavior-logic only).
  const blEstimate = JSON.parse(bash(`.claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/estimate_artifact_loc.py \
    --artifact behavior-logic \
    --scout-report plans/<active-plan>/artifacts/scout-report.md \
    --plan-dir plans/<active-plan> \
    --max-loc ${docs_maxLoc ?? 800}`).stdout)
  var behaviorLogicTaskId = blEstimate.shard
    ? TaskCreate({ subject: "Wave2: behavior-logic (shard: shell→fan-out→merge)",
        description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
SHARD MODE for BehaviorLogic (${blEstimate.unit_count} BL). Read references/artifact-sharding.md.
Template: behavior-logic-template.md. Schema: references/code-formats.md. Draft: plans/<active-plan>/artifacts/behavior-logic.md`,
        addBlockedBy: [w15Blocker] })
    : resolveWaveTaskId("Wave2: behavior-logic", () =>
        TaskCreate({ subject: "Wave2: behavior-logic",
          description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Generate BehaviorLogic (no screen-list upstream — read scout-report.md § Background Logic Source Inventory directly). Template: behavior-logic-template.md. Schema: references/code-formats.md. Draft: plans/<active-plan>/artifacts/behavior-logic.md`,
          addBlockedBy: [w15Blocker] }))
  var w2TaskIds = [behaviorLogicTaskId]
  // W2b behavior-logic renumber + contiguity gate (same as produce path; guard on async write).
  if (!existsNonEmpty("plans/<active-plan>/artifacts/behavior-logic.md"))
    throw new Error("W2b HALT — behavior-logic.md not written (async TaskCreate guard)")
  const isFull = mode === "full"
  if (isFull) {
    bash: .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/renumber_artifact_ids.py \
      --artifact behavior-logic --plan-dir plans/<active-plan>
    bash: .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
      --artifact behavior-logic --plan-dir plans/<active-plan> \
      --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
  }
}

// W2.5 (ScreenSpec fan-out) removed from main pipeline (2026-05-25).
// Use /rebuild-spec --screen-specs for standalone ScreenSpec pass after main rebuild.
// See ## Screen-Specs Pass section at end of this file.

```

### Wave 2.9 — ApiMap

```
// --- W2.9 api-map: pre-gen estimate gate ---
// PROFILE GUARD (RT-F1): a profile that maps api-map to "skip" (legacy non-web) skips this whole
// block — no estimate (route-list.md would not exist), no TaskCreate. Sentinel filtered downstream.
var apiMapTaskId
if (!produce("api-map")) {
  apiMapTaskId = "SKIPPED:api-map (profile)"
  console.log(`[SKIP] api-map (profile ${profile.id})`)
} else {
const amEstimate = JSON.parse(bash(`.claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/estimate_artifact_loc.py \
  --artifact api-map \
  --route-list plans/<active-plan>/artifacts/route-list.md \
  --max-loc ${docs_maxLoc ?? 800}`).stdout)
console.log(`[INFO] W2.9 api-map pre-gen estimate: ${amEstimate.unit_count} endpoints, shard=${amEstimate.shard}`)

if (amEstimate.shard) {
  // SHARD BRANCH: shell (preamble + per-namespace anchors) → fan-out → merge.
  // Same namespace slice key as route-list/api-contracts (DRY). validate_api_map.py wired into W2.9 review.
  apiMapTaskId = TaskCreate({ subject: "Wave2.9: api-map (shard: shell→fan-out→merge)",
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
SHARD MODE for ApiMap (${amEstimate.unit_count} endpoints, est_loc=${amEstimate.est_loc} > ${docs_maxLoc ?? 800}).
Read references/artifact-sharding.md for merge recipe.

1. Shell: write api-map.md skeleton (## Endpoints by Domain header, per-namespace ### headers with {POPULATED_BY_FRAGMENTS} anchors, ## Background Jobs, ## Webhooks). Write _fragments/api-map/_slice-plan.json.
2. Fan-out: one researcher per namespace (SEQUENTIAL BATCHES of REBUILD_SHARD_MAX_PARALLEL=5, batch i+1 only after ALL of batch i — counts toward the global 5-agent cap). Each writes endpoint→handler table rows ONLY → _fragments/api-map/NN-<namespace>.md.
3. Merge: ls|sort → inject per namespace → rm -rf.
Inputs: route-list.md + behavior-logic.md. Output: plans/<active-plan>/artifacts/api-map.md`,
    addBlockedBy: w2TaskIds })
} else {
  apiMapTaskId = resolveWaveTaskId("Wave2.9: api-map", () =>
    TaskCreate({ subject: "Wave2.9: api-map",
      description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

Synthesize ApiMap from route-list.md + behavior-logic.md.
Output: plans/<active-plan>/artifacts/api-map.md

FORMAT:
## API Map

Group routes by domain/resource (e.g. Auth, Users, Posts). For each route:
- Method + path (from route-list.md)
- BL### codes that handle it (from behavior-logic.md § Source Symbol)
- Auth/permission requirement (PERM### or "public")

Use a table per group:
| Method | Path | Handler BL### | Auth |
|--------|------|---------------|------|

Omit routes with no matching BL entry — mark them [UNMAPPED].
Call TaskUpdate(status=completed) on this task id BEFORE returning.`,
      addBlockedBy: w2TaskIds }))
}
} // end profile guard: api-map

```

### Wave 1.b / 1.c — Extractor-digest artifacts (crud-matrix · db-objects)

```
// --- W1.b / W1.c: extractor-digest-derived artifacts (v11.1.0) ---
// Dispatched when the profile maps them to produce (stack-specific: Delphi/Oracle). They read the
// Wave 0.6 digests, NOT other waves — so they only depend on Wave 0.6 completion (digest on disk).

// RT-F11 stale-digest gate (deterministic, before dispatch): recompute the source tree hash and
// compare to the digest's; mismatch → the digest predates current source → WARN (advisory, re-run 0.6).
function digestStale(extractor, globsJson) {
  return bash(`.claude/skills/.venv/bin/python3 - <<'PY'
import json, sys
sys.path.insert(0, "claude/skills/rebuild-spec/scripts")
from pathlib import Path
from _extractor_lib import source_tree_hash
p = Path("plans/<active-plan>/artifacts/_digest_${extractor}.json")
if not p.is_file(): print("missing"); raise SystemExit
d = json.load(open(p))
cur = source_tree_hash(Path("."), ${globsJson})
print("stale" if d.get("source_tree_hash") != cur else "fresh")
PY`).stdout.trim()
}
{
  const s = digestStale("extract_data_flow", JSON.stringify(["*.pas","*.sql","*.pks","*.pkb"]))
  if (s === "stale") console.warn("[WARN] stale_digest: extract_data_flow digest older than source — re-run Wave 0.6")
  if (s === "missing") console.warn("[WARN] missing_digest: extract_data_flow — Wave 0.6 did not run")
}

if (produce("crud-matrix")) {
  // Pre-gen estimate from the data-flow digest (shard by F### range — RT-DOC-b; Cross-Module post-merge).
  const cmEstimate = JSON.parse(bash(`.claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/estimate_artifact_loc.py \
    --artifact crud-matrix --plan-dir plans/<active-plan> --max-loc ${docs_maxLoc ?? 800}`).stdout)
  var crudMatrixTaskId = TaskCreate({ subject: "Wave1.b: crud-matrix",
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Write docs/generated/crud-matrix.md FROM \`plans/<active-plan>/artifacts/_digest_extract_data_flow.json\`
(feature×table C/R/U/D + columns + Cross-Module section). EVERY cell citation-bound; carry [UNVERIFIED]
for db_ops with confidence=low / unverified=true. Do NOT invent ops absent from the digest. shard=${cmEstimate.shard} (by F### range; Cross-Module built post-merge).
Template: templates/crud-matrix-template.md. Then the orchestrator runs validate_crud_matrix.py (exit 1 → HALT).`,
    addBlockedBy: [scoutTaskId] })
  // Gate: bash validate_crud_matrix.py --plan-dir plans/<active-plan> --summary-out .../validation-summary.json
} else { console.log(`[SKIP] crud-matrix (profile ${profile.id})`) }

if (produce("db-objects")) {
  // Chained behind Wave1.b, not scout: with crud-matrix + db-objects both produced (legacy profiles),
  // 6 tasks blocked on scoutTaskId would exceed the global 5-agent cap (SKILL.md § GLOBAL PARALLEL CAP).
  // Chaining db-objects behind crud-matrix holds the core-pass antichain at ≤5.
  // ⚠ MAINTENANCE: legacy profiles now sit at EXACTLY 5/5 (overview, architecture, data-model,
  // route-list, crud-matrix|db-objects) — ZERO headroom. Any NEW Wave-1 artifact task must be
  // chained into this Wave1.b→1.c chain (or behind another Wave-1 task), never added as a
  // seventh sibling on scoutTaskId, or the cap breaks again.
  var dbObjectsTaskId = TaskCreate({ subject: "Wave1.c: db-objects",
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Write docs/generated/db-objects.md FROM \`plans/<active-plan>/artifacts/_digest_extract_sql_schema.json\`
(tables/views/stored-procs/sequences/triggers + purpose-from-evidence + citation). Do NOT invent objects.
Template: templates/db-object-catalog-template.md. Then the orchestrator runs validate_db_catalog.py (exit 1 → HALT).`,
    addBlockedBy: [crudMatrixTaskId ?? scoutTaskId] })
  // Gate: bash validate_db_catalog.py --plan-dir plans/<active-plan> --summary-out .../validation-summary.json
} else { console.log(`[SKIP] db-objects (profile ${profile.id})`) }

```

**Shared-DB attribution (v22.0.0 — multi-component runs only).** When a per-component `--batch --root
PG/<MODULE>` run executes inside a multi-executable repo whose `component_profile` declares a `DB` shared
layer, the component's OWN digest holds no DB objects (they live in the sibling `DB/<TYPE>/<MODULE>/` tree
scanned ONCE by the Step 0.4 pre-pass). The db-objects / crud-matrix authoring step therefore ALSO consumes
the per-component **FILTERED shared-DB view** — `_shared_attribution_lib.filter_shared_digest_by_label`
keeps only objects whose citation carries the `<MODULE>` segment (full-segment equality, `POS` ≠ `POSDEN`).
The view is already attributed — **do NOT re-filter**. A component with no matching DB segment → empty
db-objects + `[UNVERIFIED]`. Common is referenced by pointer from the shared dataflow digest, never
re-scanned. Single-repo runs are unaffected (no shared layer → no filtered view). See
`references/multi-component-runbook.md` → "Shared-layer pre-pass + attribution".

### Wave 3 — Permissions (matrix · curated · business-rules)

```
// Wave 3 — blocks on W2b BehaviorLogic only (api-map runs in parallel, does not block W3)
const w3BlockedBy = w2TaskIds

const permissionsTaskId = resolveWaveTaskId("Wave3: permissions", () =>
  TaskCreate({ subject: "Wave3: permissions",
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Generate Permissions.

TRIPLE OUTPUT (order matters — write matrix FIRST, then derive curated from it):
1. permissions-matrix.md → plans/<active-plan>/artifacts/permissions-matrix.md
   RAW PERM### matrix + client-side gates. Template: templates/permissions-matrix-template.md
2. permissions.md → plans/<active-plan>/artifacts/permissions.md
   Plain-language CURATED view (who can do what). No PERM### codes, no matrix tables.
   Derive prose FROM permissions-matrix.md (roles → plain sentences). Template: templates/permissions-template.md
3. business-rules.md (DRAFT) → plans/<active-plan>/artifacts/business-rules.md
   Plain-language summary of behavior-logic BR codes. No PERM### or BL### codes.
   Template: templates/business-rules-template.md`,
    addBlockedBy: w3BlockedBy }))

// --- W3 permissions-matrix: renumber + contiguity gate ---
// Runs after W3 permissions task completes. BEFORE W4 user-stories dispatch.
{
  // F2: async-TaskCreate guard
  if (!existsNonEmpty("plans/<active-plan>/artifacts/permissions-matrix.md")) {
    throw new Error("W3 permissions-matrix HALT — permissions-matrix.md not written (async TaskCreate guard)")
  }
  if (fileContains("plans/<active-plan>/artifacts/permissions-matrix.md", "{POPULATED_BY_FRAGMENTS}")) {
    throw new Error("W3 permissions-matrix HALT — permissions-matrix.md still has {POPULATED_BY_FRAGMENTS} (partial merge)")
  }
  // Apply "Renumber+Contiguity Gate (canonical)" with artifact=permissions-matrix
  const isFull = mode === "full"
  if (isFull) {
    bash: .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/renumber_artifact_ids.py \
      --artifact permissions-matrix --plan-dir plans/<active-plan>
    bash: .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
      --artifact permissions-matrix --plan-dir plans/<active-plan> \
      --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
  } else {
    bash: .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
      --artifact permissions-matrix --plan-dir plans/<active-plan> --report-only \
      --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
    console.log("[INFO] W3 permissions-matrix renumber skipped (incremental: IDs frozen)")
  }
}

```

### Wave 4 — UserStories (+ W4.5 quality gate)

```
// --- W4 user-stories: pre-gen estimate gate (shard by actor when est_loc > max_loc) ---
const usEstimate = JSON.parse(bash(`.claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/estimate_artifact_loc.py \
  --artifact user-stories \
  --plan-dir plans/<active-plan> \
  --max-loc ${docs_maxLoc ?? 800}`).stdout)
console.log(`[INFO] W4 user-stories pre-gen estimate: ${usEstimate.unit_count} US, est_loc=${usEstimate.est_loc}, shard=${usEstimate.shard}`)

if (usEstimate.shard) {
  // SHARD BRANCH: shell (US### range pre-alloc per actor) → fan-out → merge → W4.5 gate UNCHANGED.
  // See references/artifact-sharding.md § US### Range Pre-allocation Algorithm.
  const usRanges = JSON.parse(bash(`.claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/estimate_artifact_loc.py \
    --artifact user-stories --emit-ranges \
    --permissions-matrix plans/<active-plan>/artifacts/permissions-matrix.md`).stdout)
  console.log(`[INFO] W4 shard: ${usRanges.ranges.length} actor ranges allocated`)

  var userStoriesTaskId = TaskCreate({ subject: "Wave4: user-stories (shard: shell→fan-out→merge)",
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
SHARD MODE for UserStories (${usEstimate.unit_count} US, est_loc=${usEstimate.est_loc} > ${docs_maxLoc ?? 800}).
Read references/artifact-sharding.md for merge recipe + US### range pre-allocation.

1. Shell step: write user-stories.md skeleton (preamble, Interaction Inventory, User Story Index, per-actor {POPULATED_BY_FRAGMENTS} anchors, Screen→US Map, Cross-Reference). Write _fragments/user-stories/_slice-plan.json with per-actor US### ranges: ${JSON.stringify(usRanges.ranges)}.
2. Fan-out: one researcher per actor (SEQUENTIAL BATCHES of REBUILD_SHARD_MAX_PARALLEL=5, batch i+1 only after ALL of batch i — counts toward the global 5-agent cap). Each writes US blocks using ONLY their assigned US### range. If range exceeded: STOP and report.
3. Merge: ls|sort → inject per actor anchor → rm -rf.
Load: references/user-stories-ipe-protocol.md. Template: user-stories-template.md.
Draft: plans/<active-plan>/artifacts/user-stories.md`,
    addBlockedBy: [permissionsTaskId] })
} else {
  var userStoriesTaskId = resolveWaveTaskId("Wave4: user-stories", () =>
    TaskCreate({ subject: "Wave4: user-stories",
      description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Generate UserStories. Template: user-stories-template.md. Draft: plans/<active-plan>/artifacts/user-stories.md.
Load: references/user-stories-ipe-protocol.md — run ALL IPE steps BEFORE writing any US.
Inputs: ScreenList (SCR### + source file paths), permissions-matrix.md (actor split).`,
      addBlockedBy: [permissionsTaskId] }))
}

// --- W4 user-stories: renumber + contiguity gate ---
// Runs after W4 user-stories task, BEFORE W4.5 quality gate.
// Ensures US### codes are contiguous before the W4.5 reviewer sees them.
{
  // F2: async-TaskCreate guard
  if (!existsNonEmpty("plans/<active-plan>/artifacts/user-stories.md")) {
    throw new Error("W4 user-stories HALT — user-stories.md not written (async TaskCreate guard)")
  }
  if (fileContains("plans/<active-plan>/artifacts/user-stories.md", "{POPULATED_BY_FRAGMENTS}")) {
    throw new Error("W4 user-stories HALT — user-stories.md still has {POPULATED_BY_FRAGMENTS} (partial merge)")
  }
  // Apply "Renumber+Contiguity Gate (canonical)" with artifact=user-stories
  const isFull = mode === "full"
  if (isFull) {
    bash: .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/renumber_artifact_ids.py \
      --artifact user-stories --plan-dir plans/<active-plan>
    bash: .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
      --artifact user-stories --plan-dir plans/<active-plan> \
      --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
  } else {
    bash: .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
      --artifact user-stories --plan-dir plans/<active-plan> --report-only \
      --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
    console.log("[INFO] W4 user-stories renumber skipped (incremental: IDs frozen)")
  }
}

// --- Wave 4.5: UserStories quality gate (before W5 FeatureList dispatch) ---
// Runs after W4 user-stories task. W5 dispatches ONLY after W4.5 passes.
// Incremental: skip W4.5 if user-stories.md not re-generated this run.

let w45TaskId = null
const w45_reran = mode === "full" || affected_waves.includes("Wave4: user-stories")
if (w45_reran) {
  w45TaskId = TaskCreate({
    subject: "Wave4.5: user-stories-review",
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.

Fast quality review of UserStories ONLY — do NOT review other artifacts (that is Wave 7a's scope).

INPUT: plans/<active-plan>/artifacts/user-stories.md

CHECKS (run all, report each separately):

**Check 1 — Single intent per story (critical):**
- Each US### goal describes exactly ONE user action
- Fail indicators: goal contains "and" joining two distinct actions, "as well as", list of verbs (create + edit + delete), or covers full CRUD in one story
- Example fail: US003 "As a user, I can create, edit, and delete my profile" → 3 intents, split into 3 stories
- Flag as critical if ≥2 clearly distinct user intents in one story

**Check 2 — Actor clarity (critical):**
- Each US### has a named human actor (user, admin, manager, etc.)
- Fail: actor is "system", "application", "platform", or missing entirely
- "The system sends a notification" → not a user story, belongs in BehaviorLogic
- Flag as critical if actor is non-human or absent

**Check 3 — Outcome present (warning):**
- Each US### has a user-visible outcome ("so that..." or equivalent)
- No outcome = unclear why the feature matters → W5 cannot assess feature value
- Flag as warning if outcome absent

**Check 4 — Overly broad scope (warning):**
- US### covering an entire resource domain ("manage all X", "administer Y system") → too broad for W5 grouping
- Heuristic: goal contains "manage", "administer", "handle" as the ONLY verb without a specific action
- Acceptable: "manage my account settings" (specific resource, clear scope)
- Flag as warning, not critical (W5 can still attempt grouping)

**Check 5 — US### code uniqueness (critical):**
- No duplicate US### codes in the document
- Fail: US005 appears in two separate story blocks

OUTPUT: plans/<active-plan>/artifacts/user-stories-review.md

Use this exact frontmatter:
\`\`\`yaml
---
passed: true   # true = W5 can proceed; false = halt
issues: 0
warnings: 0
---
\`\`\`

Severity: Checks 1, 2, 5 are critical (issues count). Checks 3, 4 are warnings.
Halt threshold: passed=false only when issues > 0.

Passed Checks: ONE LINE per check (\`✓ <check_name>\`). NO prose.

TOKEN BUDGET: Load user-stories.md only. No cross-artifact loading needed.`,
    addBlockedBy: [userStoriesTaskId]
  })
} else {
  console.log("[INFO] W4.5 skipped — user-stories not re-generated (incremental: prior UserStories carries forward)")
  w45TaskId = `SKIPPED:W4.5`
}

// Halt on W4.5 failure before W5 dispatch
if (w45TaskId && !w45TaskId.startsWith("SKIPPED:")) {
  if (!existsNonEmpty("plans/<active-plan>/artifacts/user-stories-review.md")) {
    throw new Error("W4.5 HALT — gate output missing: user-stories-review.md was not written. Check W4.5 task for errors.")
  }
  const w45Content = readFile("plans/<active-plan>/artifacts/user-stories-review.md")
  const w45fm = parseFrontmatter(w45Content)
  if (w45fm.passed === "false" || w45fm.passed === false) {
    throw new Error(
      `W4.5 HALT — UserStories has ${w45fm.issues} critical issue(s). ` +
      `Fix user-stories.md, then re-run Wave 4 (--artifact user-stories) or restart from W4. ` +
      `Review: plans/<active-plan>/artifacts/user-stories-review.md`
    )
  }
  console.log(`[INFO] W4.5 passed (issues: ${w45fm.issues ?? 0}, warnings: ${w45fm.warnings ?? 0})`)
}

const w45Blocker = (w45TaskId && !w45TaskId.startsWith("SKIPPED:")) ? w45TaskId : userStoriesTaskId

// Wave 4.7 — REMOVED (replaced by Wave 6.8 process-flow synthesis in pipeline-w7-w9.md)

```

### Wave 5 — FeatureList (+ canonical-fcode post-step)

```
// --- W5 feature-list: pre-gen estimate gate (grouping-once + expand-many) ---
const flEstimate = JSON.parse(bash(`.claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/estimate_artifact_loc.py \
  --artifact feature-list \
  --plan-dir plans/<active-plan> \
  --max-loc ${docs_maxLoc ?? 800}`).stdout)
console.log(`[INFO] W5 feature-list pre-gen estimate: ${flEstimate.unit_count} F###, est_loc=${flEstimate.est_loc}, shard=${flEstimate.shard}`)

if (flEstimate.shard) {
  // SHARD BRANCH: grouping-once (shell) → expand-many (fan-out) → merge.
  // CANONICAL-FCODE POST-STEP EXTRACTED to orchestrator (see below) so it runs on NEW F### after renumber.
  // See references/artifact-sharding.md § Feature-list — Grouping-once + Expand-many.
  var featureListTaskId = TaskCreate({ subject: "Wave5: feature-list (shard: grouping-once→expand→merge)",
    description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
SHARD MODE for FeatureList (${flEstimate.unit_count} F###, est_loc=${flEstimate.est_loc} > ${docs_maxLoc ?? 800}).
Read references/artifact-sharding.md § Feature-list — Grouping-once + Expand-many.

UNIQUE SHAPE — feature-list is a global-clustering artifact (F### derived from many source units).

1. SHELL STEP = GROUPING ONCE (global, single agent sees everything):
   - Read ALL prior drafts (US###/SCR###/routes/models/BL###/permissions).
   - Do the GLOBAL clustering in ONE pass → write compact ## Feature Hierarchy table.
   - Write _fragments/feature-list/_slice-plan.json: F### → {member US###, SCR###, routes, models, BL###}.
     F### born here, disjoint by construction. No separate range pre-allocation.
   - Write feature-list.md skeleton: preamble + ## Feature Hierarchy table (shell-owned) + per-F###-batch {POPULATED_BY_FRAGMENTS} anchors under ## Feature Details.

2. FAN-OUT = EXPAND DETAILS per F### batch (SEQUENTIAL BATCHES of REBUILD_SHARD_MAX_PARALLEL=5, batch i+1 only after ALL of batch i — counts toward the global 5-agent cap):
   - Each researcher owns a disjoint batch of already-assigned F###.
   - Write ### F###: Name detail blocks (description, related screens/US/routes/models per feature).
   - Output: _fragments/feature-list/NN-<fbatch>.md. Zero overlap by construction.

3. MERGE: ls|sort → inject per F###-batch anchor → rm -rf.

NOTE: Do NOT run the canonical-fcode post-step (slug derivation, _canonical-fcodes.json, .pending folders)
inside this task — the orchestrator runs it AFTER renumber so slugs/folders use NEW F### codes.

Template: feature-list-template.md. Draft: plans/<active-plan>/artifacts/feature-list.md`,
    addBlockedBy: [w45Blocker] })
} else {
  // SINGLE-TASK BRANCH: task writes feature-list.md ONLY.
  // CANONICAL-FCODE POST-STEP EXTRACTED to orchestrator (see below) so it runs on NEW F### after renumber.
  var featureListTaskId = resolveWaveTaskId("Wave5: feature-list", () =>
    TaskCreate({ subject: "Wave5: feature-list",
      description: `Session context: read \`plans/<active-plan>/artifacts/_session-context.md\` FIRST.
Generate FeatureList from all prior drafts. Template: feature-list-template.md. Draft: plans/<active-plan>/artifacts/feature-list.md.

FLOWS CONTEXT: process-flows are now synthesized at FL.1 (flows pass), not pre-W5.
FS.1 feature-spec researchers may read flows/ if present from a prior run, but flows are NOT a prerequisite for FS.1.

NOTE: Do NOT run the canonical-fcode post-step (slug derivation, _canonical-fcodes.json, .pending folders)
inside this task — the orchestrator runs it AFTER renumber so slugs/folders use NEW F### codes.`,
      addBlockedBy: [w45Blocker] }))
}

// --- W5 feature-list: orchestrator post-step (full runs) ---
// F1: canonical-fcode post-step EXTRACTED from task descriptions above → runs here AFTER renumber.
// Ordering: async guard → F### integrity gate (shard only) → renumber → slice-plan key-rewrite (shard only)
//           → contiguity gate → canonical-fcode bash (slug/JSON/.pending on NEW F### codes).
//
// M2: This block runs UNCONDITIONALLY (no w5_reran predicate) by design.
// Reason: an incremental re-run that only touches W5 (e.g. --artifact feature-list) still generates
// a fresh feature-list.md and must go through the renumber → contiguity → canonical-fcode chain.
// The F2 async-TaskCreate guard below (existsNonEmpty) is the gate that prevents a spurious run
// when W5 was not re-invoked this cycle.  The isFull branch inside handles full vs incremental split.
{
  // F2: async-TaskCreate guard
  const flArtifactPath = "plans/<active-plan>/artifacts/feature-list.md"
  if (!existsNonEmpty(flArtifactPath)) {
    throw new Error("W5 feature-list HALT — feature-list.md not written (async TaskCreate guard)")
  }
  if (fileContains(flArtifactPath, "{POPULATED_BY_FRAGMENTS}")) {
    throw new Error("W5 feature-list HALT — feature-list.md still has {POPULATED_BY_FRAGMENTS} (partial merge)")
  }

  // F4: renumber fires on FULL runs ONLY.
  const isFull = mode === "full"

  if (isFull) {
    // 3b. F### INTEGRITY GATE (shard only — inline orchestrator check; authority:
    //     artifact-sharding.md § Feature-list merge). Uses _slice-plan.json which holds
    //     OLD codes, so this gate MUST run BEFORE renumber. A fan-out chunk that
    //     hallucinated an out-of-batch F### would otherwise flow into a spurious
    //     .pending feature folder.
    if (flEstimate.shard) {
      const planned = Object.keys(readJson("plans/<active-plan>/artifacts/_fragments/feature-list/_slice-plan.json"))
      const merged  = parseHeadings(flArtifactPath, /^### (F\d{3})/)   // every `### F###` heading
      const rogue   = merged.filter(f => !planned.includes(f))
      if (rogue.length) {
        throw new Error(`W5 feature-list HALT — F### integrity: ${rogue.join(", ")} in merged file but not in _slice-plan.json`)
      }
    }

    // 3c. Apply "Renumber+Contiguity Gate (canonical)" with artifact=feature-list.
    //     Delta: integrity gate above MUST run before renumber (uses OLD F### codes).
    //     Delta: slice-plan key rewrite handled automatically by renumber script (F13).
    bash: .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/renumber_artifact_ids.py \
      --artifact feature-list --plan-dir plans/<active-plan>
    // (slice-plan keys rewritten atomically by renumber script when _fragments/feature-list/_slice-plan.json exists)
    bash: .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
      --artifact feature-list --plan-dir plans/<active-plan> \
      --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
    // exit 1 → FAIL → HALT (surface JSON); exit 2 → internal error → halt  [HALT scoped to FULL mode]

    // 4. CANONICAL-FCODE POST-STEP — orchestrator-performed (NOT inside the W5 task),
    //    operates on NEW F### codes after renumber. Authority: references/canonical-fcode-schema.md.
    //    1. Parse every '### F###: Name' heading under '## Feature Details' of feature-list.md.
    //    2. Derive slug per canonical-fcode-schema.md § Slug Grammar (CamelCase, alnum-only, ≤36 chars).
    //    3. GLOBAL slug-collision check: if two features derive the same slug → print
    //       '[ERROR] SLUG_COLLISION: F### "<a>" and F### "<b>" both derive slug "<slug>"' and
    //       HALT (no JSON, no folders). User resolves by renaming a feature, then reruns Wave 5.
    //    4. Write plans/<active-plan>/artifacts/_canonical-fcodes.json per the schema doc (sorted by fcode).
    //    5. For each feature: mkdir -p plans/<active-plan>/artifacts/features/{slug}/ AND
    //       touch plans/<active-plan>/artifacts/features/{slug}/.pending (zero-byte marker).
    //    Both outputs (canonical JSON + .pending folders) are consumed by the Wave 5.5
    //    existence validator and FS.1 fan-out (slug source).
  } else {
    // Apply "Renumber+Contiguity Gate (canonical)" incremental path with artifact=feature-list
    bash: .claude/skills/.venv/bin/python3 \
      claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
      --artifact feature-list --plan-dir plans/<active-plan> --report-only \
      --summary-out plans/<active-plan>/artifacts/validation/validation-summary.json
    console.log("[INFO] W5 feature-list renumber skipped (incremental: IDs frozen)")
  }
}
```
