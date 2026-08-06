# Asset Manifest

Mapping `nodeId → asset file path`. Multiple nodeIds may point to the same file (dedup by node name). The path is a PLAN — the file may still be downloading in the background. Paths are **import-ready** (prefix `/login`).

| Node ID | File path | Filename | Status |
|---------|-----------|----------|--------|
| `2939:9548` | `/login/Root_Further_Logo.png` | `Root_Further_Logo.png` | ✓ |
| `I662:14426;186:1766` | `/login/Google.svg` | `Google.svg` | ✓ |
