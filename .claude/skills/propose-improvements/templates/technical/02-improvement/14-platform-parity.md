# Improvement Aspect: Platform Parity — {PROJECT_NAME}
**Use context:** {internal|hybrid|customer-facing}
<!-- REQUIRED: copy verbatim from any 01-discovery/ item line 2. Parsed by Step 4.3. Do NOT re-classify. -->

<!-- One entry per missing platform from discovery §8. Use-context gating + evidence rule — see references/technical/02-improvement.md (Shared rules + Aspect 14). -->

<!-- Empty aspect (no platform gaps vs category norms) emits a single 'Status: clean — no current gap' entry. -->

{entries — see Entry format below}

---

## Entry format

```markdown
- Status: {opportunity | clean — no current gap | needs-more-discovery}
- Category: platform-parity
- Observation: {name the missing platform and why peers offer it; 1-2 sentences}
- Evidence: {MUST quote the §8 detection result from discovery artifact — e.g. "(none detected)" or specific absence; include path:line}
- Potential improvement: {what building this platform would entail; 1-3 sentences, stack-consistent}
- Customer-value signal: {categorical tag — vocabulary in reference}
- Value: {high | medium | low — rubric in reference}
- Engineering effort hint: {no | very-low | low | medium | high} — based on stack fit and scope, not guessing
- Risk if untouched: {what breaks, slows, or costs the customer if we do nothing}
```

<!-- Total length under 200 lines. Single-aspect scope only — no cross-aspect ranking. -->
