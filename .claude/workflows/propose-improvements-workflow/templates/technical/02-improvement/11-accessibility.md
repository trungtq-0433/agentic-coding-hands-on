# Improvement Aspect: Accessibility — {PROJECT_NAME}
**Use context:** {internal|hybrid|customer-facing}
<!-- REQUIRED: copy verbatim from any 01-discovery/ item line 2. Parsed by Step 4.3. Do NOT re-classify. -->

<!-- Skip if no UI detected per discovery §7 (UI presence: no) — emit single 'Status: clean — no UI detected per discovery §7' entry. -->

<!-- One or more entries below. Empty aspect emits a single 'Status: clean — no current gap' entry. Use-context-conditional rules in references/technical/02-improvement.md (Shared rules + Aspect 11). -->

{entries — see Entry format below}

---

## Entry format

```markdown
- Status: {opportunity | clean — no current gap | clean — no UI detected per discovery §7 | needs-more-discovery}
- Category: accessibility
- Observation: {1-2 sentences tied directly to the discovery snapshot}
- Evidence: {quote specific bullet(s) from discovery; include path:line, metric, or node ID}
- Potential improvement: {1-3 sentences, technology-consistent with stack}
- Customer-value signal: {categorical tag — vocabulary in reference}
- Value: {high | medium | low — rubric in reference}
- Engineering effort hint: {no | very-low | low | medium | high} — based on stack fit and scope, not guessing
- Risk if untouched: {what breaks, slows, or costs the customer if we do nothing}
```

<!-- Total length under 200 lines. Single-aspect scope only — no cross-aspect ranking. -->
