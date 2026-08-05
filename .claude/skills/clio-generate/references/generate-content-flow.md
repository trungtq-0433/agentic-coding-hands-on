## Output Target (v3 — 2-step flow)

**This reference covers profile sections, not slides.** Data extracted here flows into the JSON profile passed to `scripts/gen-md.py`:

| Profile section | Schema path | Old slide(s) |
|-----------------|-------------|--------------|
| `screen_flow` | `ScreenFlowSection {image_path}` | Slide 8 |
| `business_process` | `BusinessProcessSection {categories[], before_steps[], after_blocks[{title, body}]}` | Slides 10, 11 |

**Ignore** any `FILL_SLIDE:` / `SHAPE:` markers below — populate the JSON sections instead. PNG images: generate the file and put its path in the JSON (e.g. `"screen_flow": {"image_path": "outputs/screen_flow_X.png"}`).

---

### **Step 7: Generate Slide 8 - Screen Transition Diagram (UIデザイン 画面遷移図)**

**Goal:** Generate a NEW clean, slide-ready Mermaid screen flow diagram, export it as PNG, and embed it into Slide 8.

**ALWAYS generate a NEW simplified Mermaid diagram from scratch.** Do NOT reuse or extract the diagram from `screen_flow_*.md` — that file contains all 86+ screens and is far too cluttered for a slide. The goal is a clean, readable overview suitable for a presentation image.

---

**Action 1: Read screen flow data**

Find the latest screen flow markdown:
```bash
ls -t outputs/screen_flow_{project_id}_*.md 2>/dev/null | head -1
```

If found, read the file and extract:
- List of modules with their names (e.g., 01_受注, 02_仕入, 03_出荷, 04_在庫, 05_売上, 90_マスタ)
- Critical/High-priority screens per module (2–3 per module maximum)
- Key process chains (e.g., billing chain, fulfillment chain) to determine arrow direction within each module

If not found:
```
No screen_flow file found for project: {project_id}
Skipping Slide 8 and proceeding to Slides 10 & 11...
```
Skip to Step 8.

---

**Action 2: Compose a NEW clean Mermaid diagram**

Using the data from Action 1, write a new Mermaid diagram following these strict rules:

**Layout rules:**
- Direction: `flowchart LR` — left-to-right fits the horizontal slide shape
- Maximum **30 nodes total** — select only the most important screens
- Module nodes: use 2-line labels with module number + name: `"01\n受注管理"`
- Screen nodes: short Japanese names (≤8 characters per line, 2 lines max)
- Arrows: use `-->` for main flow, `-.->` only for optional/logout paths

**Mandatory color scheme (white background, high-contrast text):**

| Node role | fill | stroke | color (text) | stroke-width |
|-----------|------|--------|--------------|-------------|
| Entry point `([...])` | `#4caf50` | `#2e7d32` | `#ffffff` | `3px` |
| Login / Auth | `#ef5350` | `#c62828` | `#ffffff` | `3px` |
| Main Menu hub | `#1565c0` | `#0d47a1` | `#ffffff` | `4px` |
| Module group | `#f57c00` | `#e65100` | `#ffffff` | `2px` |
| List / Inquiry screen | `#e3f2fd` | `#1976d2` | `#0d47a1` | `1px` |
| Process / Form screen | `#e8f5e9` | `#388e3c` | `#1b5e20` | `1px` |
| Output / Export screen | `#fff9c4` | `#f9a825` | `#5d4200` | `1px` |

**Reference template — adapt node labels and structure to match actual project data:**

```
flowchart LR
    START([起動]) --> LOGIN["ログイン"]
    LOGIN --> MENU["メインメニュー"]

    MENU --> ORD["01\n受注管理"]
    MENU --> PUR["02\n仕入管理"]
    MENU --> SHIP["03\n出荷管理"]
    MENU --> INV["04\n在庫管理"]
    MENU --> SALE["05\n売上管理"]
    MENU --> MST["90\nマスタ管理"]

    ORD --> O1["顧客検索"]
    ORD --> O2["受注一覧照会"]

    PUR --> P1["発注入力"]
    PUR --> P2["入荷検収入力"]
    PUR --> P3["買掛金一覧"]

    SHIP --> S1["受注締め"]
    S1 --> S2["出荷指示書"]
    S2 --> S3["送り状番号登録"]

    INV --> I1["在庫一覧照会"]
    INV --> I2["在庫調整入力"]

    SALE --> SA1["仮締処理"]
    SA1 --> SA2["請求処理"]
    SA2 --> SA3["請求書出力"]
    SALE --> SA4["月次締め"]

    MST --> M1["得意先マスタ"]
    MST --> M2["カタログマスタ"]
    MST --> M3["仕入先マスタ"]

    classDef entry fill:#4caf50,stroke:#2e7d32,color:#ffffff,stroke-width:3px
    classDef auth  fill:#ef5350,stroke:#c62828,color:#ffffff,stroke-width:3px
    classDef hub   fill:#1565c0,stroke:#0d47a1,color:#ffffff,stroke-width:4px
    classDef mod   fill:#f57c00,stroke:#e65100,color:#ffffff,stroke-width:2px
    classDef list  fill:#e3f2fd,stroke:#1976d2,color:#0d47a1,stroke-width:1px
    classDef proc  fill:#e8f5e9,stroke:#388e3c,color:#1b5e20,stroke-width:1px
    classDef out   fill:#fff9c4,stroke:#f9a825,color:#5d4200,stroke-width:1px

    class START entry
    class LOGIN auth
    class MENU hub
    class ORD,PUR,SHIP,INV,SALE,MST mod
    class O1,O2,P1,P2,P3,I1,I2,M1,M2,M3 list
    class S1,SA1,SA2,P2 proc
    class SA3,SA4,S2,S3 out
```

> Adjust module count, screen names, and class assignments to reflect actual project screens. Never copy the template verbatim — always tailor to the real data.

---

**Action 3: Save Mermaid file and export PNG**

Use Python to write the Mermaid code (avoids shell quoting issues with Japanese characters):

```bash
python3 - << 'PYEOF'
mmd_code = \"\"\"[PASTE THE FULL MERMAID CODE FROM Action 2 HERE — no fences, raw Mermaid only]\"\"\"

out_path = 'outputs/.tmp_slide8_{project_id}.mmd'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(mmd_code.strip() + '\n')
print(f'Mermaid temp file saved: {out_path}')
PYEOF
```

Generate PNG with Mermaid CLI (white background, large resolution for slide clarity):
```bash
npx --yes @mermaid-js/mermaid-cli \
  -i outputs/.tmp_slide8_{project_id}.mmd \
  -o outputs/screen_flow_{project_id}_{YYYYMMDD_HHMMSS}.png \
  --width 2400 --height 2000 --backgroundColor white

rm outputs/.tmp_slide8_{project_id}.mmd
ls -lh outputs/screen_flow_{project_id}_{timestamp}.png
```

If PNG generation fails (e.g., mmdc not available):
```
PNG generation failed. Check that Node.js is installed:
  node --version
  npx --yes @mermaid-js/mermaid-cli --version
Skipping Slide 8...
```
Skip to Step 8.

---

**Action 4: Write Slide 8 markers to main markdown**

The PNG has been generated at `outputs/screen_flow_{project_id}_{timestamp}.png`. Now write the `FILL_SLIDE: 8` and `SHAPE` markers to the main markdown file so the PPTX renderer can inject the image.

**CRITICAL: Use `Edit` tool to append the following block** to `outputs/slides_{project_id}_{timestamp}.md`:

```markdown
<!-- FILL_SLIDE: 8 -->

<!-- SHAPE: screen_flow_image -->
screen_flow_{project_id}_{timestamp}.png
```

Replace `{project_id}` and `{timestamp}` with the actual values used for the PNG filename.

After this step, **resume using `Edit` tool** for all subsequent slides (Step 8 onwards).

---

**Action 5: Confirm and continue**

Display message:
```
=== Step 7: Slide 8 - Screen Transition Diagram ===

Slide 8 markers written to main markdown!

Diagram:  outputs/screen_flow_{project_id}_{timestamp}.png

Slide 8 includes:
- New clean Mermaid diagram (LR layout, ≤30 nodes, white background)
- FILL_SLIDE: 8 + SHAPE: screen_flow_image markers written to markdown
- Color legend: green=entry · red=auth · blue=hub · orange=modules · blue/green/yellow=screens
- Target shape: screen_flow_image (PICTURE)

→ Proceeding to Slides 10 & 11 - Business Process Flow...
```

---



### **Step 8: Generate Slides 10 & 11 - Business Process Flow (業務フロー比較)**

**Goal:** Identify the core business flow of the project, then contrast the current (manual/legacy) way of doing it against the improved way after the new system is introduced. Slide 10 uses a **vertical layout** and Slide 11 uses a **horizontal layout** — both show the same before/after comparison, just with different visual presentations.

**Step 8.1: Understand the Project's Core Business Domain**
Execute the following query using `clio_query` MCP tool tool:

```json
{
  "project_id": "<project_id>",
  "query": "業務フロー 業務プロセス 業務の流れ 主要業務 担当部署 作業手順 業務概要"
}
```

**From the result, identify:**
- What is the **main business activity** this system supports? (e.g., sales, procurement, HR, manufacturing, maintenance, internal approval, etc.)
- What are the **4 key phases** of that business flow? These become `category_label_1` through `category_label_4`
- What **roles or departments** are involved?

>  Do NOT assume the domain. Derive phase names entirely from KG results.

**If the KG returns insufficient context**, run a broader follow-up:

```json
{
  "project_id": "<project_id>",
  "query": "システム概要 導入背景 対象業務 利用部門 ユーザー"
}
```

**Step 8.2: Query Current Process Pain Points (Before System)**

Once the domain is understood, query for how the current process works:

```json
{
  "project_id": "<project_id>",
  "query": "現行業務 手作業 現行システム 課題 非効率 手動 二重入力 確認作業 既存の問題点 ボトルネック"
}
```

**From the result, for each of the 4 phases identified in Step 8.1:**
- Identify **2 specific steps** staff currently perform manually or inefficiently
- These become `before_step_1` through `before_step_8` (2 steps per phase, in order)
- Keep each description concise (max ~25 characters), using action verbs

**Step 8.3: Query Improvements After System Introduction (After System)**

```json
{
  "project_id": "<project_id>",
  "query": "システム導入後 業務改善 自動化 効率化 新機能 改善効果 簡素化 デジタル化"
}
```

**From the result, for each of the 4 phases:**
- Identify the **new capability title** — what this system now enables for that phase (→ `after_cat*_title`, 5-15 chars)
- Extract a **brief improvement description** — how specifically the system removes the old pain point (→ `after_cat*_body`, exactly 1 line)

**Step 8.4: Map Content to Shape Keys**

| Shape Key | Content | Notes |
|-----------|---------|-------|
| `category_label_1` | Phase 1 name (from KG) | 2-6 chars — **Slide 10 only** |
| `category_label_2` | Phase 2 name (from KG) | 2-6 chars — **Slide 10 only** |
| `category_label_3` | Phase 3 name (from KG) | 2-6 chars — **Slide 10 only** |
| `category_label_4` | Phase 4 name (from KG) | 2-6 chars — **Slide 10 only** |
| `before_step_1` | Phase 1, current step 1 | Max ~25 chars |
| `before_step_2` | Phase 1, current step 2 | Max ~25 chars |
| `before_step_3` | Phase 2, current step 1 | Max ~25 chars |
| `before_step_4` | Phase 2, current step 2 | Max ~25 chars |
| `before_step_5` | Phase 3, current step 1 | Max ~25 chars |
| `before_step_6` | Phase 3, current step 2 | Max ~25 chars |
| `before_step_7` | Phase 4, current step 1 | Max ~25 chars |
| `before_step_8` | Phase 4, current step 2 | Max ~25 chars |
| `after_cat1_title` | Phase 1 new capability | 5-15 chars |
| `after_cat1_body` | Phase 1 improvement detail | exactly 1 line |
| `after_cat2_title` | Phase 2 new capability | 5-15 chars |
| `after_cat2_body` | Phase 2 improvement detail | exactly 1 line |
| `after_cat3_title` | Phase 3 new capability | 5-15 chars |
| `after_cat3_body` | Phase 3 improvement detail | exactly 1 line |
| `after_cat4_title` | Phase 4 new capability | 5-15 chars |
| `after_cat4_body` | Phase 4 improvement detail | exactly 1 line |

**Step 8.5: Generate Content for Slides 10 and 11**

**CRITICAL: Use `Edit` tool to append content**

**Append to:** `outputs/slides_{project_id}_{timestamp}.md`

Generate **BOTH** slides in one content block using the content derived from KG:
- **Slide 10** includes `category_label_*` shapes (vertical layout — phase labels appear on left side)
- **Slide 11** omits `category_label_*` (horizontal layout — phase labels are decorative in the template)
- All `before_step_*` and `after_cat*` values are **identical** in both slides

**Format to append:**

```markdown
<!-- FILL_SLIDE: 10 -->
<!-- SHAPE: category_label_1 -->
[Phase 1 name from KG]

<!-- SHAPE: category_label_2 -->
[Phase 2 name from KG]

<!-- SHAPE: category_label_3 -->
[Phase 3 name from KG]

<!-- SHAPE: category_label_4 -->
[Phase 4 name from KG]

<!-- SHAPE: before_step_1 -->
[Current manual/inefficient step 1 of Phase 1]

<!-- SHAPE: before_step_2 -->
[Current manual/inefficient step 2 of Phase 1]

<!-- SHAPE: before_step_3 -->
[Current manual/inefficient step 1 of Phase 2]

<!-- SHAPE: before_step_4 -->
[Current manual/inefficient step 2 of Phase 2]

<!-- SHAPE: before_step_5 -->
[Current manual/inefficient step 1 of Phase 3]

<!-- SHAPE: before_step_6 -->
[Current manual/inefficient step 2 of Phase 3]

<!-- SHAPE: before_step_7 -->
[Current manual/inefficient step 1 of Phase 4]

<!-- SHAPE: before_step_8 -->
[Current manual/inefficient step 2 of Phase 4]

<!-- SHAPE: after_cat1_title -->
[New capability enabled by system for Phase 1]

<!-- SHAPE: after_cat1_body -->
[How the system improves Phase 1 — 1 line only]

<!-- SHAPE: after_cat2_title -->
[New capability enabled by system for Phase 2]

<!-- SHAPE: after_cat2_body -->
[How the system improves Phase 2 — 1 line only]

<!-- SHAPE: after_cat3_title -->
[New capability enabled by system for Phase 3]

<!-- SHAPE: after_cat3_body -->
[How the system improves Phase 3 — 1 line only]

<!-- SHAPE: after_cat4_title -->
[New capability enabled by system for Phase 4]

<!-- SHAPE: after_cat4_body -->
[How the system improves Phase 4 — 1 line only]

<!-- FILL_SLIDE: 11 -->
<!-- SHAPE: before_step_1 -->
[Same as slide 10]

<!-- SHAPE: before_step_2 -->
[Same as slide 10]

<!-- SHAPE: before_step_3 -->
[Same as slide 10]

<!-- SHAPE: before_step_4 -->
[Same as slide 10]

<!-- SHAPE: before_step_5 -->
[Same as slide 10]

<!-- SHAPE: before_step_6 -->
[Same as slide 10]

<!-- SHAPE: before_step_7 -->
[Same as slide 10]

<!-- SHAPE: before_step_8 -->
[Same as slide 10]

<!-- SHAPE: after_cat1_title -->
[Same as slide 10]

<!-- SHAPE: after_cat1_body -->
[Same as slide 10]

<!-- SHAPE: after_cat2_title -->
[Same as slide 10]

<!-- SHAPE: after_cat2_body -->
[Same as slide 10]

<!-- SHAPE: after_cat3_title -->
[Same as slide 10]

<!-- SHAPE: after_cat3_body -->
[Same as slide 10]

<!-- SHAPE: after_cat4_title -->
[Same as slide 10]

<!-- SHAPE: after_cat4_body -->
[Same as slide 10]
```

**Content generation rules:**

**`category_label_*` (Slide 10 only):**
- Short noun derived from KG (2-6 chars), represents one phase of the project's actual business flow
- Alignment: cat1 = steps 1-2, cat2 = steps 3-4, cat3 = steps 5-6, cat4 = steps 7-8
- **Do NOT include in Slide 11 block**

**`before_step_*`:**
- Max ~25 characters — concise action description
- Must reflect what actually happens in THIS project's current process (from KG)
- Do NOT invent or assume typical industry steps — only use what the KG confirms

**`after_cat*_title`:**
- Short noun phrase (5-15 chars) naming the new system capability for that phase
- Must be grounded in actual system features described in the KG

**`after_cat*_body`:**
- Exactly **1 line** — no newlines allowed
- Max **20 characters** — ultra short noun phrase only
- Describe the key improvement/automation in that phase (e.g. `自動登録・即時反映`, `ワンクリック発注`, `在庫自動連携`)
- Do NOT write full sentences — just a short label/phrase

**Step 8.6: Confirm and Continue**

Save the updated file and display message:
```
=== Step 8: Generate Slides 10 & 11 - Business Process Flow ===
Querying KG for current business process flows...
Retrieved manual steps and pain points

Querying KG for post-system improvements...
Retrieved automation and efficiency gains

Process phases defined:
  Phase 1 (category_label_1): [Phase 1 name]
  Phase 2 (category_label_2): [Phase 2 name]
  Phase 3 (category_label_3): [Phase 3 name]
  Phase 4 (category_label_4): [Phase 4 name]

Generated process flow content:
  Before: 8 manual process steps (2 per phase)
  After:  4 improvement sections (title + body per phase)

Added Slides 10 & 11 to outputs/slides_{project_id}_{timestamp}.md
  ✓ Slide 10 (vertical layout): 4 category labels + 8 before steps + 4 after improvements
  ✓ Slide 11 (horizontal layout): 8 before steps + 4 after improvements (no category labels)


→ Proceeding to Slide 12 - System Benefits...
```

