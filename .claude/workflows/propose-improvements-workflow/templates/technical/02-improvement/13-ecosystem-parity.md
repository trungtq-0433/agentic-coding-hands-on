# Improvement Aspect: Ecosystem Parity — {PROJECT_NAME}
**Use context:** {internal|hybrid|customer-facing}
<!-- REQUIRED: copy verbatim from any 01-discovery/ item line 2. Parsed by Step 4.3. Do NOT re-classify. -->

<!-- One entry per missing peer vendor for each `single-vendor` discovery entry. Use-context gating + evidence/effort rules — see references/technical/02-improvement.md (Shared rules + Aspect 13). -->

<!-- Empty aspect (zero single-vendor entries in discovery) emits a single 'Status: clean — no current gap' entry. -->

{entries — see Entry format below}

---

## Entry format

```markdown
- Status: {opportunity | clean — no current gap | needs-more-discovery}
- Category: ecosystem-parity
- Observation: {name the existing single-vendor integration and the missing peer; 1-2 sentences}
- Evidence: {MUST quote the discovery's vendor-category map line; include path:line}
- Potential improvement: {integrate peer vendor X in the same category; 1-3 sentences on approach}
- Customer-value signal: {categorical tag — vocabulary in reference}
- Value: {high | medium | low — rubric in reference}
- Engineering effort hint: {no | very-low | low | medium | high — low/medium if adapter pattern; high if hardcoded per-vendor}
- Risk if untouched: {what breaks, slows, or costs the customer if we do nothing}
```

<!-- Total length under 200 lines. Single-aspect scope only — no cross-aspect ranking. -->
