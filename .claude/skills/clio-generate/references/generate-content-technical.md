## Output Target (v3 — 2-step flow)

**This reference covers all technical sections.** Data extracted here flows into the JSON profile:

| Profile section | Schema | Old slide(s) |
|-----------------|--------|--------------|
| `infrastructure` | `list[dict]` (rows of infra config; columns become table headers) | Slide 33 |
| `software_stack` | `list[dict]` (rows of software/version) | Slide 34 |
| `nfr_sections` | `list[NFRSection {title, body}]` — Performance / Maintainability / Scalability / Availability | Slide 35 |
| `nfr_detailed` | `list[dict]` (multi-column NFR table; overflow handled automatically) | Slide 36 |
| `schedule` | `ScheduleSection {description, image_path}` (Gantt PNG path) | Slide 43 |

**Ignore** any `FILL_SLIDE:` / `SHAPE:` markers below — populate the JSON sections. PNG images: pass file paths in `schedule.image_path`.

---

### **Step 13: Generate Slide 33 - Infrastructure Configuration Proposal**

**Goal:** Generate infrastructure configuration proposal table (インフラ構成) explaining HOW to implement the system with specific cloud services.

**Step 13.1: Query KG for Infrastructure Requirements**

Query the Knowledge Graph for infrastructure and non-functional requirements:

```
{
  "project_id": "<project_id>",
  "query": "インフラ要件 非機能要件 可用性 スケーラビリティ セキュリティ 運用 コスト AWS GCP Azure クラウド インフラストラクチャ アーキテクチャ Kubernetes コンテナ データベース ストレージ ネットワーク 監視 ログ管理"
}
```

**Step 13.2: Analyze Infrastructure Requirements**

Analyze the retrieved data to identify infrastructure needs across 5 key categories:

1. **可用性・スケーラビリティ** (Availability & Scalability)
   - High availability requirements (SLA targets)
   - Auto-scaling needs
   - Load distribution

2. **データ保護・セキュリティ** (Data Protection & Security)
   - Data encryption requirements
   - Access control needs
   - Backup and disaster recovery

3. **モニタリング・ログ管理** (Monitoring & Log Management)
   - System monitoring requirements
   - Log aggregation needs
   - Alerting requirements

4. **コスト最適化** (Cost Optimization)
   - Resource efficiency needs
   - Cost control requirements
   - Usage optimization

5. **ネットワーク・接続** (Network & Connectivity)
   - Network isolation requirements
   - Connectivity needs
   - Security groups/firewall

**Step 13.3: Propose Infrastructure Services**

For each category, propose specific cloud services with technical rationale:

**Example Proposals:**

**Category: 可用性・スケーラビリティ**
- **Service:** AWS ECS Fargate + Application Load Balancer
- **Rationale:**
  - ECSでコンテナベースの自動スケーリング実現 ・マルチAZ配置で99.99%可用性保証 ・ALBで負荷分散とヘルスチェック自動化

**Category: データ保護・セキュリティ**
- **Service:** Amazon Aurora Multi-AZ + Amazon S3 (Glacier)
- **Rationale:**
  - Aurora Multi-AZで自動フェイルオーバー ・暗号化(AES-256)でデータ保護 ・S3 Glacierで長期バックアップ(7年保管)

**Category: モニタリング・ログ管理**
- **Service:** CloudWatch + CloudWatch Logs Insights
- **Rationale:**
  - リアルタイムメトリクス監視 ・ログ集約と高度な分析クエリ ・異常検知とアラート自動通知

**Category: コスト最適化**
- **Service:** AWS Cost Explorer + Auto Scaling
- **Rationale:**
  - コスト可視化とRI/Savings Plans最適化 ・需要に応じた自動スケーリングで無駄削減 ・予算アラートで超過防止

**Category: ネットワーク・接続**
- **Service:** Amazon VPC + Security Groups + PrivateLink
- **Rationale:**
  - VPCでネットワーク分離とセキュリティ強化 ・Security Groupsで細かいアクセス制御 ・PrivateLinkでセキュアなサービス接続

**Step 13.4: Generate Slide 33 Markdown Table**

Generate markdown table with 3 columns:

**Table Structure:**
- **Column 1:** # (Number)
- **Column 2:** カテゴリ (Category)
- **Column 3:** 提案理由 (Proposal Rationale)

**Formatting Rules:**
1. Use `<!-- FILL_SLIDE: 33 -->` marker
2. Use `<!-- SHAPE: infrastructure_configuration_table -->` for table content
3. Create 5-8 rows (one per category or sub-category)
4. Use bullet points with `・` character, all on one line separated by spaces
5. NO line breaks within table cells - each cell must be on a single line
6. NO `<br>` tags - use plain text only
7. NO `**` bold markers - use plain text
8. Include specific service names (AWS ECS, Aurora, CloudWatch, etc.)
9. Focus on technical benefits and specific capabilities
10. Format must match Slide 5 and Slide 6 tables (one row per line, one cell per line)

**Example Output:**

```markdown
<!-- FILL_SLIDE: 33 -->

<!-- SHAPE: infrastructure_configuration_table -->
| # | カテゴリ | 提案理由 |
|---|---------|----------|
| 1 | 可用性・スケーラビリティ | AWS ECS Fargate + ALB ・ECSでコンテナベースの自動スケーリング実現 ・マルチAZ配置で99.99%可用性保証 ・ALBで負荷分散とヘルスチェック自動化 |
| 2 | データ保護・セキュリティ | Amazon Aurora Multi-AZ + S3 Glacier ・Aurora Multi-AZで自動フェイルオーバー ・暗号化(AES-256)でデータ保護 ・S3 Glacierで長期バックアップ(7年保管) |
| 3 | モニタリング・ログ管理 | CloudWatch + CloudWatch Logs Insights ・リアルタイムメトリクス監視 ・ログ集約と高度な分析クエリ ・異常検知とアラート自動通知 |
| 4 | コスト最適化 | AWS Cost Explorer + Auto Scaling ・コスト可視化とRI/Savings Plans最適化 ・需要に応じた自動スケーリングで無駄削減 ・予算アラートで超過防止 |
| 5 | ネットワーク・接続 | Amazon VPC + Security Groups + PrivateLink ・VPCでネットワーク分離とセキュリティ強化 ・Security Groupsで細かいアクセス制御 ・PrivateLinkでセキュアなサービス接続 |
<!-- END SHAPE -->
```

**Step 13.5: Validate and Save Slide 33**

**CRITICAL: Use `Edit` tool to append content:**
- Append the new slide content (from Step 13.4) to the end of the file: `outputs/slides_{project_id}_{timestamp}.md`
- **DO NOT use `cat`, `echo`, or terminal commands - these require user confirmation**

Content validation checks:
- Verify `<!-- FILL_SLIDE: 33 -->` marker exists
- Verify `<!-- SHAPE: infrastructure_configuration_table -->` marker exists
- Check table structure has 3 columns
- Verify bullet points use `・` character
- Confirm service names are included (AWS, ECS, Aurora, CloudWatch, VPC, etc.)
- Ensure minimum 5 rows in table

**Expected console output:**
```
=== Step 13: Generate Slide 33 - Infrastructure Configuration ===

Querying KG for infrastructure requirements...
Retrieved non-functional requirements and infrastructure constraints

Analyzing infrastructure categories:
  1. 可用性・スケーラビリティ (Availability & Scalability)
  2. データ保護・セキュリティ (Data Protection & Security)
  3. モニタリング・ログ管理 (Monitoring & Logs)
  4. コスト最適化 (Cost Optimization)
  5. ネットワーク・接続 (Network & Connectivity)

Generating infrastructure proposal table...
Created proposal with 5 categories × specific cloud services

Content validation:
  ✓ fill_slide_marker
  ✓ shape_marker
  ✓ table_structure
  ✓ bullet_points
  ✓ line_breaks
  ✓ service_names
  ✓ min_rows

 Added Slide 33 to outputs/slides_{project_id}_{timestamp}.md

→ Proceeding to Slide 34...
```

---



### **Step 14: Generate Slide 34 - Software Configuration / Tech Stack**

**Goal:** Generate software configuration table (ソフトウェア構成) explaining application-level tech stack with rationale.

**Step 14.1: Query KG for Technology Stack Requirements**

Query the Knowledge Graph for technology, framework, and tooling information:

```
{
  "project_id": "<project_id>",
  "query": "開発言語 フレームワーク プログラミング言語 技術スタック フロントエンド バックエンド API データベース CI/CD GitHub GitLab ソースコード管理 テスト 自動化 デプロイメント インフラ管理 IaC Terraform システムアーキテクチャ マイクロサービス モノリス 認証 セキュリティ 監視 ログ"
}
```

**Step 14.2: Analyze Software Components**

Analyze the retrieved data to identify key software components across 6-8 categories:

1. **フロントエンド開発言語/フレームワーク** (Frontend Language/Framework)
   - Language: JavaScript/TypeScript
   - Framework: React, Vue, Angular, Next.js, Nuxt.js
   - Focus: Performance, SEO, maintainability, security (XSS prevention)

2. **バックエンド開発言語/フレームワーク** (Backend Language/Framework)
   - Language: Node.js, Java, Python, Go, .NET
   - Framework: NestJS, Express, Spring Boot, Django, FastAPI
   - Focus: Type safety, scalability, testability, authentication compatibility

3. **ソースコード管理** (Source Code Management)
   - Tool: GitHub, GitLab, Bitbucket
   - Process: PR workflow, code review, branch strategy
   - Focus: Quality assurance, collaboration

4. **CI/CD** (CI/CD Pipeline)
   - Tool: GitHub Actions, GitLab CI, Jenkins, CircleCI
   - Process: Automated lint/test/build/deploy
   - Focus: Release reproducibility, automation

5. **クラウドプラットフォーム** (Cloud Platform)
   - Platform: AWS, GCP, Azure
   - Focus: Managed services, operational stability, proven track record

6. **インフラ管理（IaC）** (Infrastructure Management / IaC)
   - Tool: Terraform, CloudFormation, Pulumi
   - Focus: Environment consistency, reduced operational burden

7. **システムアーキテクチャ** (System Architecture)
   - Pattern: Modular monolith, microservices, serverless
   - Focus: Maintainability, future extensibility

8. **Optional Components** (if applicable):
   - **テスト** (Testing): Jest, Pytest, JUnit
   - **監視** (Monitoring): CloudWatch, Datadog, New Relic
   - **認証方式** (Authentication): JWT, OAuth 2.0, SAML

**Step 14.3: Select Tech Stack with Rationale**

For each component, select specific technologies and provide rationale:

**Selection Criteria (prioritize):**
1. **安定性** (Stability) - Mature, proven in production
2. **セキュリティ** (Security) - Built-in security features, community support
3. **保守性** (Maintainability) - Clear documentation, active community, testability
4. **拡張性** (Extensibility) - Modular design, easy to scale

**Example Selections:**

**Frontend:**
```
・Next.js（React）を採用し、CSR/SSRの選択により表示性能とSEOを両立
・コンポーネント設計により保守性を確保し、XSS等のリスク低減に寄与
```

**Backend:**
```
・NestJS（Node.js + TypeScript）で型安全なAPI開発を実現
・DI/モジュール構成により拡張性・テスト容易性を向上
・JWT/OAuth等の認証方式と親和性が高い
```

**Source Control:**
```
・GitHubを採用し、PR運用とレビューによる品質担保を行う
```

**CI/CD:**
```
・GitHub ActionsでLint/Test/Build/Deployを自動化し、リリースの再現性を確保
```

**Cloud Platform:**
```
・AWSを採用し、運用実績とマネージドサービスで安定運用を実現
```

**IaC:**
```
・TerraformでIaCを行い、環境差異を排除して運用負荷を削減
```

**Architecture:**
```
・モジュラーモノリス（必要に応じて段階的に分割可能）で保守性と将来拡張を両立
```

**Step 14.4: Generate Slide 34 Markdown Table**

Generate markdown table with 3 columns:

**Table Structure:**
- **Column 1:** # (Number)
- **Column 2:** コンポーネント (Component)
- **Column 3:** 説明 (Description with rationale)

**Formatting Rules:**
1. Use `<!-- FILL_SLIDE: 34 -->` marker
2. Use `<!-- SHAPE: software_configuration_table -->` for table content
3. Create 6-8 rows (one per component)
4. Use bullet points with `・` character, all on one line separated by spaces
5. NO line breaks within table cells - each cell must be on a single line
6. NO `<br>` tags - use plain text only
7. NO `**` bold markers - use plain text
8. Specify concrete tech names (Next.js, NestJS, GitHub Actions, etc.)
9. Explain WHY chosen (focus on 安定性/セキュリティ/保守性/拡張性)
10. 2-4 bullet points per component
11. Format must match Slide 5 and Slide 6 tables (one row per line, one cell per line)

**Example Output:**

```markdown
<!-- FILL_SLIDE: 34 -->

<!-- SHAPE: software_configuration_table -->
| # | コンポーネント | 説明 |
|---|--------------|------|
| 1 | フロントエンド開発言語/フレームワーク | ・Next.js（React）を採用し、CSR/SSRの選択により表示性能とSEOを両立 ・コンポーネント設計により保守性を確保し、XSS等のリスク低減に寄与 |
| 2 | バックエンド開発言語/フレームワーク | ・NestJS（Node.js + TypeScript）で型安全なAPI開発を実現 ・DI/モジュール構成により拡張性・テスト容易性を向上 ・JWT/OAuth等の認証方式と親和性が高い |
| 3 | ソースコード管理 | ・GitHubを採用し、PR運用とレビューによる品質担保を行う |
| 4 | CI/CD | ・GitHub ActionsでLint/Test/Build/Deployを自動化し、リリースの再現性を確保 |
| 5 | クラウドプラットフォーム | ・AWSを採用し、運用実績とマネージドサービスで安定運用を実現 |
| 6 | インフラ管理 | ・TerraformでIaCを行い、環境差異を排除して運用負荷を削減 |
| 7 | システムアーキテクチャ | ・モジュラーモノリス（必要に応じて段階的に分割可能）で保守性と将来拡張を両立 |
<!-- END SHAPE -->
```

**Step 14.5: Validate and Save Slide 34**

**CRITICAL: Use `Edit` tool to append content:**
- Append the new slide content (from Step 14.4) to the end of the file: `outputs/slides_{project_id}_{timestamp}.md`
- **DO NOT use `cat`, `echo`, or terminal commands - these require user confirmation**

Content validation checks:
- Verify `<!-- FILL_SLIDE: 34 -->` marker exists
- Verify `<!-- SHAPE: software_configuration_table -->` marker exists
- Check table structure has 3 columns
- Verify bullet points use `・` character
- Confirm tech names are included (Next.js, React, NestJS, TypeScript, GitHub, AWS, Terraform, etc.)
- Ensure minimum 6 rows in table

**Expected console output:**
```
=== Step 14: Generate Slide 34 - Software Configuration ===

Querying KG for tech stack information...
Retrieved technology, framework, and tooling data

Analyzing software components:
  1. フロントエンド開発言語/フレームワーク (Frontend)
  2. バックエンド開発言語/フレームワーク (Backend)
  3. ソースコード管理 (Source Control)
  4. CI/CD (CI/CD Pipeline)
  5. クラウドプラットフォーム (Cloud Platform)
  6. インフラ管理 (IaC)
  7. システムアーキテクチャ (Architecture)

Generating software configuration table...
Created tech stack proposal with 7 components

Content validation:
  ✓ fill_slide_marker
  ✓ shape_marker
  ✓ table_structure
  ✓ bullet_points
  ✓ line_breaks
  ✓ tech_names
  ✓ min_rows

Added Slide 34 to outputs/slides_{project_id}_{timestamp}.md

→ Proceeding to Slide 35...
```

---



### **Step 15: Generate Slide 35 - Non-Functional Requirements (非機能要件)**

**Context:** When customer doesn't provide non-functional requirements (NFRs) in RFP, propose concise NFRs based on the project context from KG.

**Goal:** Generate 4 sections, each with exactly **5 short bullets**. Each bullet = 1 concise phrase (max ~25 chars). No long sentences.

**Step 15.1: Query Knowledge Graph for System Context**

```
{
  "project_id": "<project_id>",
  "query": "インフラ構成 AWS パフォーマンス スケーラビリティ 可用性 監視 CloudWatch Aurora ECS ALB 技術スタック フレームワーク デプロイメント CI/CD"
}
```

**Step 15.2: Content Rules**

- Each bullet: **key term + value/impact** — no filler phrases
- Format: `・[項目]：[値または効果]`
- Max ~30 chars per bullet
- Use `・` (middle dot), one line per bullet, no line breaks
- Write in formal Japanese

**Example Output:**

```markdown
<!-- FILL_SLIDE: 35 -->

<!-- SHAPE: performance_title -->
パフォーマンス（Performance）
<!-- END SHAPE -->

<!-- SHAPE: performance_body -->
・応答時間：< 0.5秒（コア操作）
・API：< 1秒
・同時接続：ピーク時300〜600ユーザー
・スループット：150 RPS以上
・体感速度：次画面表示 < 0.5秒
<!-- END SHAPE -->

<!-- SHAPE: maintainability_title -->
保守性（Maintainability）
<!-- END SHAPE -->

<!-- SHAPE: maintainability_body -->
・MTTR：障害復旧 < 2時間
・デプロイ：週1回以上の無停止リリース
・ログ保持：アプリ30日、監査90日
・監視カバレッジ：99.5%以上
・ドキュメント：Runbook・手順書整備
<!-- END SHAPE -->

<!-- SHAPE: scalability_title -->
スケーラビリティ（Scalability）
<!-- END SHAPE -->

<!-- SHAPE: scalability_body -->
・スケールアウト：< 5分で自動拡張
・インスタンス数：2〜6台で自動調整
・DB容量：初期100GB、最大1TB以上
・ストレージ：S3で無制限拡張
・負荷分散：ALBで均等分散
<!-- END SHAPE -->

<!-- SHAPE: availability_title -->
可用性（Availability）
<!-- END SHAPE -->

<!-- SHAPE: availability_body -->
・稼働率：99.99%以上
・RTO：障害復旧 < 4時間
・RPO：データ損失 < 1時間
・バックアップ：日次＋14世代保持
・構成：マルチAZ・マルチリージョン
<!-- END SHAPE -->
```

**Step 15.3: Validate and Save Slide 35**

**CRITICAL: Use `Edit` tool to append content:**
- Append the new slide content to the end of the file: `outputs/slides_{project_id}_{timestamp}.md`
- **DO NOT use `cat`, `echo`, or terminal commands - these require user confirmation**

Content validation:
- Verify `<!-- FILL_SLIDE: 35 -->` marker exists
- Verify all 8 SHAPE markers exist (4 titles + 4 bodies)
- Check each body section has exactly **5 bullets**
- Each bullet max ~30 chars, format `・[項目]：[値]`
- No long sentences, no `<br>` tags

**Expected console output:**
```
=== Step 15: Generate Slide 35 - Non-Functional Requirements ===

Querying KG for system context...

Generating concise NFR content (5 short bullets per section):
  1. パフォーマンス
  2. 保守性
  3. スケーラビリティ
  4. 可用性

 Added Slide 35 to outputs/slides_{project_id}_{timestamp}.md

→ Proceeding to Slide 36...
```

---



### **Step 16: Generate Slide 36 - Detailed Non-Functional Requirements Table (非機能要件・詳細版)**

**Context:** This slide is for deep technical evaluation (CTO / Tech Lead level) when NFRs are critical. Used in banking, payment, insurance, large-scale systems, or competitive technical bidding.

**Goal:** Generate comprehensive NFR table with quantitative metrics and technical explanations.

**Step 16.1: Query Knowledge Graph for Technical Context**

Execute the following queries using `clio_query` MCP tool tool:

**Query 1 - System Architecture:**
```
{
  "project_id": "<project_id>",
  "query": "インフラ構成 AWS ECS ALB Aurora RDS マルチAZ 可用性 バックアップ パフォーマンス CDN キャッシュ レイテンシ スループット TTFB セキュリティ 暗号化 TLS 認証 認可 RBAC 2FA モニタリング CloudWatch Datadog メトリクス ログ アラート スケーラビリティ オートスケール 水平スケール ロードバランシング 信頼性 災害復旧 RTO RPO MTTR"
}
```

**Query 2 - Tech Stack and Operations:**
```
{
  "project_id": "<project_id>",
  "query": "CI/CD パイプライン テスト コード品質 デプロイ ブルーグリーン コンテナ Docker Kubernetes ECS オーケストレーション IaC Terraform インフラコード 自動化"
}
```

**Step 16.2: Analyze 6 NFR Categories**

Analyze and determine detailed specifications for each category:

**1. パフォーマンス (Performance)**
- Web応答時間 (Web response time)
- APIレイテンシ (API latency)
- TTFB (Time To First Byte)
- スループット (Throughput)
- 同時接続数 (Concurrent connections)

**2. 可用性・信頼性 (Availability & Reliability)**
- 稼働率 (Uptime SLA)
- RTO (Recovery Time Objective)
- RPO (Recovery Point Objective)
- データ耐久性 (Data durability)
- エラー率 (Error rate)

**3. スケーラビリティ (Scalability)**
- 同時接続数 (Concurrent users)
- オートスケール時間 (Auto-scale time)
- データベース容量 (Database capacity)
- スケールアウト能力 (Scale-out capability)

**4. セキュリティ (Security)**
- データ暗号化 (Data encryption)
- 認証・認可 (Authentication & Authorization)
- 脆弱性対応 (Vulnerability response)
- アクセス制御 (Access control)
- 監査証跡 (Audit trail)

**5. 運用・監視 (Operations & Monitoring)**
- 障害検知時間 (Failure detection time)
- ログ保持期間 (Log retention period)
- モニタリングカバレッジ (Monitoring coverage)
- アラート設定 (Alert configuration)

**6. 保守性・品質 (Maintainability & Quality)**
- コード品質 (Code quality)
- テストカバレッジ (Test coverage)
- デプロイ頻度 (Deployment frequency)
- MTTR (Mean Time To Repair)
- ドキュメント整備 (Documentation)

**Step 16.3: Generate Detailed NFR Table Rows**

For each NFR item, generate table row with 5 columns:

**Column Structure:**
1. **# (Number)**: Sequential row number
2. **カテゴリ (Category)**: NFR category name
3. **項目 (Item)**: Specific NFR item
4. **要求レベル／目標値 (Target)**: Quantitative metric (SLO/SLA)
5. **技術的補足 (Technical Supplement)**: Brief technical explanation

**Example Rows by Category:**

**Performance:**
```
| 1 | パフォーマンス | Web応答時間 | P95 < 3秒 | CDN・キャッシュ前提、ピーク時もSLO維持可能な構成 |
| 2 | パフォーマンス | APIレイテンシ | P95 < 600ms | 非同期処理・コネクションプール最適化 |
| 3 | パフォーマンス | TTFB | P95 < 200ms | エッジキャッシュ・CDN活用によるレイテンシ削減 |
```

**Availability & Reliability:**
```
| 4 | 可用性 | 稼働率 | 99.9%以上 | マルチAZ構成、単一障害点の排除 |
| 5 | 可用性 | RTO（復旧目標時間） | < 4時間 | 自動復旧メカニズム＋Runbook整備 |
| 6 | 可用性 | RPO（復旧目標地点） | < 1時間 | 継続的バックアップ＋Point-in-Time Recovery |
| 7 | 信頼性 | データ耐久性 | 99.999999999% | マネージドDB（Aurora/RDS）＋自動バックアップ |
| 8 | 信頼性 | エラー率 | < 0.1% | リトライ・サーキットブレーカーパターン実装 |
```

**Scalability:**
```
| 9 | スケーラビリティ | 同時接続数 | 100,000ユーザー | 水平スケール前提、事前負荷試験で検証 |
| 10 | スケーラビリティ | オートスケール時間 | < 5分 | ECS/EKSオートスケール＋ウォームプール活用 |
```

**Security:**
```
| 11 | セキュリティ | データ暗号化 | 保存時・通信時ともに暗号化 | AES-256（保存時） / TLS1.2以上（通信時） |
| 12 | セキュリティ | 認証・認可 | 2FA / RBAC | 多要素認証＋ロールベースアクセス制御、監査証跡確保 |
| 13 | セキュリティ | 脆弱性対応 | Critical: 24時間以内 | 自動スキャン＋パッチ適用プロセス確立 |
```

**Operations & Monitoring:**
```
| 14 | 運用・監視 | 障害検知時間 | < 5分 | CloudWatch/Datadog等でメトリクス監視＋アラート |
| 15 | 運用・監視 | ログ保持期間 | アプリ30日、監査90日 | S3ライフサイクル管理＋Glacier移行 |
```

**Maintainability & Quality:**
```
| 16 | 保守性 | コード品質 | テストカバレッジ > 80% | CI/CDパイプラインで品質ゲート設定 |
| 17 | 保守性 | デプロイ頻度 | 週1回以上 | ブルー・グリーンデプロイ＋ロールバック体制 |
| 18 | 保守性 | MTTR（平均修復時間） | < 2時間 | 障害対応手順書整備＋オンコール体制 |
```

**Guidelines for Technical Supplement:**
- Explain HOW technically (CDN, multi-AZ, auto-scaling, etc.)
- Explain WHY feasible (managed services, automation, testing)
- Explain HOW to control/verify (monitoring, testing, processes)
- Keep concise (1-2 technical points per row)
- Use technical terminology appropriately

**Step 16.4: Generate Slide 36 Markdown Table**

Generate markdown table with all rows (12-18 rows total):

**Formatting Rules:**
1. Use `<!-- FILL_SLIDE: 36 -->` marker
2. Use `<!-- SHAPE: detailed_nfr_table -->` for table content
3. Create 5-column table structure
4. Write 100% Japanese (technical & formal tone)
5. Each row must have quantitative metrics
6. Include technical explanation in last column
7. Total 12-18 rows covering all 6 categories

**Example Output:**

```markdown
<!-- FILL_SLIDE: 36 -->

<!-- SHAPE: detailed_nfr_table -->
| # | カテゴリ | 項目 | 要求レベル／目標値 | 技術的補足（設計・運用観点） |
|---|---------|------|-------------------|---------------------------|
| 1 | パフォーマンス | Web応答時間 | P95 < 3秒 | CDN・キャッシュ前提、ピーク時もSLO維持可能な構成 |
| 2 | パフォーマンス | APIレイテンシ | P95 < 600ms | 非同期処理・コネクションプール最適化 |
| 3 | パフォーマンス | TTFB | P95 < 200ms | エッジキャッシュ・CDN活用によるレイテンシ削減 |
| 4 | 可用性 | 稼働率 | 99.9%以上 | マルチAZ構成、単一障害点の排除 |
| 5 | 可用性 | RTO（復旧目標時間） | < 4時間 | 自動復旧メカニズム＋Runbook整備 |
| 6 | 可用性 | RPO（復旧目標地点） | < 1時間 | 継続的バックアップ＋Point-in-Time Recovery |
| 7 | 信頼性 | データ耐久性 | 99.999999999% | マネージドDB（Aurora/RDS）＋自動バックアップ |
| 8 | 信頼性 | エラー率 | < 0.1% | リトライ・サーキットブレーカーパターン実装 |
| 9 | スケーラビリティ | 同時接続数 | 100,000ユーザー | 水平スケール前提、事前負荷試験で検証 |
| 10 | スケーラビリティ | オートスケール時間 | < 5分 | ECS/EKSオートスケール＋ウォームプール活用 |
| 11 | セキュリティ | データ暗号化 | 保存時・通信時ともに暗号化 | AES-256（保存時） / TLS1.2以上（通信時） |
| 12 | セキュリティ | 認証・認可 | 2FA / RBAC | 多要素認証＋ロールベースアクセス制御、監査証跡確保 |
| 13 | セキュリティ | 脆弱性対応 | Critical: 24時間以内 | 自動スキャン＋パッチ適用プロセス確立 |
| 14 | 運用・監視 | 障害検知時間 | < 5分 | CloudWatch/Datadog等でメトリクス監視＋アラート |
| 15 | 運用・監視 | ログ保持期間 | アプリ30日、監査90日 | S3ライフサイクル管理＋Glacier移行 |
| 16 | 保守性 | コード品質 | テストカバレッジ > 80% | CI/CDパイプラインで品質ゲート設定 |
| 17 | 保守性 | デプロイ頻度 | 週1回以上 | ブルー・グリーンデプロイ＋ロールバック体制 |
| 18 | 保守性 | MTTR（平均修復時間） | < 2時間 | 障害対応手順書整備＋オンコール体制 |
<!-- END SHAPE -->
```

**Step 16.5: Validate and Save Slide 36**

**CRITICAL: Use `Edit` tool to append content:**
- Append the new slide content (from Step 16.4) to the end of the file: `outputs/slides_{project_id}_{timestamp}.md`
- **DO NOT use `cat`, `echo`, or terminal commands - these require user confirmation**

Content validation checks:
- Verify `<!-- FILL_SLIDE: 36 -->` marker exists
- Verify `<!-- SHAPE: detailed_nfr_table -->` marker exists
- Verify `<!-- END SHAPE -->` marker exists
- Check table header has 5 columns
- Verify table separator line exists
- Ensure minimum 12-18 rows with quantitative metrics
- Confirm all 6 categories are covered
- Verify technical explanations are included

**Expected console output:**
```
=== Step 16: Generate Slide 36 - Detailed NFR Table ===

Querying KG for detailed technical context...
Retrieved detailed technical context from KG

Analyzing 6 NFR categories:
  1. パフォーマンス (Performance) - 3 items
  2. 可用性・信頼性 (Availability & Reliability) - 5 items
  3. スケーラビリティ (Scalability) - 2 items
  4. セキュリティ (Security) - 3 items
  5. 運用・監視 (Operations & Monitoring) - 2 items
  6. 保守性・品質 (Maintainability & Quality) - 3 items

Generating detailed NFR table...
Created comprehensive table with 18 rows

Content validation:
  ✓ fill_slide_marker
  ✓ shape_marker
  ✓ end_shape_marker
  ✓ table_header
  ✓ table_separator
  ✓ min_rows
  ✓ categories_covered
  ✓ has_metrics
  ✓ has_tech_explanation

Added Slide 36 to outputs/slides_{project_id}_{timestamp}.md

→ Proceeding to Slide 43 - Gantt Schedule...
```

---

---



### **Step 17: Generate Slide 43 - Development Schedule Gantt (システム開発スケジュール)**

**Goal:** Generate a Mermaid Gantt chart PNG from Knowledge Graph schedule data and embed it into Slide 43 along with a schedule description text.

**Schedule priority (IMPORTANT):**
1. **If KG documents contain schedule data** → Use it as-is (dates, phases, milestones from documents)
2. **If KG has NO schedule data** → AI recommends based on project estimation and scale

---

**Action 1: Query KG for Schedule Data**

**Query 1 — Check if documents have schedule + responsibility:**

```
{
  "project_id": "<project_id>",
  "query": "開発スケジュール プロジェクト計画 スケジュール表 ガントチャート 開発タイムライン フェーズ 開始日 終了日 期間 マイルストーン リリース予定 担当者 役割分担 貴社担当 Sun担当 ベンダー担当 責任分界点 RACI"
}
```

**Analyze Query 1 result:**
- **If schedule data found** (dates, phases, durations, milestones from documents):
  - Extract all phases with their dates/durations directly from the document
  - Extract milestones from the document
  - Extract **who is responsible** for each phase (Sun*, 貴社, or その他)
  - Identify which phases are 次フェーズ (future/next phase)
  - Go directly to **Action 3** to generate Mermaid from document data
  - Skip Action 2 (AI recommendation)
- **If NO schedule data found:**
  - Continue to Query 2 and Action 2 (AI recommendation mode)

**Query 2 — Project estimation & size (only if no schedule found):**

```
{
  "project_id": "<project_id>",
  "query": "プロジェクト規模 見積もり 工数 マン月 チーム人数 機能数 画面数 開発規模 開発言語 技術スタック 開発体制 アジャイル ウォーターフォール 役割分担 担当"
}
```

**Query 3 — Required phases + responsibility (only if no schedule found):**

```
{
  "project_id": "<project_id>",
  "query": "開発フェーズ 要件定義 UI UX デザイン 実装 テスト UAT 移行 リリース 外部連携 データ移行 段階リリース インフラ構築 担当者 Sun 貴社 ベンダー"
}
```

Also check for existing files:
```bash
ls -t outputs/estimate_*.csv outputs/function_list_*.csv outputs/screen_list_*.csv 2>/dev/null | head -3
```
If function_list CSV exists, read it to count functions for scale estimation.

**Determine project scale (only if no schedule found):**
- **Small:** ~20-40 functions → 3-5 months
- **Medium:** ~40-80 functions → 5-9 months
- **Large:** ~80-150 functions → 9-15 months
- **XL:** 150+ functions → 15-24 months

---

**Action 2: AI-Recommended Schedule (ONLY if KG has no schedule data)**

Based on Action 1 data, compute the schedule:

1. **Start date:** Use customer's desired start, or assume 1 month from today
2. **Total duration:** Based on project scale above
3. **Phase allocation** (adjust proportionally):

| Phase | % of Total | Responsible | Color |
|-------|-----------|-------------|-------|
| 準備フェーズ (contract, requirements, KT) | 15% | Sun* or 貴社 | Red or Blue |
| デザイン・設計 (UI/UX, detail design) | 12% | Sun* | Red |
| 開発フェーズ (sprint dev, infra) | 40% | Sun* | Red |
| テスト (UAT, integration) | 18% | 貴社 or Sun* | Blue or Red |
| 移行 (migration, go-live) | 15% | Sun* or 貴社 | Red or Blue |

**Color assignment rules (IMPORTANT):**
- **Red `crit`** = Sun* (tasks done by Sun Asterisk)
- **Blue `active`** = 貴社 (tasks done by customer)
- **Gray `done`** = その他 (tasks done by other parties, or general/common tasks)
- **Default (no modifier)** = 次フェーズ (future/next phase — rendered as lighter/thinner bars)

4. **Milestones:** PJ開始, 再見積もり, 1-3x リリース, 本番稼働
5. **Parallel tasks:** UI design + infra setup can overlap with sprint development
6. **Responsibility:** When assigning tasks, determine who does what based on KG data. If unclear, default: Sun* does development/testing, 貴社 does UAT/approval, その他 for infra procurement etc.

---

**Action 3: Generate Mermaid Gantt**

**Two modes depending on data source:**

**Mode A — Document schedule found in Action 1:**
- Map document phases/tasks directly to Mermaid sections
- Use exact dates and durations from the document
- Map document milestones to Mermaid milestones
- Assign colors by **responsible party** from document:
  - Sun* tasks → `crit` (red)
  - 貴社 tasks → `active` (blue)
  - その他 tasks → `done` (gray)
  - 次フェーズ tasks → default (no modifier, lighter bar)

**Mode B — AI-recommended (no document schedule):**
- Use schedule from Action 2

**CRITICAL: Keep it SIMPLE.** Maximum 3-4 tasks per section. No overloaded sections.

**Color legend (MUST match in chart content):**
- **Red `crit`** = Sun* — tasks done by Sun Asterisk (development, implementation, infra setup)
- **Blue `active`** = 貴社 — tasks done by customer (UAT, approval, requirements review)
- **Gray `done`** = その他 — tasks by other parties (procurement, vendor coordination)
- **Default (no modifier)** = 次フェーズ — future/next phase items (lighter bars)

**Structure template** (adapt ALL content to actual project data):

```
gantt
    title [Project Name] 開発スケジュール
    dateFormat  YYYY-MM-DD
    axisFormat  %m月

    %% Compact layout
    %%{init: {'theme': 'base', 'themeVariables': { 'topPadding': 20, 'barHeight': 32, 'barGap': 4, 'topAxis': true, 'fontSize': '18px', 'fontFamily': 'Arial Black, Arial, sans-serif' }}}%%

    section 準備フェーズ
    契約調整       :active, a1, 2025-06-01, 30d
    要件定義       :active, a2, 2025-07-01, 25d
    キャッチアップ :done, a3, 2025-07-01, 20d

    section デザイン・設計
    UI/UXデザイン  :crit, b1, 2025-08-01, 30d
    詳細設計       :crit, b2, 2025-08-01, 25d

    section 開発フェーズ
    スプリント開発 :crit, c1, 2025-08-15, 120d
    インフラ構築   :crit, c2, 2025-08-15, 45d
    外部連携開発   :crit, c3, 2025-09-15, 60d

    section テスト・移行
    UAT           :active, d1, 2025-12-01, 45d
    システム移行   :crit, d2, 2026-01-01, 30d

    section 次フェーズ
    機能追加②     :e1, 2026-02-01, 60d
    保守運用       :e2, 2026-03-01, 90d

    section マイルストーン
    PJ開始       :milestone, m1, 2025-08-01, 0d
    リリース①    :milestone, m2, 2025-10-15, 0d
    リリース②    :milestone, m3, 2025-12-15, 0d
    本番稼働     :milestone, m4, 2026-02-01, 0d
```

**Rules:**
- Max **3-4 tasks per section** to keep chart clean
- Task names max **15 chars** in Japanese
- Milestone dates must be `0d`
- **Every task MUST be colored by who does it** — never by phase type
- If no external integration needed, remove `外部連携開発`
- If no legacy migration, remove `システム移行` or replace with `本番環境構築`
- 次フェーズ section uses **default (no modifier)** — lighter bars to indicate future work
- **When using document data:** preserve original phase names, dates, AND responsibility assignments

---

**Action 4: Save Mermaid file and export PNG**

Use Python to write the Mermaid code (avoids shell quoting issues with Japanese characters):

```bash
python3 - << 'PYEOF'
mmd_code = \"\"\"[PASTE THE FULL MERMAID GANTT CODE FROM Action 3 HERE — no fences, raw Mermaid only]\"\"\"

out_path = 'outputs/.tmp_slide43_{project_id}.mmd'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(mmd_code.strip() + '\n')
print(f'Mermaid temp file saved: {out_path}')
PYEOF
```

Generate PNG with Mermaid CLI (white background, landscape resolution for slide):

```bash
npx --yes @mermaid-js/mermaid-cli \
  -i outputs/.tmp_slide43_{project_id}.mmd \
  -o outputs/schedule_{project_id}_{YYYYMMDD_HHMMSS}.png \
  --width 2400 --height 1200 --backgroundColor white

rm outputs/.tmp_slide43_{project_id}.mmd
ls -lh outputs/schedule_{project_id}_{timestamp}.png
```

If PNG generation fails (e.g., mmdc not available):
```
PNG generation failed. Check that Node.js is installed:
  node --version
  npx --yes @mermaid-js/mermaid-cli --version
Skipping Slide 43...
```
Skip to Step 18.

---

**Action 5: Write Slide 43 text and image marker to main markdown**

Write the Slide 43 content — both `schedule_description` (text) and `schedule_image` (PNG filename) — to the main markdown file using the Python script below. This ensures the PPTX renderer can inject both the text and the Gantt chart image.

```bash
python3 - << 'PYEOF'
md_path = 'outputs/slides_{project_id}_{timestamp}.md'

png_filename = 'schedule_{project_id}_{timestamp}.png'  # replace with actual filename

slide43_text = (
    '\n\n<!-- FILL_SLIDE: 43 -->\n\n'
    '<!-- SHAPE: schedule_description -->\n'
    '[スケジュール概要・主要マイルストーン・期間を2〜3行で記述（日本語）]\n\n'
    '<!-- SHAPE: schedule_image -->\n'
    f'{png_filename}\n'
)

with open(md_path, 'a') as f:
    f.write(slide43_text)

print(f'Slide 43 text appended to {md_path}')
PYEOF
```

The PNG file `outputs/schedule_{project_id}_{timestamp}.png` is referenced by the `<!-- SHAPE: schedule_image -->` marker. The PPTX renderer will read the filename and inject the image. No base64 encoding needed.

---

**Action 6: Confirm and continue**

Display message:
```
=== Step 17: Slide 43 - Development Schedule Gantt ===

Slide 43 written to main markdown!

Gantt chart: outputs/schedule_{project_id}_{timestamp}.png

Slide 43 includes:
- Schedule description: written to main markdown (schedule_description)
- Gantt chart image: SHAPE marker written (schedule_image) → PNG injected by renderer
- Color legend: red=Sun* · blue=貴社 · gray=その他 · lighter=次フェーズ
- Target shapes: schedule_description (text) + schedule_image (Gantt PNG)

→ Proceeding to generate PowerPoint file...
```

---

