# Improvement Aspect — Performance

**Track:** technical · **Aspect:** 05 of 14 · **Slug:** `performance`
**Read first:** `references/technical/02-improvement.md` — Shared rules, Ownership map, Entry format, and Value rubric apply unconditionally.
**Output:** `plans/improvement-proposal/technical/02-improvement/05-performance.md`
**Template:** `templates/technical/02-improvement/05-performance.md`

## Goal
Enumerate performance improvement opportunities: hot paths without caching, N+1 queries, bundle size, startup time, memory usage, missing indexes, slow background jobs, unoptimized assets.

## Intake gate
Owns ALL caching, hot-path optimisation, and query performance concerns exclusively. Architecture (01) and scalability (10) MUST NOT emit entries whose primary remedy is adding a cache layer, fixing an N+1 query, or optimising a hot code path. Defers from: 01-architecture, 10-scalability — see ownership map.
