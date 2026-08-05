## Output Target (v3 — 2-step flow)

**This reference covers `approach_comparison` + `assumptions`.** Data flows into JSON; Step B's renderer slices assumptions across slides 23/24/25 automatically.

| Profile section | Schema | Old slide(s) |
|-----------------|--------|--------------|
| `approach_comparison` | `list[dict]` (row dicts; column keys preserved as table headers) | Slide 21 |
| `assumptions` | `list[AssumptionSection {label, content}]` | Slides 23, 24, 25 |

**Assumption labels** are fixed by the template (e.g. 開発方針/品質戦略/開発言語/...). The `label` field is preserved for ordering; the `content` field is what gets written. Provide one entry per template row (9 total for slides 23-25).

**Ignore** any `FILL_SLIDE:` / `SHAPE:` markers below — populate the JSON sections.

---

### **Step 11: Generate Slide 21 - Approach Comparison Table**

**Goal:** Create comparison table analyzing different system development approaches to support decision-making.

**Step 11.1: Query Knowledge Graph for Approach Analysis Data**

Query the Knowledge Graph for information needed to analyze and compare approaches:

```
{
  "project_id": "<project_id>",
  "query": "システム要件 制約条件 技術スタック 既存システム 予算 期間 開発手法 チーム能力 リスク 優先度 アプローチ 開発方式 段階的導入 全面刷新 部分改修"
}
```

**Extract key information:**
- System requirements and constraints
- Budget and timeline limitations
- Current technology stack
- Existing system information
- Team capabilities and experience
- Business priorities
- Risk tolerance

**Step 11.2: Define Comparison Approaches**

Based on the KG results, define 2-4 distinct approaches. Common patterns:

**Type A: Minimal Change Approach (既存活用型)**
- Leverage existing systems with targeted improvements
- Low risk, lower cost, faster implementation
- Limited UX improvement, technical debt remains

**Type B: Modernization Approach (刷新型)**
- Modernize frontend or key components
- Moderate cost and risk, significant UX improvement
- Some technical debt addressed

**Type C: Full Rebuild Approach (全面再構築型)**
- Complete system reconstruction
- High cost and risk, maximum future flexibility
- All technical debt eliminated

**Step 11.3: Analyze Each Approach**

For each approach, analyze:

1. **アプローチ (Approach)**: One-sentence description of the approach
2. **アプローチが成立する前提条件 (Prerequisites)**: 2-4 conditions required for success
3. **想定機能数 (Estimated Functions)**: Number of functions (e.g., "約50機能")
4. **UXの改善度合い (UX Improvement)**: Platform-specific improvement level (高/中/低)
5. **要件の網羅性 (Requirements Coverage)**: Percentage or level (e.g., "85%", "全面対応")
6. **pro (Advantages)**: 3-7 key benefits with quantitative impact when possible
7. **con (Disadvantages)**: 3-7 key drawbacks, risks, and limitations

**Step 11.4: Generate Markdown Table**

Create a comparison table in markdown format. **CRITICAL FORMAT RULES:**
- NO line breaks within table cells - each cell must be on a single line
- NO `<br>` tags - use plain text only
- NO `**` bold markers - use plain text
- Use `・` (middle dot) for bullet points, all on one line separated by spaces
- Keep pro/con items concise, join multiple items on one line with spaces
- Include quantitative data where possible (costs, timelines, percentages)

**Example structure:**

```markdown
<!-- FILL_SLIDE: 21 -->

<!-- SHAPE: approach_comparison_table -->
| 項目 | A案 | B案 | C案 |
|------|-----|-----|-----|
| アプローチ | [Brief approach description] | [Brief approach description] | [Brief approach description] |
| アプローチが成立する前提条件 | ・[Condition 1] ・[Condition 2] ・[Condition 3] | ・[Condition 1] ・[Condition 2] ・[Condition 3] | ・[Condition 1] ・[Condition 2] ・[Condition 3] |
| 想定機能数 | 約[X]機能 | 約[Y]機能 | 約[Z]機能 |
| UXの改善度合い | [Platform]: [高/中/低] | [Platform]: [高/中/低] | [Platform]: [高/中/低] |
| 要件の網羅性 | [Percentage or level] | [Percentage or level] | [Percentage or level] |
| pro | ・[Benefit 1] ・[Benefit 2] ・[Benefit 3] ・[Benefit 4] ・[Benefit 5] | ・[Benefit 1] ・[Benefit 2] ・[Benefit 3] ・[Benefit 4] ・[Benefit 5] | ・[Benefit 1] ・[Benefit 2] ・[Benefit 3] ・[Benefit 4] ・[Benefit 5] |
| con | ・[Drawback 1] ・[Drawback 2] ・[Drawback 3] ・[Drawback 4] ・[Drawback 5] | ・[Drawback 1] ・[Drawback 2] ・[Drawback 3] ・[Drawback 4] ・[Drawback 5] | ・[Drawback 1] ・[Drawback 2] ・[Drawback 3] ・[Drawback 4] ・[Drawback 5] |
<!-- END SHAPE -->
```

**Step 11.5: Content Guidelines**

**For each row:**

- **アプローチ**: Clear differentiation between options, mention key technology choices
- **前提条件**: Specific, verifiable conditions (team skills, budget, timeline, existing systems)
- **想定機能数**: Specific numbers showing scope differences
- **UX改善度**: Be realistic - not all approaches improve everything equally
- **要件網羅性**: Show trade-offs - lower cost often means lower coverage
- **pro**: Focus on business value, include quantitative benefits (% reduction, time saved)
- **con**: Be honest about risks, costs, limitations, and trade-offs

**Step 11.6: Save Slide 21**

**CRITICAL: Use `Edit` tool to append content:**
- Append the new slide content (from Step 9.4) to the end of the file: `outputs/slides_{project_id}_{timestamp}.md`
- **DO NOT use `cat`, `echo`, or terminal commands - these require user confirmation**

**Expected console output:**
```
=== Step 11: Generate Slide 21 - Approach Comparison ===

Querying KG for approach analysis data...
Retrieved system requirements and constraints

Analyzing approaches:
  A案: 既存システム部分改修 (Minimal change)
  B案: フロントエンド刷新 (Modernization)
  C案: 全面再構築 (Full rebuild)

Generating comparison table...
Created comparison with 7 rows × 3 approaches

Content validation:
  Prerequisites: 2-4 items per approach
  Pro/con balance: 4-6 items each
  ✓ Quantitative data included
  Format: Markdown table (no line breaks within cells)

Added Slide 21 to outputs/slides_{project_id}_{timestamp}.md

→ Proceeding to Slides 23, 24, 25...
```

---



### **Step 12: Generate Slides 23, 24 & 25 - Estimated Assumptions (お見積りの前提条件)**

**Goal:** Query the Knowledge Graph for project assumptions, constraints, and scope boundaries that define the basis for the estimate. This content spans 3 slides, each covering a different category group of assumptions.

**Table structure reminder:**
- Each slide is a 2-column table in the template
- **Col 0 (FIXED, do NOT write):** category labels (開発方針, 品質戦略…) — preserved from template
- **Col 1 (FILL):** the assumption detail for that category
- Markdown format: single-column table, one row per category, in the same order as the fixed labels

**Step 12.1: Query for Development & Quality Assumptions**

Query the Knowledge Graph:

```json
{
  "project_id": "<project_id>",
  "query": "開発方針 開発スタイル 品質戦略 テスト方針 開発言語 技術スタック 機能要件 非機能要件 制約事項 前提条件 見積前提"
}
```

**From the result, extract content for each of the 5 rows in Slide 23:**
1. **開発方針** — development methodology, style, approach (e.g., agile, waterfall, hybrid)
2. **品質戦略** — quality assurance strategy, test scope, exception handling policy
3. **開発言語** — programming languages and frameworks to be used
4. **機能要件** — functional scope assumptions (what is/isn't included, API assumptions, etc.)
5. **非機能要件** — non-functional assumptions (security, operations, deployment, SLA, etc.)

> Only use information found in the KG. If a category has no data, leave it blank (empty). Do NOT write placeholder or sample content.

**Step 12.2: Query for Design, External APIs, and Other Constraints**

Query the Knowledge Graph:

```json
{
  "project_id": "<project_id>",
  "query": "デザイン UI/UX 坓面数 プロトタイプ 外部API 外部サービス連携 その他前提 スコープ外 この見積に含まない"
}
```

**From the result, extract content for each of the 3 rows in Slide 24:**
1. **デザイン** — UI/UX scope and constraints (screen count, prototype scope, design system limits)
2. **外部API** — external service integration assumptions (existing APIs, third-party services)
3. **その他** — other miscellaneous assumptions (scope adjustments, release management, data access, etc.)

**Step 12.3: Query for Infrastructure Assumptions**

Query the Knowledge Graph:

```json
{
  "project_id": "<project_id>",
  "query": "インフラ前提 クラウド環境 オンプレミス サーバー構成 インフラ保守 運用 モニタリング パッチ適用 保守運用体制"
}
```

**From the result, extract content for the single row in Slide 25:**
1. **インフラ** — infrastructure assumptions (cloud vs on-premise, environment setup, maintenance scope by case/approach)

**Step 12.4: Generate Content for Slides 23, 24, 25**

**CRITICAL: Use `Edit` tool to append content**

**Append to:** `outputs/slides_{project_id}_{timestamp}.md`

**Format to append (replace bracketed values with KG-derived content):**

```markdown
<!-- FILL_SLIDE: 23 -->
<!-- SHAPE: assumptions_table_23 -->
| [開発方針の内容] |
| [品質戦略の内容] |
| [開発言語の内容] |
| [機能要件の内容] |
| [非機能要件の内容] |

<!-- FILL_SLIDE: 24 -->
<!-- SHAPE: assumptions_table_24 -->
| [デザインの内容] |
| [外部APIの内容] |
| [その他の内容] |

<!-- FILL_SLIDE: 25 -->
<!-- SHAPE: assumptions_table_25 -->
| [インフラの内容] |
```

**Content generation rules:**
- Each row maps **positionally** to the fixed label in col 0 — row 1 → label 1, row 2 → label 2, etc.
- Write bullet points starting with `・` for each cell
- Do NOT restate the category label in the cell content
- Keep each cell concise — 1-5 bullet points, each max ~60 characters
- Use line breaks (`\n`) within a cell to separate bullet points if needed
- Do NOT invent or assume content — only use what the KG provides; if a row has no data, leave it blank (empty)

**Step 12.5: Confirm and Continue**

Save the updated file and display message:
```
=== Step 12: Generate Slides 23, 24 & 25 - Estimated Assumptions ===
Querying KG for development/quality assumptions...
Querying KG for design/API/other assumptions...
Querying KG for infrastructure assumptions...

Generated assumption tables:
  ✓ Slide 23 (assumptions_table_23): 5 rows (開発方針 / 品質戦略 / 開発言語 / 機能要件 / 非機能要件)
  ✓ Slide 24 (assumptions_table_24): 3 rows (デザイン / 外部API / その他)
  ✓ Slide 25 (assumptions_table_25): 1 row (インフラ)

Added Slides 23, 24 & 25 to outputs/slides_{project_id}_{timestamp}.md

→ Proceeding to Slide 33...
```

---

