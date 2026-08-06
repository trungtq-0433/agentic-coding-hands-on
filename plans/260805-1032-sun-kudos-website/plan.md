---
title: "Sun* Kudos (SAA 2025) — Website MVP"
description: "Dựng website ghi nhận Kudos nội bộ Sun* trên Next.js 16 + Supabase local, 18 màn MoMorph, hai track UI/backend chạy song song."
status: pending
priority: P1
effort: 63h
branch: main
work_type: feature
spec_waived: "SDD mode disabled (takumi.sddMode: off)"
tags: [nextjs16, supabase, realtime, momorph, i18n, rls]
created: 2026-08-05
---

# Sun* Kudos (SAA 2025) — Blueprint

Nguồn chân lý: [`clarifications.md`](./clarifications.md) · Yêu cầu: [`reports/…momorph-requirements-synthesis.md`](./reports/researcher-260805-1032-momorph-requirements-synthesis.md) · Kỹ thuật: [`reports/…nextjs16-supabase-local.md`](./reports/researcher-260805-1032-nextjs16-supabase-local.md) · Inventory 18 màn: [`../reports/momorph-260805-1011-website-spec-done-screens.md`](../reports/momorph-260805-1011-website-spec-done-screens.md).

## Hai track song song

| | Track A — UI theo màn | Track B — Backend/logic |
|---|---|---|
| Phase | 06 → 15 (06 trước, 07–15 song song) | 01 → 05 tuần tự |
| Cross-track | **CẤM** `blocks`/`blockedBy` giữa A và B | như bên trái |
| Dữ liệu | mock lấy từ chính Figma | Postgres local thật |
| Gặp nhau | tại phase-16 (integration) | tại phase-16 |

Track A không import file nào của Track B trước phase-16; mọi hành vi động đi qua **props/callback** khai trong "Integration contract" của từng phase file.

## Danh sách phase

| # | Phase | Track | Status | Effort | Phụ thuộc |
|---|---|---|---|---|---|
| — | **PRE-REQ-01 — Google OAuth client** (việc của người, không phải agent) | — | **chưa giao** | — | ngày 0 |
| 01 | [Nền tảng Supabase + Next](./phase-01-nen-tang-supabase-va-next.md) | B | completed | 3h | — |
| 02 | [Schema, migrations, RLS](./phase-02-schema-migrations-rls.md) | B | completed | 6h | 01 |
| 03 | [Auth Google OAuth](./phase-03-auth-google-oauth.md) | B | completed | 3h | 02 + **PRE-REQ-01** |
| 04 | [Data access + business logic](./phase-04-data-access-va-business-logic.md) | B | completed | 6h | 03 |
| 05 | [Realtime — Broadcast](./phase-05-realtime.md) | B | completed | 3h | 04 |
| 06 | [UI shared components (9 màn)](./phase-06-ui-shared-components.md) | A | completed | 4h | — |
| 07 | [UI Login](./phase-07-ui-login.md) | A | completed | 1h | 06 |
| 08 | [UI Homepage SAA](./phase-08-ui-homepage-saa.md) | A | completed | 3h | 06 |
| 09 | [UI Live board](./phase-09-ui-live-board.md) | A | pending | 4h | 06 |
| 10 | [UI Viết Kudo](./phase-10-ui-viet-kudo.md) | A | pending | 3h | 06 |
| 11 | [UI Profile bản thân](./phase-11-ui-profile-ban-than.md) | A | pending | 3h | 06, 09 |
| 12 | [UI Hệ thống giải](./phase-12-ui-he-thong-giai.md) | A | pending | 2h | 06 |
| 13 | [UI Thể lệ](./phase-13-ui-the-le.md) | A | pending | 1h | 06 |
| 14 | [UI Countdown Prelaunch](./phase-14-ui-countdown-prelaunch.md) | A | pending | 1h | 06 |
| 15 | [UI Open Secret Box](./phase-15-ui-open-secret-box.md) | A | pending | 1h | 06 |
| 16 | [Integration](./phase-16-integration.md) | — | pending | 5h | 05 + 07..15 |
| 17 | [Tests](./phase-17-tests.md) | — | pending | 14h | 16 |

**Tổng 63h** = Track B 21h (3+6+3+6+3) · Track A 23h (4+1+3+4+3+3+2+1+1+1) · phase-16 5h · phase-17 14h.

**Tiến độ:** 8/17 phase hoàn thành · 29h/63h effort done.

## Pre-requisites (ngoài phase, làm song song từ ngày 0)

**PRE-REQ-01 — Google OAuth client.** Tạo trên Cloud Console, redirect URI `http://localhost:54321/auth/v1/callback` (cổng **Supabase**). Client ID + secret đặt vào **`.env`** dưới hai biến `SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID` và `SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET` — xem `.env.example`. (KHÔNG phải `.env.local`; xem ghi chú dưới.) Người làm: có quyền admin Google Workspace Sun\* — **ĐÃ GIAO và HOÀN THÀNH**. Chặn phase-03 → 04 → 05 → 16 khi chưa xong; Track A không ảnh hưởng. Agent không có và không nên có quyền này. Với credential đã có, phase-03 + 04/05/16 không còn chặn.

> **Không bao giờ dán giá trị credential vào file trong `plans/` hay `docs/`.** Bản kế hoạch này
> từng chứa client ID + secret thật ở đúng dòng trên; GitHub secret scanning chặn push và secret
> đó phải xoay lại. Nơi duy nhất của giá trị thật là **`.env`** — file mà CLI Supabase đọc để
> thay thế `env()` trong `supabase/config.toml`, dưới tên `SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID`
> và `_SECRET`. **KHÔNG phải `.env.local`** (file đó của Next.js; CLI Supabase không đọc nó — đã
> kiểm chứng bằng thực nghiệm). Cả hai đều gitignore; template ở `.env.example`.

## Bản đồ route + ranh giới sở hữu file (chốt ở đây, mọi phase theo)

`/` Homepage · `/login` · `/kudos` Live board · `/awards` · `/profile[?id=]` · `/prelaunch` gate · `/admin` placeholder · `/auth/callback` Route Handler. Viết Kudo / Thể lệ / Open Secret Box là **modal**, không có route riêng. **Không dùng route group** — mỗi page một file, tách bạch quyền sở hữu giữa các phase.

- Track B: `supabase/**`, `lib/{supabase,auth,data,actions,validations,realtime,kudos}/**`, `proxy.ts`, `app/layout.tsx`, `next.config.ts`, `app/auth/**`
- Track A: `app/{page,login,kudos,awards,profile,prelaunch}/**`, `components/**`, `lib/content/**`, `locales/*/<namespace>.json`
- Phase 16 là phase duy nhất được sửa file của cả hai track.

## Rủi ro xuyên suốt

| Rủi ro | K/năng × T/động | Countermove |
|---|---|---|
| Dev viết `middleware.ts` theo trí nhớ Next 14 | Cao × Cao | phase-01 tạo `proxy.ts` trước tiên; phase-17 test chặn sự tồn tại của `middleware.ts` |
| `params`/`searchParams`/`cookies()` không `await` | Cao × TB | `tsc --noEmit` trong `validate` (phase-17) |
| Track A "đoán" hành vi backend rồi lệch contract | TB × Cao | Integration contract bắt buộc ở mọi phase Track A; phase-16 là nơi duy nhất nối dây |
| Rò danh tính người gửi ẩn danh | Thấp × **Rất cao** | Che ở tầng DB (`public_kudos_feed` + `revoke`), không che ở UI — phase-02 |
| Luật nghiệp vụ bị lách qua PostgREST | TB × **Rất cao** | `revoke` quyền ghi trực tiếp, mọi ghi qua RPC — phase-02/04 |
| PRE-REQ-01 trễ → dừng Track B ở phase-03 | Cao × Cao | Khởi động ngày 0; phase-04 chạy trước bằng phiên giả lập |

## Còn treo (không chặn MVP)

Hero tier · rule cấp Secret Box · notification bell · màn Admin thật · `department_id` NULL của user thật · `PAO - PAO` ở nguồn · 8 màn trắng TC · PRE-REQ-01 chưa giao. Xem `clarifications.md` mục "Còn treo".

## Red Team Review

> **Ghi chú độ dài:** phần thân plan (tới hết mục "Còn treo") giữ đúng dưới 80 dòng theo ràng buộc. Section Red Team Review bên dưới đẩy tổng file lên ~148 dòng — vượt có chủ ý và được cho phép, vì bảng disposition là hồ sơ kiểm toán phải đi cùng plan, không phải nội dung điều hướng.

### Session — 2026-08-05
**Findings:** 20 (18 accepted, 2 rejected) + 4 capped-applied + **3 phase-03 Critical phát hiện sau thực thi**
**Severity breakdown:** 11 Critical, 8 High, 1 Warning

| # | Finding | Severity | Disposition | Applied To |
|---|---|---|---|---|
| 1 | RLS cho INSERT thẳng vào `kudos` — policy `with check` không chặn được nội dung, client lách RPC qua PostgREST | Critical | Accept | phase-02 (KI#9, bảng RLS, bước 7, SC, risk) |
| 2 | RLS cho INSERT thẳng vào `hearts`; `is_special_day_bonus` client tự đặt được | Critical | Accept | phase-02 (revoke, trigger), phase-04 (KI#2, chữ ký RPC, SC) |
| 3 | `revoke select on kudos` giết Realtime Postgres Changes — **confirmed by 2 reviewers** | Critical | Accept | phase-02 (KI#10, trigger `0006b`), **phase-05 viết lại toàn bộ sang Broadcast**, phase-16, phase-17 |
| 4 | `next lint` đã bị xoá khỏi Next 16 (`version-16.md:1084`) | Critical | Accept | phase-17 (KI#3b, bước 11, SC), phase-16 (bước 14) |
| 5 | `NEXT_PUBLIC_*` inline lúc build — restart không đủ (`environment-variables.md:166`) | Critical | Accept | phase-01 (KI#5b, runbook, SC, risk), phase-14, `clarifications.md:19` |
| 6 | `department_id` không có đường gán → NULL với mọi user thật, filter rỗng im lặng | High | Accept | phase-04 (KI#9, bước 8b, SC), phase-16, clarifications "Còn treo" |
| 7 | Secret Box hết hộp giữa sự kiện, không có đường cấp thêm | Critical | Accept | phase-02 (RPC `admin_grant_secret_box`, Runbook), phase-16 (`docs/runbook-su-kien.md`) |
| 8 | `create_kudos` không verify `p_image_urls` thuộc sở hữu người gọi | High | **Reject — user quyết** | — (không sửa file) |
| 9 | Thiếu `SET search_path` ở `is_admin()` và `handle_new_user()` | High | Accept | phase-02 (bước 3, SC), phase-03 (bước 3, SC, risk) |
| 10 | Race double-click ở `toggle_heart`; `heart-actions` không có nhánh lỗi | High | Accept | phase-04 (KI#3b, chữ ký RPC, bước 11, SC, risk), phase-09 (prop `pending`) |
| 11 | Realtime không catch-up sau reconnect | High | **Reject — user quyết** | — (ghi thành rủi ro chấp nhận có ý thức ở phase-05) |
| 12 | `handle_new_user()` không COALESCE metadata Google null → khoá đăng nhập vĩnh viễn | High | **Reject — user quyết** | — (không sửa file) |
| 13 | Thiếu `images.remotePatterns` → `next/image` throw với avatar Google thật | High | Accept | phase-01 (KI#6b, bước 3b, SC, risk), phase-03 (SC) |
| 14 | Effort phase-17 5h phi thực tế | High | Accept | phase-17 (14h + phân bổ theo tầng), `plan.md` (tổng 63h) |
| 15 | `kudos_mentions` ghi mà không ai đọc | High | Accept | phase-02 (KI#7, bỏ bảng), phase-04 (bỏ `p_mention_ids`), phase-10 (bỏ `mentionIds`) |
| **16** | **TRUNCATE privilege không revoke — phiên authenticated truncate sạch 4 bảng** | **Critical** | **Accept** | **phase-02 (bước 7, khối revoke toàn bộ, C1 vá: `revoke all` → `grant select`)** |
| **17** | **Counter `sent_kudos_count` rò ẩn danh — suy luận chính xác 100% số kudo ẩn → truy sender** | **Critical** | **Accept** | **phase-02 (bước 7, column-level grant loại `sent_kudos_count`, C2 vá: hệ quả `select('*')` lỗi)** |
| **18** | **Trigger 0007 làm `seed.sql` rollback khi `profiles`/`user_roles` xung đột khoá** | **Critical** | **Accept** | **phase-03 (bước 3, SC + vá: thêm `ON CONFLICT ... DO UPDATE` ở seed, khớp lại `full_name`, bồi `department_id`)** |
| **19** | **`redirect_uri` config để trống → GoTrue dùng `127.0.0.1`, Google Console đăng ký `localhost` → mismatch** | **Critical** | **Accept** | **phase-03 (PRE-REQ-01, SC, risk + vá: khai tường minh `http://localhost:54321/auth/v1/callback`)** |
| **20** | **Biến env `.env.local` chứa `GOOGLE_CLIENT_ID/SECRET` mà Next.js không dùng → mix-up với `.env`** | **Warning** | **Accept** | **phase-03 (bước 2 bổ sung, `.env.local.example` + `clarifications.md`)** |
| capped-1 | ModalShell dùng chung — 3 phase song song tự dựng modal chrome riêng | — | Accept (capped) | phase-06 (contract + SC), phase-10/13/15 |
| capped-2 | Google OAuth client là pre-requisite ngoài phase | — | Accept (capped) | phase-03 (khối PRE-REQ-01, risk), `plan.md` (bảng Pre-requisites) |
| capped-3 | Số đếm sai: phòng ban và test case | — | Accept (capped) | phase-02 (**50** phòng ban + `PAO - PAO`, script đếm), phase-17 (**292** TC + bảng 8 file rỗng) |
| capped-4 | Ownership `package.json` không khai ở phase-04 | — | Accept (capped) | phase-04 (bàn giao tường minh 01 → 04 → 17) |

**Hai số liệu trong brief bị sửa lại sau khi đếm bằng parser:**
- Phòng ban: brief nói "~50", bản kế hoạch cũ ghi 48 → **50** (`scripts/count-departments.mjs`, 0 trùng lặp).
- Test case: brief nói **284** → thực tế **292**. Đếm bằng `csv.DictReader` trên cả 18 file, 0 dòng thiếu `TC_ID`; đếm dòng thô cũng ra 292. Đã dùng 292. Phần *quan trọng hơn* của finding — **8/18 file rỗng 0 byte** — thì đúng và đã áp.

### Cross-Phase Claim Reconciliation Sweep

Chạy sau khi áp xong 16 thay đổi, quét cả những phase reviewer không đọc.

| Kiểm | Lệnh | Kết quả |
|---|---|---|
| `postgres_changes` còn sót | `grep -rn "postgres_changes" *.md` | Chỉ còn ở phase-05 (KI#1 giải thích vì sao bỏ) + SC `grep` + risk, và bảng Red Team này. **Không còn chỗ nào mô tả nó như thiết kế đang dùng.** ✅ |
| `kudos_mentions` còn sót | `grep -rn "kudos_mentions" *.md` | Chỉ còn ở chỗ nêu lý do bỏ (phase-02 KI#7, danh sách "không dựng", phase-04 KI#1b) + SC kiểm bảng không tồn tại. ✅ |
| `p_mention_ids` / `mentionIds` | `grep -rn "mention_ids\|mentionIds" *.md` | Chỉ còn trong câu phủ định ở phase-04 và phase-10. ✅ |
| `next lint` | `grep -rn "next lint" *.md` | Chỉ còn trong câu cấm dùng (phase-16 bước 14, phase-17 KI#3b + bước 11 + SC). ✅ |
| Tổng effort | cộng cột Effort | 21+23+5+14 = **63h**, khớp frontmatter. ✅ |
| `clarifications.md` mâu thuẫn | đọc lại toàn file | Dòng "sửa `.env` + restart" đã sửa kèm ghi chú lý do; 5 quyết định mới + 4 mục "Còn treo" mới đã thêm. ✅ |
| Migration đánh số trùng | đối chiếu ownership 4 phase | 02 giữ `0001–0006`+`0006b`, 03 giữ `0007`, 04 giữ `0008`/`0009`, 05 **không còn** `0010`. Không trùng. ✅ |
| Số bảng | phase-02 vs phase-17 | Cả hai đã đổi 13 → **12** sau khi bỏ `kudos_mentions`. ✅ |
| Số trigger | phase-02 vs phase-17 | phase-02 khai 5 (3 counter + 2 broadcast); phase-17 pgTAP ghi 5. ✅ |
| Số RPC | phase-02/04 vs phase-17 | 4 (3 nghiệp vụ + `admin_grant_secret_box`); phase-17 đã ghi 4. ✅ |
| Cross-track dependency | đọc header 10 phase Track A | Không phase Track A nào phụ thuộc phase-01…05. ✅ |
| Track A ≤ 30 dòng | `wc -l` | 10/10 đạt. ✅ |

### Session — 2026-08-05 (Phase-04/05/06 Execution Review)
**Findings:** 4 Critical + actions remediation path

| # | Finding | Severity | Phase | Action |
|---|---|---|---|---|
| **RR-1** | **Random weight phân phối lệch 10% → 0.43%, 20% → 2.96%** — `open_secret_box` đặt `random() * total` trong mệnh đề WHERE, Postgres gọi hàm ngẫu nhiên một lần cho **mỗi hàng** subquery 6 badge, không phải chung. 10.000 lần test: `revival` 10% kỳ vọng nhưng chỉ 0,43% thực tế. | Critical | 04 (Success Criteria) | Rút `v_pick := random() * total_weight` thành biến trước WHERE; sau vá lệch tối đa 0,74% ✓ |
| **RR-2** | **Kiểu dữ liệu RPC sai** — `create_kudos(p_hashtag_ids uuid[])` nhưng `hashtags.id` / `kudos.id` thực tế `bigint identity` (schema phase-02) → psql reject `invalid input syntax for type uuid` | Critical | 04 (RPC chữ ký) | Sửa `p_hashtag_ids bigint[]` · `p_kudos_id bigint` · returns `bigint` ✓ |
| **RR-3** | **Cursor keyset injection PostgREST** — `decodeCursor` chỉ kiểm `typeof createdAt === "string"` rồi ghép thẳng vào `.or("created_at.lt.<X>,…")`. Dấu phẩy là ký tự ngăn mệnh đề → cursor `createdAt="2000-01-01T00:00:00Z,id.gt.0"` phá ranh keyset. Tái hiện thật bằng curl: cursor hợp lệ trả 0, cursor độc trả 5. Lỗi ở 3 hàm đọc feed (board/received/sent) cùng gốc. | Critical | 04 (lib/kudos/cursor.ts) | Regex ISO-8601 strict tại `decodeCursor`, kiểm: 2 payload độc + 3 dạng rác từ chối, hợp lệ qua ✓ |
| **RR-4** | **`ModalShell` cướp focus** — effect focus-trap phụ thuộc `onClose` chưa bọc ref; caller truyền arrow inline → effect chạy lại mỗi cha re-render → focus nhảy về phần tử đầu, cướp con trỏ khỏi input đang gõ | Warning | 06 (ModalShell) | Dùng `onCloseRef` giống `lib/realtime/use-kudos-stream.ts` ✓ |

**Kiểm độc lập (orchestrator):**
- **12/12** security definer có `search_path=public, pg_temp` ✓
- **3 RPC:** anon reject, authenticated accept ✓; `toggle_heart` chỉ 1 param (no bonus flag) ✓
- **Race `toggle_heart`:** `for update skip locked` + `on conflict do nothing` ✓
- **Phân phối 10.000:** max deviation 0,74% ✓
- **Feed read:** 0 `.from('kudos')`, 7 `public_kudos_feed` + 2 `my_sent_kudos` ✓
- **Guest realtime:** ✓ · **Payload:** `{kudos_id, event}` only ✓
- **Lint/compile:** 0 errors ✓

### Session — 2026-08-06 (Phase-08 UI Homepage SAA)
**Findings:** 3 Warning từ reviewer (0 Critical) + **8 sai sót orchestrator tự bắt bằng visual diff**

| # | Finding | Severity | Nguồn | Xử lý |
|---|---|---|---|---|
| RR-7 | **Nền keyvisual biến mất hoàn toàn.** `overflow-x-hidden` khiến trình duyệt tính lại `overflow-y` thành `auto` → thẻ gốc thành vùng cuộn, Chromium sơn nền vùng cuộn ĐÈ lên con `z` âm. Ảnh vẫn load, `opacity:1`, đúng kích thước, không lỗi nào báo ra. | Critical | Visual diff | Bỏ `overflow-x-hidden`; kiểm bằng pixel: `(209,129,57)` vs thiết kế `(204,131,65)` ✓ |
| RR-8 | **`box-shadow` thẻ giải tính ra TRONG SUỐT.** `shadow-[0_4px_4px_0_rgba(0,0,0,.25),0_0_6px_0_#FAE287]` — Tailwind v4 bỏ qua giá trị nhiều lớp có dấu phẩy trong `rgba()`; `getComputedStyle` trả `rgba(0,0,0,0) 0px 0px 0px 0px`, không lỗi build | Critical | `getComputedStyle` | Chuyển sang `style={{ boxShadow }}` inline |
| RR-9 | **`fonts.ts` chỉ nạp Montserrat weight 700** nhưng Homepage cần 400 + 500. `next/font/google` chỉ sinh `@font-face` cho weight khai báo → chữ dày sai mà không báo lỗi | Critical | implementer (từ chối tự sửa vì ngoài ownership — đúng) | Thêm `["400","500","700"]` |
| RR-10 | **Header đè chữ hero ở 375px.** `h-20` cố định + `flex-wrap` → nav xuống dòng tràn ra ngoài hộp | High | Responsive check | `h-20`→`min-h-20`; header chỉ PHỦ từ `lg`, dưới `lg` nằm trong luồng |
| RR-11 | **Footer thiếu logo + 4 mục nav** (chỉ có dòng bản quyền) | High | Visual diff | Thêm prop `logo` cho `SiteFooter`, đảo thứ tự nhóm trái/phải |
| RR-12 | **Khoảng cách cột lưới giải sai**: dùng `gap:80px` Figma khai, nhưng `space-between` làm khoảng cách thật là **108px** | Warning | Đối chiếu toạ độ | `lg:gap-x-[108px] lg:gap-y-20`; 3×336+2×108 = 1224 ✓ |
| RR-13 | **Khối Root Further cao dư 467px**: áp `padding 120px 104px` mà Figma khai, trong khi con của frame đặt tuyệt đối và phớt lờ padding đó (frame còn khai height 1219 < nội dung 1256) | Warning | Đo `getBoundingClientRect` | Bỏ cả padding ngang lẫn dọc → tổng trang **4479 vs 4480** |
| RR-14 | **Khối Sun\* Kudos rộng dư 104px**: dùng 1224 (khung canh giữa) thay vì 1120 (tấm thẻ thật) | Warning | Đối chiếu toạ độ | `max-w-[1120px]` |
| RR-15 | **Rác lọt vào `public/`** — `kv-preview.png` (236KB, do chính orchestrator tạo lúc xem ảnh) + `.claude/agent-memory/` rỗng. `public/` được Next phục vụ TĨNH → mọi file trong đó truy cập công khai được (đã curl xác nhận 200) | Warning | reviewer | Xoá; dọn thêm `next.svg`/`vercel.svg` mồ côi sau khi thay trang mặc định |
| RR-16 | `home-page.tsx` 213 dòng, vượt ngưỡng 200 | Warning | reviewer + tester (cùng bắt) | Tách `home-header.tsx` + `home-footer.tsx` → còn 153 |
| RR-17 | `useMemo` với dep `[t]` không bao giờ trúng (`t` là closure mới mỗi render) — chú thích còn giải thích SAI lý do | Suggestion | orchestrator tự bắt, reviewer xác nhận | Gỡ `useMemo` |

**Kiểm độc lập (orchestrator):**
- **Toạ độ 4 khối khớp Figma**: x/w đúng tuyệt đối; tổng trang **4479 vs 4480 (lệch 1px)**, footer lệch 1px
- **Nền keyvisual khớp pixel** với ảnh thiết kế tại 9 điểm mẫu
- **Responsive 375/768/1280**: 0 tràn ngang, header không đè hero ở cả 3 khổ
- **Countdown chạy thật** (`20/05/54` với mốc tương lai) và về `00 00 00` với mốc quá khứ, không âm, không `NaN`
- **12/12 đường dẫn asset** trong code trỏ tới file có thật · **0 import** `lib/data|actions|supabase|realtime`
- **i18n 45 = 45 key**, VI/EN không lệch tên · tsc 0 · lint 0 error · build thành công

**Hồi quy phát hiện thêm:** `site-footer.tsx` trước đây dùng `justify-between` với đúng MỘT con nên dòng bản quyền dạt trái — bản sửa của phase-08 **vá luôn** lỗi đó cho `/login`, không phải gây hồi quy.

### Session — 2026-08-06 (Phase-07 UI Login)
**Findings:** 2 Warning (minor) + 1 follow-up architectural (không sửa file)

| # | Finding | Severity | Disposition | Notes |
|---|---|---|---|---|
| RR-5 | **`role="alert"` render từ SSR** khi `?error=oauth` → live region có nội dung lúc mount, có thể screen reader không công bố. NVDA/VoiceOver thật chưa verify. | Warning | Accept (deferred) | Kiểm lúc phase-16 tích hợp OAuth hay manual browser test. Ghi "Còn treo". |
| RR-6 | **`namespace: string` không ràng buộc union.** Orchestrator REJECT: union type ép sửa file mỗi lần thêm namespace — chính cái vừa gỡ. Đã kiểm path traversal qua bundler module context: `.replace(NAMESPACE_PATH_PATTERN)` + try/catch gặp `*.json` lạ. Không khai thác được. | Suggestion | Reject (by design) | Generality forward-looking; chưa ai dùng param namespace, không nợ. Ghi vào clarifications. |

**Kiểm độc lập (orchestrator):**
- **5 file locale:** `locales/{vi,en}/{common,login}.json` + key bảng `5 vi = 5 en` ✓
- **Mỗi component < 200 dòng**, tổng phase < 30 dòng ✓
- **Bàn giao kiểm soát:** `lib/i18n/get-dictionary.ts` sửa từ `fs.readFile` sang `import()` template literal, `use-common-ui-text.ts` (phase-06) migrate sang hook mới; cùng khuôn 01→03, 01→04, 01→17 ✓
- **Lint/compile:** tsc 0 · next build success · curl /login → 200 VI+EN ✓
- **Live region:** chưa NVDA/VoiceOver, kiểm phase-16

**Unresolved (không che):**
1. **`useKudosStream` cho guest phụ thuộc cấu hình Realtime Authorization của Supabase local** — plan ghi bước kiểm và policy dự phòng (phase-05 bước 6), nhưng **chưa verify được ở giai đoạn lập kế hoạch** vì `supabase start` chưa từng chạy trên máy này. Nếu bản CLI bật Authorization mặc định cho Broadcast, phase-05 phải thêm policy trên `realtime.messages`; nếu không thì bỏ qua. Xác nhận ở bước đầu phase-05.
2. **Chưa rõ `realtime.send()` có sẵn trong bản Supabase local sẽ cài hay không.** Hàm này là đường phát Broadcast từ trigger; bản cũ hơn phải phát qua `pg_notify` + Edge Function. Nếu thiếu, phase-02 `0006b` phải đổi cách phát — kiến trúc (payload nghèo, refetch-on-signal) không đổi, chỉ cơ chế phát đổi. Kiểm ngay sau `supabase start` ở phase-01.
3. **PRE-REQ-01 chưa có người nhận.** Đã tách thành action-item và ghi rõ chuỗi bị chặn, nhưng "ai làm" vẫn trống — cần điều phối viên giao trước khi phase-02 xong, nếu không Track B sẽ dừng ở ranh giới phase-03.
4. **Ba finding Reject (#8, #11, #12) là nợ kỹ thuật có chủ đích, không phải đã giải quyết.** #12 đáng chú ý nhất: nếu tài khoản Google thật trả `raw_user_meta_data` thiếu `name`/`avatar_url`, `handle_new_user()` có thể lỗi và chặn đăng nhập vĩnh viễn cho tài khoản đó. User đã quyết không sửa; ghi lại ở đây để khi nó xảy ra thì biết ngay chỗ nhìn.
