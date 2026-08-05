# Output Templates (README / option / screen-index)

The templates for the files the `pm-design-wireframe` skill writes into `plans/project-management/screens/` in Step 5. Copy them and fill in the `{ }` placeholders. The body is written in Japanese. When you make a substantive change, add one row to each file's "改訂履歴" (revision history) with the date (`currentDate`) and the updater (`pm-design-wireframe skill` or the persona name in use).

---

## A. `plans/project-management/screens/{slug}/README.md` (the screen index)

```markdown
# 画面ワイヤーフレーム：{画面名}（{slug}）

> 本ファイルは `pm-design-wireframe` skill による**低忠実度ワイヤーフレームの検討用**（探索ワークスペース `plans/project-management/`）。
> 正式な画面設計は後工程で `project/04_screen-design/` に反映される（本ファイルはそのインプット）。
> 入力：[`../../../project/02_requirements/function-list.md`]（{F-ID}）、[`../../../project/01_management/stories/{story-file}`]（{Story ID}、あれば）。

## 1. 画面情報

| 項目 | 内容 |
| --- | --- |
| 画面名 | {画面名} |
| slug | {slug} |
| 関連機能ID | {F-00X（機能名）} |
| 関連ストーリー | {E-0X-SYY（あれば） / なし} |
| 対象ロール | {ROLE-00X …} |
| 優先度 | {必須 / 推奨 / 任意} |
| ステータス | 案作成済（未選定） |
| 作成日 | {YYYY-MM-DD} |

## 2. 目的・利用文脈

- **目的**：{この画面の主目的を1〜2文}
- **利用文脈**：{誰が・いつ・どこから来て、成功後どこへ行くか（業務フロー上の位置）}
- **補足（多言語・端末等）**：{3言語対応の有無・言語切替UIの位置、モバイル主体 等}

## 3. 案一覧

| 案 | 方針 | 差別化ポイント | ファイル |
| --- | --- | --- | --- |
| A | {一言の方針} | {導線/ステップ数/情報密度 等} | [option-A.md](./option-A.md) |
| B | {一言の方針} | {…} | [option-B.md](./option-B.md) |
| C | {一言の方針}（任意） | {…} | [option-C.md](./option-C.md) |

## 4. 比較・トレードオフ

| 観点 | 案A | 案B | 案C |
| --- | --- | --- | --- |
| 操作の速さ／導線 | {…} | {…} | {…} |
| 情報の見やすさ | {…} | {…} | {…} |
| 実装コスト（目安） | {…} | {…} | {…} |
| 迷いにくさ／学習コスト | {…} | {…} | {…} |

## 5. 決定

| 項目 | 内容 |
| --- | --- |
| 選定案 | 未定 |
| 理由 | ― |
| 決定日 | ― |

<!-- ユーザーが選定したら「選定案：Option B」「理由：…」「決定日：YYYY-MM-DD」に更新する -->

## 6. 前提・未確定事項

| # | 区分（[ASSUMPTION]/要確認/依存） | 内容 | 確認先・確認予定 |
| --- | --- | --- | --- |
| 1 | {[ASSUMPTION]} | {仮置きした内容} | {確認先} |

## 7. 改訂履歴

| 日付 | 更新者 | 内容 |
| --- | --- | --- |
| {YYYY-MM-DD} | pm-design-wireframe skill | ファイル新規作成。{画面名}の 2〜3 案を作成 |
```

---

## B. `plans/project-management/screens/{slug}/option-X.md` (the wireframe for each option)

```markdown
# {画面名} — Option {X}：{一言の方針}

## 1. 方針

- {この案の設計方針を1〜2文。どの差別化軸を採ったか（例：ボトムナビ回遊型／単一ページ集約 等）}

## 2. ワイヤーフレーム（モバイルファースト）

### 正常時
（`references/wireframe-guide.md` の ASCII 記法で描く。ラベルは日本語）

（コードブロックにワイヤーフレームを記述）

### 空／エラー等の主要状態（必要な場合）
（設計判断が変わる状態のみ併記。例：空状態、認証失敗、権限なし）

（コードブロック）

## 3. 画面遷移・主要導線

- 入口：{どこから来るか}
- 主要アクション：{主 CTA} → {遷移先（成功時／失敗時）}
- 副次導線：{他画面への移動・言語切替・戻る 等}

（必要なら簡易フロー：`{前画面} → [{この画面}] → {次画面}`）

## 4. 表示データ（ストーリー §7 データ要件との対応）

| 情報要素 | 種別（表示専用/入力） | 出所（Admin参照/本サイト） | 備考 |
| --- | --- | --- | --- |
| {項目} | {表示専用/入力} | {Admin/本サイト} | {制約・マスキング 等} |

## 5. 受入条件との対応（ストーリー §9）

- {AC-1}：{この案でどう満たすか}
- {AC-2}：{…}

## 6. メリット / デメリット

- **メリット**：{…}
- **デメリット**：{…}
```

---

## C. `plans/project-management/screens/screen-index.md` (the catalog of all screens)

If it does not exist, create it with `Write` using the skeleton below, and thereafter update the relevant row with `Edit`.

```markdown
# 画面ワイヤーフレーム インデックス

> `pm-design-wireframe` skill が作成した各画面のワイヤーフレーム（`plans/project-management/screens/{slug}/`）の一覧。
> これは探索ワークスペース `plans/project-management/` の検討成果であり、正式な画面設計は後工程で `project/04_screen-design/` に反映される。
> 凡例（ステータス）：⬜ 未着手 / 🔄 案作成中 / 🅰 案作成済（未選定） / ✅ 選定済

## 1. 画面一覧

| 画面名 | slug | 関連 F-ID / Story | 案数 | 選定案 | ステータス | リンク |
| --- | --- | --- | --- | --- | --- | --- |
| {画面名} | {slug} | {F-00X / E-0X-SYY} | {2 or 3} | {未定 / Option B} | {🅰 / ✅} | [README](./{slug}/README.md) |

## 2. 改訂履歴

| 日付 | 更新者 | 内容 |
| --- | --- | --- |
| {YYYY-MM-DD} | pm-design-wireframe skill | {画面名}（{slug}）を追加 |
```
