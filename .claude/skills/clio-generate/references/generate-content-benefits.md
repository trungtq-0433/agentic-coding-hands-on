## Output Target (v3 — 2-step flow)

**This reference covers the `benefits` profile section.** Data extracted here flows into JSON as a list of benefit blocks (each with `title` + `content`). Step B's renderer splits them across slides automatically (`benefits[0:2]` → slide 12, `benefits[2:4]` → slide 13).

| Profile section | Schema | Old slide(s) |
|-----------------|--------|--------------|
| `benefits` | `list[BenefitSection {title, content}]` | Slides 12, 13 |

**Ignore** any `FILL_SLIDE:` / `SHAPE:` markers below — populate the JSON list. Aim for 4 benefit entries (cost / efficiency / security / integration are the conventional four).

---

### **Step 9: Generate Slide 12 - System Benefits (システムの導入のメリット)**

**Goal:** Analyze business process changes and generate benefits summary for digital transformation.

**Action 1: Query for Business Process Changes**

Execute the following query using `clio_query` MCP tool tool:

```
{
  "project_id": "<project_id>",
  "query": "業務プロセス改善 ビジネスプロセス変更 デジタルトランスフォーメーション 業務効率化 自動化 ワークフロー簡素化 コスト削減 生産性向上 品質改善 エラー削減 手作業削減 業務標準化"
}
```

**Analyze the result:**
- Extract information about manual processes → automated processes
- Identify workflow simplification points
- Note efficiency improvements
- Capture cost reduction opportunities
- Document quality improvements (error reduction)
- Extract employee productivity impacts

**If insufficient information is returned:**
Run a follow-up query:
```
{
  "project_id": "<project_id>",
  "query": "現行の手作業 業務改善効果 システム導入効果 業務フロー改善 作業時間短縮 人的コスト削減 ミス削減効果"
}
```

**Action 2: Categorize Benefits into Two Main Areas**

Based on the analysis, create content for two benefit categories:

**1. 削減されるコスト (Cost Reduction)**
Focus on:
- 人的コスト削減 (Human resource cost reduction)
- 入力ミス・再作業の抑制 (Error and rework reduction)
- インフラコスト最適化 (Infrastructure cost optimization)
- クラウド活用によるコスト削減 (Cloud cost savings)

**2. 業務効率 (Business Efficiency)**
Focus on:
- 処理時間の短縮 (Processing time reduction)
- コア業務への集中 (Focus on core business)
- プロセス標準化 (Process standardization)
- 自動化による生産性向上 (Automation productivity gains)

**Content guidelines:**
- Each section: **2 lines maximum**
- Business-focused, professional tone
- Specific and measurable benefits when possible
- Connect directly to the business process changes identified
- Clear and concise Japanese
- Focus on tangible outcomes

**Action 3: Generate Slide 12 Content**

**Append to:** `outputs/slides_{project_id}_{timestamp}.md`

**Content to append:**

```markdown

<!-- FILL_SLIDE: 12 -->

<!-- SHAPE: benefit_title_1 -->
削減されるコスト

<!-- SHAPE: benefit_content_1 -->
作業の自動化により人的コストを削減し、入力ミスや再作業の発生も抑制されます。
また、クラウド活用により、サーバーやインフラ費用を最小限に抑えることができます。

<!-- SHAPE: benefit_title_2 -->
業務効率

<!-- SHAPE: benefit_content_2 -->
手作業の削減により処理時間が短縮され、従業員はコア業務に集中できます。
業務プロセスの標準化により、作業の属人化を防ぎ、チーム全体の生産性を向上します。
```

**Content generation rules:**
- **Shape 3 (benefit_title_1):** Section 1 title - 削減されるコスト
- **Shape 4 (benefit_content_1):** Section 1 content - Exactly 2 lines about cost reduction
- **Shape 5 (benefit_title_2):** Section 2 title - 業務効率
- **Shape 6 (benefit_content_2):** Section 2 content - Exactly 2 lines about business efficiency

**Other possible benefit categories (for reference):**
- セキュリティ向上 (Security improvement)
- 顧客満足度向上 (Customer satisfaction improvement)
- 意思決定の迅速化 (Faster decision making)
- データ活用の推進 (Data utilization promotion)
- コンプライアンス強化 (Compliance enhancement)

**Choose the two most relevant categories based on the project context from Knowledge Graph.**

**Action 4: Save and confirm**

**CRITICAL: Use `Edit` tool to append content:**
- Append the new slide content (from Action 3) to the end of the file: `outputs/slides_{project_id}_{timestamp}.md`
- **DO NOT use `cat`, `echo`, or terminal commands - these require user confirmation**

Save the updated file and display message:
```
Slide 12 content added to markdown file!

File: outputs/slides_{project_id}_{timestamp}.md

Slide 12 includes:
- Section 1: 削減されるコスト (Cost Reduction)
- Section 2: 業務効率 (Business Efficiency)

Based on business process analysis for project: {project_id}

→ Proceeding to Slide 13...
```

---



### **Step 10: Generate Slide 13 - Additional System Benefits**

**Goal:** Add two more benefit categories to provide comprehensive value proposition.

**Action 1: Continue analyzing benefits from Knowledge Graph**

Based on the same business process analysis from Step 7, identify two additional benefit categories:

**Common additional benefit categories:**

1. **向上するセキュリティ (Security Improvement)**
   - ユーザー権限管理強化
   - データ暗号化
   - アクセス制御
   - コンプライアンス対応
   - 操作ログ・監査証跡

2. **連携されるシステムとその効果 (System Integration)**
   - 既存システムとの連携
   - データ一元管理
   - リアルタイム同期
   - 情報共有の円滑化
   - 部門間連携強化

3. **顧客満足度向上 (Customer Satisfaction)**
   - 待ち時間短縮
   - サービス品質向上
   - 契約プロセス迅速化
   - 顧客対応の改善
   - リテンション率向上

4. **データ活用の推進 (Data Utilization)**
   - リアルタイムデータ分析
   - 意思決定の迅速化
   - レポート自動生成
   - KPI可視化
   - 予測分析機能

**Select the two most relevant additional categories based on:**
- Project-specific requirements
- Industry characteristics
- Customer priorities from KG data
- Digital transformation objectives

**Action 2: Generate Slide 13 Content**

**Append to:** `outputs/slides_{project_id}_{timestamp}.md`

**Content example to append:**

```markdown

<!-- FILL_SLIDE: 13 -->

<!-- SHAPE: benefit_title_3 -->
向上するセキュリティ

<!-- SHAPE: benefit_content_3 -->
ユーザー権限管理やデータ暗号化により、不正アクセスや情報漏洩リスクを低減します。
操作ログの記録により、コンプライアンス要件への対応と監査証跡の確保が可能になります。

<!-- SHAPE: benefit_title_4 -->
連携されるシステムとその効果

<!-- SHAPE: benefit_content_4 -->
既存の会計ソフトやチャットツールなどと連携し、情報の一元管理と作業効率化を実現します。
リアルタイムデータ同期により、部門間の情報共有がスムーズになり意思決定が迅速化されます。
```

**Content generation rules:**
- **Shape 3 (benefit_title_3):** Section 3 title - Choose from benefit categories above
- **Shape 4 (benefit_content_3):** Section 3 content - Exactly 2 lines
- **Shape 5 (benefit_title_4):** Section 4 title - Second benefit category
- **Shape 6 (benefit_content_4):** Section 4 content - Exactly 2 lines

**Alternative benefit examples:**

**For Customer-Facing Systems:**
```markdown
<!-- SHAPE: benefit_title_3 -->
顧客満足度向上

<!-- SHAPE: benefit_content_3 -->
システムの応答速度向上により、顧客の待ち時間が大幅に短縮されます。
オンライン対応の拡充により、24時間365日のサービス提供が可能になります。

<!-- SHAPE: benefit_title_4 -->
データ活用の推進

<!-- SHAPE: benefit_content_4 -->
リアルタイムダッシュボードにより、経営指標の即時把握と迅速な意思決定が可能です。
顧客行動分析により、マーケティング施策の最適化と売上向上が期待できます。
```

**Action 3: Save and confirm**

**CRITICAL: Use `Edit` tool to append content:**
- Append the new slide content (from Action 2) to the end of the file: `outputs/slides_{project_id}_{timestamp}.md`
- **DO NOT use `cat`, `echo`, or terminal commands - these require user confirmation**

Save the updated file and display message:
```
Slide 13 content added to markdown file!

File: outputs/slides_{project_id}_{timestamp}.md

Slide 13 includes:
- Section 3: 向上するセキュリティ (Security Improvement)
- Section 4: 連携されるシステムとその効果 (System Integration)

Total benefit sections: 4 (Slides 12 & 13)
---



→ Proceeding to Slide 21...
```

---

