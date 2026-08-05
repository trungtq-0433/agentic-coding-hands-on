# Improvement Aspect — Platform Parity

**Track:** technical · **Aspect:** 14 of 14 · **Slug:** `platform-parity`
**Read first:** `references/technical/02-improvement.md` — Shared rules, Ownership map, Entry format, and Value rubric apply unconditionally.
**Output:** `plans/improvement-proposal/technical/02-improvement/14-platform-parity.md`
**Template:** `templates/technical/02-improvement/14-platform-parity.md`

## Goal
Identify client or deployment platforms that peers in this product category commonly offer but the discovery snapshot's §8 (`08-platform-support.md`) shows as `(none detected)` or absent. Each missing platform is a distinct entry (e.g., "no mobile app", "no self-hosted deployment option", "no CLI", "no public API/SDK"). Do NOT propose platforms already detected in §8. If §8 shows no gaps vs category norms, emit `Status: clean — no current gap`.

`Evidence:` MUST quote the §8 detection result from the discovery artifact. Do NOT propose platforms already detected in §8.

## Use-context overrides
**When `internal`:**
- Do NOT propose mobile, consumer desktop, or public-SDK platforms.

**When `hybrid`:**
- Consumer-only platforms (mobile app for end users, browser extension) are out of scope.

**When `customer-facing`:** full platform matrix applies — web, mobile, desktop, CLI, API/SDK, browser extension.
