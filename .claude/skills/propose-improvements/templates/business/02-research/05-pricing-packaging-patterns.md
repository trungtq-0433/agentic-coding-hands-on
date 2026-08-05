# Pricing & Packaging Patterns — {PRODUCT_NAME}
**Use context:** {internal|hybrid|customer-facing}
<!-- REQUIRED: copy verbatim from any 01-discovery/ item line 2. Parsed by Step 3.3 and downstream. Do NOT re-classify. -->

<!-- EMIT EXACTLY ONE of the three variants below, gated on the Use-context marker:
     - "customer-facing" → emit Variant A only (Pricing & packaging patterns).
     - "hybrid"          → emit Variant B only (enterprise / self-host / partner tier).
     - "internal"        → emit Variant C only (Operational benchmarks & build-vs-buy);
                           also rename the section heading to "## 5. Operational benchmarks & build-vs-buy".
     Never emit more than one variant. Delete the unused variant blocks before writing output. -->

<!-- VARIANT A — Use context: customer-facing -->
## 5. Pricing & packaging patterns

- **Comparable monetization:** {free-tier limits, seat pricing, usage pricing, enterprise add-ons used by category peers} (source: {url or model-prior}, accessed {YYYY-MM-DD})
- **Common upgrade triggers in the category:** {usage caps, team size, SSO/SAML, audit logs, SLAs} (source: {url or model-prior}, accessed {YYYY-MM-DD})

<!-- VARIANT B — Use context: hybrid (REPLACES Variant A; scope narrowed to enterprise/self-host/partner tier) -->
## 5. Pricing & packaging patterns

- **Open-core vs. proprietary splits:** {how category peers divide OSS and commercial features} (source: {url or model-prior}, accessed {YYYY-MM-DD})
- **Enterprise-tier feature gates:** {SSO, audit log, support SLA, on-prem deployment — what competitors gate and at what tier} (source: {url or model-prior}, accessed {YYYY-MM-DD})
- **Partner / reseller / OEM terms:** {packaging patterns for channel distribution} (source: {url or model-prior}, accessed {YYYY-MM-DD})

<!-- VARIANT C — Use context: internal (REPLACES Variant A entirely; rename heading as shown) -->
## 5. Operational benchmarks & build-vs-buy

- **How peer organizations solve this internally:** {tooling choices, team size, build complexity} (source: {url or model-prior}, accessed {YYYY-MM-DD})
- **Build-vs-buy signals:** {factors that tip decisions toward build, buy, or OSS adoption in this category} (source: {url or model-prior}, accessed {YYYY-MM-DD})
- **Maturity benchmarks for the category run in-house:** {what "good" looks like operationally} (source: {url or model-prior}, accessed {YYYY-MM-DD})

<!-- Total length under 200 lines. Snapshot only — no recommendations or commentary. -->
