## Purpose
Generate presentation content by analyzing project data from Knowledge Graph.

## Output Target (v3 — 2-step flow)

**This reference covers profile sections, not slides.** Data extracted here flows into the JSON profile passed to `scripts/gen-md.py`, which produces `outputs/project_content_{id}_{ts}.md`. Slide rendering happens later in Step B via `gen-slide.py`.

Sections covered here map to:

| Profile section | Schema path | Old slide(s) |
|-----------------|-------------|--------------|
| `project_background` | `BackgroundSection {current_issues, objectives}` | Slide 4 |
| `features` | `FeaturesSection {description, table[]}` | Slide 5 |
| `nfr_overview` | `NFROverviewSection {description, table[]}` | Slide 6 |

**Ignore** any `FILL_SLIDE:` / `SHAPE:` markers in legacy text below — write each piece of content into the corresponding JSON section instead. The `Generate Slide N` framing is preserved for query semantics only.

---


## Execution Workflow

### **CRITICAL: Automatic Sequential Execution**

**This workflow will execute ALL steps automatically in sequence:**
1. Start with Step 0 (Get Project ID)
2. Automatically proceed through Steps 1-17 (Generate all slides)
3. Each step generates content for ONE specific slide
4. After completing each step, show completion message and automatically continue to next step
5. Complete with Step 18 (Finalize markdown + images, show PPTX generation instructions)

**Agent must:**
- Execute all steps in order without stopping
- Generate each slide completely before moving to next
- Show progress message after each slide
- Automatically proceed to next slide generation
- **CRITICAL: For all steps after Slide 5, use `Edit` tool to append content to the markdown file**
  - Append new slide content to the end of the file using `Edit` tool
  - **DO NOT use `cat`, `echo`, or any terminal commands that require user confirmation**
  - **EXCEPTION: Step 7 (Slide 8 image) and Step 17 (Slide 43 image)** — use Python heredoc or Bash to save Mermaid `.mmd` files and generate PNG via Mermaid CLI. All other steps always use `Edit`.
- After all slides are generated, automatically run the Python script to create PowerPoint
- DO NOT create a separate `.py` file - execute the script directly using terminal
- Only stop when all slides and PowerPoint file are complete

---



### **Step 0: Get Project ID**

**Check if `.clio.yml` config file exists in the current directory:**

1. **Look for `.clio.yml` file** in the current working directory
2. **If file exists:**
   - Read the content of `.clio.yml`
   - Extract `project_id` from the config (format: `project_id: xxx`)
   - Use this `project_id` for all subsequent Knowledge Graph queries
3. **If file does NOT exist:**
   - Ask user for `project_id` if not provided in the request

**Example `.clio.yml` content:**
```yaml
project_id: hayate
```

**Action:**
- Use `Read` tool to check and read `.clio.yml`
- Parse the YAML content to extract `project_id` value
- Store the project_id for use in all subsequent steps

---



### **Step 1: Query for Current Issues & Pain Points**

**Goal:** Extract information about customer's current situation, problems, and challenges.

Execute the following query using `clio_query` MCP tool tool:

```
{
  "project_id": "<project_id>",
  "query": "顧客の現状の課題 問題点 ペインポイント 背景 現在の状況 契約形態 開発体制 制約 困っていること 改善したい点 システム開発の課題"
}
```

**Analyze the result:**
- Extract information about current contract type (請負契約, 準委任契約, etc.)
- Identify current development methodology issues (WF開発, アジャイル, etc.)
- Note communication/collaboration challenges
- Capture flexibility limitations
- Document any operational pain points
- Extract customer frustrations or inefficiencies

**If insufficient information is returned:**
Run a follow-up query:
```
{
  "project_id": "<project_id>",
  "query": "プロジェクトの背景 なぜこのプロジェクトが必要 現行システムの問題 ビジネス上の課題 ユーザーの不満 改善が必要な理由"
}
```

**Synthesize the findings into Japanese narrative:**
- Start with overall context/background (1-2 sentences)
- List specific current issues (現状の課題) as **3-4 bullet points**
- Each bullet point should express one main problem or need
- **Total length: maximum 80 words**
- Writing style: concise, clear, business-focused
- Do NOT add new information, only extract core points from provided content
- Focus on problems that need solving

---



### **Step 2: Query for Project Objectives & Goals**

**Goal:** Extract information about what the customer wants to achieve, project goals, and desired outcomes.

Execute the following query using `clio_query` MCP tool tool:

```
{
  "project_id": "<project_id>",
  "query": "プロジェクトの目的 目標 実現したいこと 期待される成果 達成したい状態 ビジョン ゴール 改善目標 エンドユーザー 協力体制 パートナーシップ"
}
```

**Analyze the result:**
- Extract project purpose and vision
- Identify specific goals to achieve
- Note desired collaboration models
- Capture expected outcomes
- Document target user benefits
- Extract partnership/cooperation objectives

**If insufficient information is returned:**
Run a follow-up query:
```
{
  "project_id": "<project_id>",
  "query": "プロジェクトで解決したい課題 期待される効果 成功の定義 KPI ユーザーに提供したい価値 ビジネス価値"
}
```

**Synthesize the findings into Japanese narrative:**
- State overall project purpose (1-2 sentences)
- List specific objectives (目的・実現したいこと) as **3-4 bullet points**
- Each bullet point should express one main goal or desired outcome
- **Total length: maximum 80 words**
- Writing style: concise, clear, business-focused
- Do NOT add new information, only extract core points from provided content
- Focus on positive outcomes and goals

---



### **Step 3: Generate Slide 4 Markdown Content**

Using the information gathered from Steps 1 and 2, create a `.md` file with the following structure:

**Filename:** `outputs/slides_{project_id}_{timestamp}.md`
**Timestamp format:** `YYYYMMDD_HHMMSS` (e.g., 20251217_143000)

**Content structure:**

```markdown
<!-- FILL_SLIDE: 4 -->

<!-- SHAPE: current_issues -->
[Insert synthesized current issues content here]
現状の課題：
- [Issue point 1]
- [Issue point 2]
- [Issue point 3]
- [Additional issues as needed]

<!-- SHAPE: objectives -->
[Insert synthesized objectives content here]
目的・実現したいこと：
- [Objective 1]
- [Objective 2]
- [Objective 3]
- [Additional objectives as needed]

```

**Content guidelines:**
- Use natural Japanese writing style
- Start each SHAPE section with a brief context paragraph (1-2 sentences)
- Follow with bulleted list of **3-4 specific points only**
- **Total content per section: maximum 80 words**
- Each bullet should be concise (one line or short phrase)
- Focus on clarity and relevance to the customer
- Ensure content reflects actual KG data, not generic statements
- Do NOT add information beyond what was found in the Knowledge Graph

---



### **Step 4: Save and Confirm Slide 4**

1. **Save the file** to `outputs/slides_{project_id}_{timestamp}.md`
2. **Show completion message:**
   ```
   Slide 4 content added to markdown file!

   File: outputs/slides_{project_id}_{timestamp}.md

   Slide 4 includes:
   - Current Issues: [X] points
   - Objectives: [Y] points

   Based on Knowledge Graph data for project: {project_id}

   → Proceeding to generate Slide 5...
   ```

---



### **Step 5: Generate Slide 5 - Function List Table**

**Goal:** Append Slide 5 content to the same markdown file.

**Action 1: Find the function_list file**

Look for function list file in outputs directory:
```bash
ls -t outputs/function_list_*.csv | head -1
```

**If function_list file EXISTS → go to Action 2.**

**If no function_list file exists → Query Clio KG (Action 1b):**

**Action 1b: Query Clio KG for function/feature information**

Execute the following queries using `clio_query` MCP tool:

**Query 1: Core features & functions**
```
{
  "project_id": "<project_id>",
  "query": "システムの主要機能 機能一覧 画面機能 業務機能 機能要件 処理フロー CRUD操作 API連携 画面遷移 入力検証 ビジネスロジック"
}
```

**Query 2: Screen-level feature details**
```
{
  "project_id": "<project_id>",
  "query": "各画面の機能 画面名 機能名 操作 ボタン 入力項目 データ登録 データ検索 データ更新 削除 バリデーション"
}
```

**If queries return results:**
- Fields that **exist in KG data** → use **exactly as returned**, do NOT rephrase or change
- Fields that **do not exist in KG data** → infer/generate from context (screen name, category, related info)
- Extract function names, screen names, categories, descriptions directly from query results
- Map the extracted data to the table format in Action 4

**If queries return no results:**
```
No function data found in Knowledge Graph and no function_list file exists.
Skipping Slide 5.
Note: Run tkm:estimate skill to generate function_list_*.csv first.
```
Skip to Step 6.

**Action 2: Parse and analyze the function_list CSV**

Read the CSV file and extract:
- Function ID
- Function Name
- Screen
- Category
- Description
- Dependencies

**Action 3: Select representative functions (8-10 items)**

Selection criteria:
- Cover diverse categories (UI, CRUD, API, Validation, Navigation, Logic)
- Prioritize high-impact/core functions
- Include at least one function from each major screen/subsystem
- Balance complexity (mix of simple and complex functions)

**Action 4: Transform to Slide 5 format**

Map function data to table columns:
- **No**: Sequential number (1, 2, 3...)
- **カテゴリ**: Category in Japanese
  - UI → 画面表示
  - CRUD-Create → データ登録
  - CRUD-Read → データ取得
  - CRUD-Update → データ更新
  - CRUD-Delete → データ削除
  - API → API連携
  - Validation → 入力検証
  - Navigation → 画面遷移
  - Logic → ビジネスロジック
- **PID**: Create short ID (e.g., AU-01, US-02, PD-03)
  - Use 2-letter prefix from screen/category + sequential number
- **画面・機能**: Screen name + Function name (concise)
- **機能要件**: Function description (business-focused, concise)
- **詳細**: Technical details, constraints, or special notes

**Action 5: Append Slide 5 to existing markdown file**

**Append to:** `outputs/slides_{project_id}_{timestamp}.md`

**Content example to append:**

```markdown

<!-- FILL_SLIDE: 5 -->

<!-- SHAPE: feature_description -->
システムの主要機能を以下の通り定義しました。各機能はカテゴリ別に分類され、画面・機能要件・技術詳細が明確化されています。

<!-- SHAPE: function_summary -->
| No | カテゴリ | PID | 画面・機能 | 機能要件 | 詳細 |
|----|----------|-----|------------|----------|------|
| 1 | 認証・認可 | AU-01 | ログイン画面 | ユーザーがIDとPWでログインできる | JWT発行、リフレッシュトークン対応 |
| 2 | データ取得 | DS-02 | 配車計画一覧 | 月次・日次の配車計画を一覧表示 | ページネーション、検索・フィルタ機能 |
| 3 | データ登録 | DP-03 | 月次配車登録 | 初期マスタから路線を登録 | ルート選択、バリデーション |
| 4 | 入力検証 | VL-04 | 配車入力検証 | 必須項目・日付範囲をチェック | リアルタイム検証、エラー表示 |
| 5 | API連携 | AP-05 | BOSS連携API | 配車データをBOSSシステムに送信 | REST API、エラーハンドリング |
| 6 | ビジネスロジック | BL-06 | コスト計算 | チャーターコストを自動計算 | 料金マスタ参照、消費税計算 |
| 7 | 画面遷移 | NV-07 | メニュー遷移 | メインメニューから各機能へ遷移 | ロールベースアクセス制御 |
| 8 | データ更新 | UP-08 | 実績データ更新 | 運行実績データを更新・修正 | 楽観的ロック、履歴管理 |
```

**Content guidelines:**
- Select **8-10 representative functions only** (not all functions)
- Each row should be concise and business-focused
- 機能要件: Focus on "what" the function does (business perspective)
- 詳細: Technical details, constraints, or special considerations
- Ensure variety across categories
- Suitable for cost estimation purposes
- **IMPORTANT:** Use `<!-- SHAPE: feature_description -->` for intro text and `<!-- SHAPE: function_summary -->` for the table
- The parser only recognizes SHAPE markers, NOT TABLE markers

**Action 6: Automatically append and confirm**

**CRITICAL: Use `Edit` tool to append content:**
- Append the new slide content (from Action 5) to the end of the file: `outputs/slides_{project_id}_{timestamp}.md`
- **DO NOT use `cat`, `echo`, or terminal commands - these require user confirmation**

Save the updated file and display message:
```
Slide 5 content added to markdown file!

File: outputs/slides_{project_id}_{timestamp}.md

Slide 5 includes:
- Representative functions: [X] items
- Categories covered: [list of categories]

Based on function_list file for project: {project_id}

→ Proceeding to Slide 6...
```

---



### **Step 6: Generate Slide 6 - Non-Functional Requirements (Optional)**

**Goal:** Extract and summarize non-functional requirements if they exist in the project documentation.

**Action 1: Query for Non-Functional Requirements**

Execute the following query using `clio_query` MCP tool tool:

```
{
  "project_id": "<project_id>",
  "query": "非機能要件 性能要件 可用性 拡張性 セキュリティ要件 運用要件 保守性 システム品質 応答時間 処理性能 同時接続数 データバックアップ 障害対応"
}
```

**Analyze the result:**
- Extract performance requirements (性能要件)
- Identify availability requirements (可用性)
- Note scalability needs (拡張性)
- Capture security requirements (セキュリティ要件)
- Document operational requirements (運用要件)
- Extract maintainability requirements (保守性)

**If insufficient information is returned:**
Run a follow-up query:
```
{
  "project_id": "<project_id>",
  "query": "システム品質保証 応答時間 スループット 同時ユーザー数 バックアップ リカバリ 可用性目標 セキュリティ対策 暗号化 アクセス制御"
}
```

**Action 2: Evaluate if Slide 6 is needed**

**If non-functional requirements are found:**
- Proceed to create Slide 6
- Synthesize findings into structured format

**If no non-functional requirements are found:**
- Skip Slide 6 creation
- Display message:
  ```
  ℹNo non-functional requirements found in Knowledge Graph.
  Skipping Slide 6 (非機能要件).

  Note: Non-functional requirements can be proposed later in the
  architecture design section if needed.

  → Proceeding directly to Slide 12...
  ```

**Action 3: Synthesize Non-Functional Requirements (if found)**

**Categorize into main areas:**
1. **性能要件 (Performance Requirements)**
   - 応答時間 (Response time)
   - スループット (Throughput)
   - 同時接続数 (Concurrent connections)

2. **可用性 (Availability)**
   - 稼働時間目標 (Uptime target)
   - 障害復旧時間 (Recovery time)

3. **拡張性 (Scalability)**
   - ユーザー数の増加対応 (User growth)
   - データ量の増加対応 (Data growth)

4. **セキュリティ (Security)**
   - 認証・認可 (Authentication & Authorization)
   - データ暗号化 (Data encryption)
   - アクセス制御 (Access control)

5. **運用・保守性 (Operations & Maintenance)**
   - バックアップ (Backup)
   - 監視・ログ (Monitoring & Logging)
   - 保守対応 (Maintenance)

**Content guidelines:**
- Use bullet points format (3-5 points per category)
- Be specific with numbers/targets when available
- Keep descriptions concise and clear
- Focus on customer's actual requirements

**Action 4: Transform to Slide 6 table format**

Create a table with 10-14 rows covering key non-functional requirements:
- **#**: Sequential number (1, 2, 3...)
- **カテゴリ**: Category (パフォーマンス, 信頼性, セキュリティ, 運用性, 拡張性)
- **項目**: Specific item/metric
- **概要**: Quantitative description (time, %, conditions)
- **備考**: Additional notes, context, or constraints

**Content guidelines:**
- Select **10-14 representative requirements** covering all categories
- Focus on measurable, quantitative criteria
- Use specific values (< 3秒, >= 99.5%, AES-256, etc.)
- Each row should be clear and suitable for design/evaluation criteria
- Do NOT include functional requirements (login, CRUD, etc.)
- Ensure technical and business clarity
- **IMPORTANT:** Use `<!-- SHAPE: requirements_description -->` for intro text and `<!-- SHAPE: requirements_table -->` for the table
- The parser only recognizes SHAPE markers, NOT TABLE markers

**Action 5: Append Slide 6 to markdown file**

**Append to:** `outputs/slides_{project_id}_{timestamp}.md`

**Content example to append:**

```markdown

<!-- FILL_SLIDE: 6 -->

<!-- SHAPE: requirements_description -->
貴社よりご提示いただいた非機能要件書を基に、いくつかの前提を置かせていただきました。

<!-- SHAPE: requirements_table -->
| # | カテゴリ | 項目 | 概要 | 備考 |
|---|----------|------|------|------|
| 1 | パフォーマンス | 画面応答時間 | < 3秒 | 通常処理の画面表示完了まで |
| 2 | パフォーマンス | API応答時間 | < 1秒 | データ取得・更新処理 |
| 3 | パフォーマンス | 同時接続数 | 最大500ユーザー | ピーク時の同時アクセス対応 |
| 4 | パフォーマンス | データ処理量 | 10,000件/10分 | 月次配車データ一括処理 |
| 5 | 信頼性 | システム稼働率 | >= 99.5% | 月次平均、計画停止除く |
| 6 | 信頼性 | 障害復旧時間 | < 4時間 | 予期せぬ障害からの復旧目標 |
| 7 | 信頼性 | データ整合性 | 100% | トランザクション保証、ロールバック対応 |
| 8 | セキュリティ | 認証方式 | JWT + セッション管理 | トークンベース認証、有効期限管理 |
| 9 | セキュリティ | 通信暗号化 | TLS 1.2以上 | 全API通信の暗号化必須 |
| 10 | セキュリティ | データ暗号化 | AES-256 | 個人情報・機密データ対象 |
| 11 | セキュリティ | アクセス制御 | RBAC | ロールベース権限管理 |
| 12 | 運用性 | バックアップ頻度 | 日次フルバックアップ | トランザクションログ併用 |
| 13 | 運用性 | ログ保管期間 | 3年間 | 操作ログ・エラーログ・監査ログ |
| 14 | 運用性 | 監視・アラート | リアルタイム監視 | 異常検知時の即時通知 |
| 15 | 拡張性 | スケーラビリティ | 水平スケーリング対応 | ユーザー数・データ量の増加対応 |
```

**Action 6: Automatically append and confirm**

**CRITICAL: Use `Edit` tool to append content:**
- Append the new slide content (from Action 5) to the end of the file: `outputs/slides_{project_id}_{timestamp}.md`
- **DO NOT use `cat`, `echo`, or terminal commands - these require user confirmation**

Save the updated file and display message:
```
Slide 6 content added to markdown file!

File: outputs/slides_{project_id}_{timestamp}.md

Slide 6 includes:
- Non-functional requirements table: [X] items
- Categories covered: パフォーマンス, 信頼性, セキュリティ, 運用性, 拡張性

Based on non-functional requirements document for project: {project_id}

→ Proceeding to Slide 8...
```

---

