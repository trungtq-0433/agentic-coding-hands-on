# Monetization Model — {PRODUCT_NAME}
**Use context:** {internal|hybrid|customer-facing}

<!-- Use-context-conditional:
     - `internal` → write exactly: "N/A (internal use — monetization out of scope)" and skip the rest.
     - `hybrid` → capture ONLY external-facing portion (enterprise tier, self-host licensing, partner tier).
       Internal-only usage remains out of scope. Note which users/tiers each item targets.
     - `customer-facing` → capture in full. -->

- **Model type:** {free | trial | freemium | subscription | usage-based | enterprise | none}
- **Tier structure:**
  - {Tier name} — limits: {…}, price: {if in spec — NOT if only in `.env.prod` or secret}
  - {Tier name} — limits: {…}, price: {…}
- **Conversion / upgrade paths declared in spec:** {description with cited spec IDs}

<!-- Total length under 100 lines. Snapshot only — no recommendations or commentary. -->
