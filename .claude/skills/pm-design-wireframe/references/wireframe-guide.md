# Wireframe Guide (Screen Breakdown, ASCII Notation, Mobile First)

The reference used in Steps 2 and 4 of the `pm-design-wireframe` skill: how to break work down into screens, the ASCII wireframe notation, mobile-first principles, and the axes for differentiating the 2–3 options.

---

## 1. How to Break Work Down Into Screens

One function or story often decomposes into several screens (plus modals and states). Enumerate them along these axes:

- **Split by business flow step**: each step of the main flow in story §6 can become its own screen (e.g. login → dashboard → each function).
- **Split by role or state**: if the same function is presented differently by role or state, make it a separate screen or a separate state (e.g. the dashboard before account verification completes ↔ after).
- **Split by CRUD or purpose**: list, detail, create/edit and confirm (modal) are treated as separate screens by default (e.g. item list → item detail → submission confirmation).
- **Separate sub-screens and modals**: decide whether confirmation dialogs, language switching, errors, etc. are drawn as a state of the main screen or split out as a modal.

**Naming slugs**: romaji kebab-case. Name them by meaning so they do not collide across functions.
Derive every slug from **this project's** `function-list.md` — the generic shapes below are only illustrations of the naming style, never a starting set to copy: `login` / `dashboard` / `mypage-profile` / `{entity}-list` / `{entity}-detail` / `{entity}-edit` / `{action}-confirm` / `settings` / `notifications`.

Present the breakdown to the user as "screen name (in Japanese) | slug | related F-ID/Story" and **have them choose one screen to wireframe**.

---

## 2. Wireframe Notation (ASCII Component Catalog)

Low fidelity is enough — it only has to convey layout, information and navigation. No decoration needed. Combine the catalog below and draw in a single mobile column (use a width of roughly 32–36 characters for the rules). Write it **inside a code block**.

### Screen frame / app bar (header)
```
┌──────────────────────────────┐
│ ☰   画面タイトル        🌐 🔔 │   ← ☰: menu  🌐: language  🔔: notifications
├──────────────────────────────┤
│ (コンテンツ領域)              │
│                              │
└──────────────────────────────┘
```

### Bottom navigation (for screens that need browsing)
```
├──────────────────────────────┤
│  🏠      📋      🔔      👤   │   ← home / list / notifications / my page
│ ホーム   一覧   通知  マイページ │
└──────────────────────────────┘
```

### Headings, text, dividers
```
■ セクション見出し
本文テキスト（説明）……
────────────────  ← divider
```

### Input forms
```
氏名（必須）
[____________________]
言語
[ 日本語            ▾ ]   ← dropdown
[✓] 利用規約に同意する      ← checkbox
( ) 現金  ( ) 口座          ← radio
```

### Buttons / CTAs
```
[      ログイン        ]   ← primary CTA (filled, full width)
[      キャンセル       ]   ← secondary (outlined)
 〔 詳細を見る 〕           ← small inline button
```

### Lists / cards
```
┌──────────────────────────────┐
│ アイテムのタイトル            │
│ 補足情報 ・ ステータス        │
│                  〔詳細〕     │
└──────────────────────────────┘
・行アイテム ……………………… ›   ← tap for detail (› indicates navigation)
```

### Tabs / steps
```
[ 基本情報 ]  詳細   履歴          ← tabs ([ ] marks the selected one)
① 入力 ─ ②確認 ─ ③完了              ← stepper (the circled number is the current position)
```

### Modals / dialogs
```
   ╔════════════════════════╗
   ║ 本当に削除しますか？    ║
   ║ この操作は取り消せません ║
   ║   [削除]   [やめる]     ║
   ╚════════════════════════╝
```

### Notifications / state displays
```
⚠ 本人確認が未完了です  〔手続きする〕  ← indicator / banner
✅ 保存しました                       ← toast
(空状態) 表示できるデータがありません
(読込中) ⏳ 読み込み中…
(エラー) ⚠ 通信に失敗しました 〔再試行〕
```

### Images / avatars
```
(◯ avatar)  表示名          ← an avatar image URL rendered directly
[  画像  ]                   ← image placeholder
```

> Do not be over-constrained by this notation. Getting the idea across matters most. Arrows `→` `›`, circled numbers and emoji icons may be used as aids.

---

## 3. Mobile-First Principles

- **The baseline is a narrow screen (equivalent to ~375px), single column.** Order information top-down by importance. As a rule, avoid left/right splits.
- **The primary CTA goes at the bottom of the screen (the thumb zone).** Narrow the main action of a screen to one.
- **Assume tap targets are large enough** (do not pack adjacent elements too tightly).
- **Draw the states**: alongside the happy path, include whichever of empty, loading, error and no-permission changes a design decision.
- **Labels stretch across languages**: when the project is multilingual, assume the character count varies across whichever languages `non-function-list.md` lists. Use layouts that tolerate wrapping and truncation, and avoid cramming into fixed widths.
- **Distinguish display-only from editable visually**: draw reference data mastered elsewhere as "label: value" and data entered on this screen as an input field.
- **Desktop only needs a one-line mention as a responsive extension** (the main target is mobile).

---

## 4. Axes for Differentiating the 2–3 Options

Each option should differ in its **layout/flow approach**, not in color or spacing. Pick 2–3 of the axes below and distribute them across the options:

- **Navigation structure**: bottom nav ↔ hamburger menu ↔ no navigation (single-purpose focus).
- **Number of steps**: everything on a single page ↔ split into steps (a wizard).
- **Information density**: lists (dense, space-efficient) ↔ cards (sparse, more legible).
- **Input style**: one bulk form ↔ conversational, one question at a time ↔ defaults plus collapsed details.
- **CTA placement / emphasis**: fixed footer CTA ↔ inline CTA ↔ floating button.
- **How states are shown**: an always-visible indicator ↔ interrupting with a modal ↔ a dedicated section.

**How to write the options up**:
- Give each option **a one-line approach** (e.g. "Option A: shortest path, everything on one page", "Option B: stepped, to reduce hesitation").
- Line up the "differentiation points" and "pros and cons" in the README's comparison table to help the choice.
- On the premise that every option satisfies the same acceptance criteria (story §9), let them compete on **how they satisfy them**.
