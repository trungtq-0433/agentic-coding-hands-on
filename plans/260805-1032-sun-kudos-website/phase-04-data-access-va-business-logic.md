# Phase 04 — Data access & business logic

**Track:** B · **Priority:** P1 · **Status:** completed · **Effort:** 6h
**Phụ thuộc:** phase-03 · **Mở khoá:** phase-05
**KHÔNG có quan hệ blocks/blockedBy với bất kỳ phase Track A nào.**

## Context Links

- Quy tắc nghiệp vụ & validation: [`reports/researcher-260805-1032-momorph-requirements-synthesis.md`](./reports/researcher-260805-1032-momorph-requirements-synthesis.md) §4
- Server Function vs Server Action, `refresh()`/`revalidateTag`: [`reports/researcher-260805-1032-nextjs16-supabase-local.md`](./reports/researcher-260805-1032-nextjs16-supabase-local.md) §1
- Spec/TC gốc cần tra: `research/momorph/csv/tc-viet-kudo-ihQ26W78P2.csv` (57 TC validation), `tc-open-secret-box-J3-4YFIpMM.csv`, `tc-profile-ban-than-3FoIx6ALVb.csv`

## Overview

Toàn bộ đường đọc/ghi dữ liệu, không có một dòng JSX nào. Nguyên tắc chi phối: **mọi bất biến nghiệp vụ phải được ép ở server** — client chỉ được phép làm validation cho trải nghiệm, không được là nơi duy nhất luật tồn tại.

## Key Insights

1. **Ghi nhiều bảng phải nguyên tử → RPC.** Gửi một kudo chạm 3 bảng (`kudos`, `kudos_hashtags`, `kudos_images`). Ba lệnh `insert` rời từ client sẽ để lại kudos què nếu lỗi giữa chừng. → `create_kudos()` là hàm plpgsql một giao dịch. Và vì phase-02 đã `revoke` quyền ghi trực tiếp trên cả ba bảng, RPC là **đường duy nhất**, không phải đường được khuyến khích.
1b. **Không còn `p_mention_ids` / bảng `kudos_mentions`** — bỏ khỏi MVP vì không màn nào đọc (phase-02 Key Insight #7). `@mention` vẫn có ở UI, sống trong `body` dưới dạng text.
2. **Thả tim là RPC, không phải insert trần.** Ba luật cùng lúc: cấm tự-tim, một tim/user/kudos, +2 vào ngày đặc biệt. Không luật nào được để client quyết. **RPC TỰ TRA bảng `special_days`** bằng `now() AT TIME ZONE 'Asia/Ho_Chi_Minh'` để quyết định `is_special_day_bonus` — giá trị này **không bao giờ** nhận từ tham số. Nếu client truyền được cờ đó vào, ai cũng tự cộng +2 tim mọi ngày. Phase-02 đã `revoke insert, delete on hearts from authenticated`, nên RPC là đường duy nhất.
3. **Thu hồi tim đọc cờ từ chính hàng bị xoá**, không tính lại theo ngày hiện tại — nếu không, unlike sau nửa đêm sẽ trả sai số.
3b. **`toggle_heart` phải chống race giống `open_secret_box`.** Double-click gửi hai lời gọi song song: cả hai đọc "chưa tim", cả hai insert → một cái vỡ UNIQUE và ném lỗi thô lên UI, hoặc tệ hơn là toggle chồng nhau thành trạng thái sai. `open_secret_box` đã xử lý bằng `for update skip locked`; `toggle_heart` ban đầu không có gì. Sửa: khoá hàng `kudos` (`select … for update`) rồi mới quyết định insert/delete, và `insert … on conflict (kudos_id,user_id) do nothing` để lời gọi trùng thành no-op thay vì lỗi.
4. **Mở hộp là RPC server-authoritative.** TC bảo mật khẳng định số hộp chưa mở phải từ server và không thao túng được client-side. Random có trọng số chạy trong `open_secret_box()`, `SELECT ... FOR UPDATE` hàng grant để chống double-open khi bấm hai lần.
5. **Không tự tăng lạc quan số tim.** TC_WEB_PROFILE_FUN_014 đòi hiển thị đúng "giá trị SERVER báo về" → RPC `toggle_heart` trả về `heart_count` mới, UI dùng con số đó.
6. **Keyset cursor, không OFFSET.** Cursor = cặp `(created_at, id)`; điều kiện `(created_at, id) < (cursor_created_at, cursor_id)`. Kudos mới chèn vào giữa lúc đang cuộn sẽ không làm lặp/nhảy hàng.
7. **Feed đọc qua view, không qua bảng.** `public_kudos_feed` cho mọi feed công khai; `my_sent_kudos` cho tab "Đã gửi" của chính chủ. Query chạm thẳng `kudos` để đọc feed là lỗi bảo mật (phase-02 đã `revoke`).
8. **Hoa-thị là hàm thuần, không phải query.** `starCount(received) = received >= 50 ? 3 : received >= 20 ? 2 : received >= 10 ? 1 : 0`. Tính từ `profiles.received_kudos_count` sẵn có.
9. **`department_id` của user thật sẽ là NULL, và filter phải sống chung với điều đó.** Google OAuth không trả phòng ban; `handle_new_user()` chỉ chép name/avatar; không có màn sửa profile trong 18 màn. → mọi user đăng nhập thật đều `department_id = NULL`. Nếu filter Phòng ban chỉ `where department_id = ?` thì nó trả rỗng **im lặng** và trông như hỏng. Sửa: coi NULL là một nhóm hiển thị được — **"Chưa phân loại"** — đứng cuối danh sách dropdown. **Không** đẻ thêm màn chọn phòng ban: không có design cho nó trong 18 màn, tự thêm là vượt scope. Đây là hạn chế đã biết, đã ghi vào `clarifications.md` mục "Còn treo".

## Requirements

### Chức năng — Kudos
- Người nhận bắt buộc, phải là profile có thật, `sender_id <> recipient_id`.
- Nội dung bắt buộc, không rỗng sau khi trim.
- Hashtag **1–5** (bắt buộc ít nhất 1).
- Ảnh 0–5, chỉ `image/jpeg` và `image/png`; loại khác bị từ chối cả ở client lẫn server.
- `is_anonymous` mặc định `false`. **Không có** trường tên ẩn danh tự nhập. **Không có** `mentionIds`.

### Chức năng — Hearts
- 1 tim/user/kudos; bấm lại = thu hồi.
- Cấm tim kudos do chính mình gửi.
- Ngày trong `special_days` → +2 thay vì +1; thu hồi đúng số đã cộng.
- Cờ bonus do **RPC tự tra**, không nhận từ client.
- Lời gọi trùng do double-click là **no-op**, không phải lỗi UNIQUE ném lên UI.

### Chức năng — Secret Box
- Mở một lần nhận đúng **một** huy hiệu, trọng số 30/25/10/5/20/10.
- Số hộp chưa mở luôn từ server.
- Hết hộp → RPC trả lỗi có mã, không tạo badge.

### Chức năng — Truy vấn
- All Kudos: keyset, page 20, lọc theo hashtag và/hoặc phòng ban.
- Highlight: top-5 theo `heart_count desc, created_at desc`, cùng bộ lọc.
- Tổng số kudos (bộ đếm "388 KUDOS") + danh sách tên cho word-cloud — query lúc tải trang, **không** realtime (clarifications gap #13).
- Profile: hồ sơ + 5 chỉ số (kudos nhận / kudos gửi / tim nhận / box đã mở / box chưa mở) — **chỉ trả khi caller là chính chủ**, người khác nhận `stats = null`.
- Sunner autocomplete (Viết Kudo) + tìm kiếm Sunner (Spotlight, ≤100 ký tự).
- Master data: hashtags, departments.
- Leaderboard: 10 Sunner thăng hạng mới nhất, 10 Sunner nhận quà mới nhất.

### Phi chức năng
- Mỗi file `lib/data/*.ts` một domain, < 200 dòng.
- Schema Zod dùng chung cho client và server (DRY) — một định nghĩa, hai nơi gọi.
- Mọi Server Action mở đầu bằng `requireUser()`.

## Architecture

### Sơ đồ tầng

```
Client Component  ──(props/callback do phase-16 nối)──►  lib/actions/*.ts   ('use server')
                                                              │ requireUser()
                                                              │ zod parse
                                                              ▼
                                                       lib/data/*.ts  (query thuần)
                                                              │ supabase server client
                                                              ▼
                                            RPC plpgsql  /  view  /  bảng  (Postgres)
Server Component  ──────────────────────────────────►  lib/data/*.ts (đọc trực tiếp)
```

Ghi luôn đi qua `lib/actions` (có auth + validate). Đọc được phép gọi thẳng `lib/data` từ Server Component.

### Module

| File | Nội dung |
|---|---|
| `lib/data/kudos-queries.ts` | `listKudos(cursor, filters)`, `listHighlightKudos(filters)`, `getKudoById`, `countKudos()`, `listSpotlightNames()` |
| `lib/data/profile-queries.ts` | `getProfile(id)`, `getProfileStats(id, callerId)`, `listReceivedKudos`, `listSentKudos` (qua `my_sent_kudos`), `searchSunners(q)` |
| `lib/data/master-queries.ts` | `listHashtags()`, `listDepartments()` |
| `lib/data/secret-box-queries.ts` | `getUnopenedCount(userId)`, `listRecentPrizeWinners()`, `listRecentRankUps()` |
| `lib/actions/kudos-actions.ts` | `createKudoAction`, `uploadKudoImagesAction` |
| `lib/actions/heart-actions.ts` | `toggleHeartAction` |
| `lib/actions/secret-box-actions.ts` | `openSecretBoxAction` |
| `lib/validations/kudo-schema.ts` | Zod: body, recipientId, hashtagIds(1..5), images(≤5, mime), isAnonymous |
| `lib/validations/link-schema.ts` | Add Link Box: text 1–100 không-chỉ-khoảng-trắng, url http/https 5–2048 |
| `lib/validations/search-schema.ts` | Spotlight search ≤100 ký tự |
| `lib/kudos/star-count.ts` | hàm thuần 10/20/50 |
| `lib/kudos/cursor.ts` | encode/decode keyset cursor |

### RPC (migration `0008_business_rpc.sql`)

| Hàm | Chữ ký | Bất biến ép trong hàm |
|---|---|---|
| `create_kudos` | `(p_recipient uuid, p_body text, p_is_anonymous bool, p_hashtag_ids uuid[], p_image_urls text[]) returns uuid` | sender = `auth.uid()`; recipient tồn tại; sender≠recipient; 1≤hashtag≤5; ảnh≤5; body không rỗng |
| `toggle_heart` | `(p_kudos_id uuid) returns table(hearted bool, heart_count int)` | không tự-tim; `select … for update` trên hàng `kudos` rồi mới quyết; `insert … on conflict do nothing`; **bonus do hàm tự tra `special_days`**, không có tham số nào cho nó; thu hồi đọc `is_special_day_bonus` từ hàng bị xoá |
| `open_secret_box` | `() returns table(badge_id uuid, badge_code text, remaining int)` | `for update skip locked` một grant `unopened` của `auth.uid()`; random theo trọng số; hết hộp → `raise exception 'NO_UNOPENED_BOX'` |

Cả ba `security definer`, **`set search_path = public, pg_temp`**, và `revoke execute from anon`.
Chữ ký `create_kudos` **không có `p_mention_ids`** — bảng `kudos_mentions` đã bị bỏ khỏi MVP.

### Xử lý ảnh

Supabase Storage bucket `kudos-images`, policy: authenticated được INSERT vào thư mục `${auth.uid()}/`, ai cũng SELECT. Kiểm MIME **hai lớp**: `accept` ở input (UX) + kiểm `file.type` và phần mở rộng trong `uploadKudoImagesAction` (thật). Upload xong mới gọi `create_kudos` với mảng URL.

### Làm mới UI sau mutation

Dùng `revalidatePath('/kudos')` / `revalidatePath('/profile')` trong Server Action. **Không** dùng `updateTag`/`revalidateTag` — chưa có tag cache nào được đặt, thêm vào là phức tạp thừa (repo không bật `cacheComponents`, `fetch` mặc định no-store).

## Related Code Files

**Tạo mới**
- `supabase/migrations/0008_business_rpc.sql`
- `supabase/migrations/0009_storage_kudos_images.sql` (bucket + policy)
- `lib/data/{kudos-queries,profile-queries,master-queries,secret-box-queries}.ts`
- `lib/actions/{kudos-actions,heart-actions,secret-box-actions}.ts`
- `lib/validations/{kudo-schema,link-schema,search-schema}.ts`
- `lib/kudos/{star-count,cursor}.ts`
- `lib/kudos/kudo-card-mapper.ts` — một mapper duy nhất từ hàng view → `KudoCard` (TC_WEB_PROFILE_GUI_006 đòi card trên board và trên profile không được phân kỳ)

**Sửa**
- `package.json` — **chỉ thêm `zod` vào `dependencies`**. File này do phase-01 tạo/sở hữu; phase-04 và phase-17 nhận bàn giao tuần tự (01 → 04 → 17), mỗi phase chỉ chạm khối của mình: 01 deps nền + scripts supabase, 04 `zod`, 17 devDeps + scripts test. Ba phase chain tuần tự nên không có nguy cơ giẫm chân — ghi tường minh ở đây giống cách đã làm với `proxy.ts` giữa phase-01 → phase-03.
- `lib/supabase/database.types.ts` (sinh lại sau migration — bàn giao từ phase-02)

**Xoá:** không

**File ownership (glob):** `lib/data/**`, `lib/actions/{kudos,heart,secret-box}-actions.ts`, `lib/validations/**`, `lib/kudos/**`, `supabase/migrations/000[89]_*.sql`; bàn giao có kiểm soát: `package.json` (khối `dependencies`), `lib/supabase/database.types.ts`

## Implementation Steps

1. `npm i zod`.
2. Viết `0008_business_rpc.sql` với ba hàm ở bảng trên. Random có trọng số: cộng dồn `probability_weight` rồi `where cumulative >= random() * total order by cumulative limit 1`.
3. Viết `0009_storage_kudos_images.sql`: `insert into storage.buckets`, policy INSERT theo `(storage.foldername(name))[1] = auth.uid()::text`, policy SELECT `true`.
4. `npx supabase db reset` + `npm run supabase:types`.
5. `lib/kudos/cursor.ts`: `encodeCursor({createdAt,id})` → base64url, `decodeCursor` trả `null` khi hỏng (không throw — cursor rác từ URL không được làm sập trang).
6. `lib/kudos/star-count.ts` + `kudo-card-mapper.ts`.
7. `lib/validations/*`: Zod schema. `kudo-schema` xuất cả type suy ra để client và action dùng chung.
8. `lib/data/kudos-queries.ts`: mọi select **từ `public_kudos_feed`**. `listKudos` nhận `{cursor, hashtagId, departmentId, limit=20}`; lọc phòng ban = lọc theo phòng ban **người nhận** (spec dropdown-phòng-ban: "lọc ra các lời cảm ơn đến người thuộc phòng ban này").
8b. **Xử lý `department_id = NULL`**: `listDepartments()` trả thêm một mục ảo `{id: 'unassigned', name: 'Chưa phân loại'}` đứng cuối. `listKudos` khi nhận `departmentId === 'unassigned'` thì lọc `recipient_department_id is null`, ngược lại lọc `= ?`. Không có nhánh này thì user thật (luôn NULL phòng ban) biến mất khỏi mọi kết quả filter mà không báo lỗi gì.
9. `lib/data/profile-queries.ts`: `getProfileStats(targetId, callerId)` → `targetId !== callerId` thì trả `null` **trước khi query** (rẻ hơn, và là một nhánh dữ liệu duy nhất quyết định self/other như TC_WEB_PROFILE_FUN_006 mô tả). `listSentKudos` chỉ đọc `my_sent_kudos`, không nhận tham số userId.
10. `lib/actions/kudos-actions.ts`: `requireUser()` → `kudoSchema.parse` → upload ảnh (nếu có) → `rpc('create_kudos', …)` → `revalidatePath('/kudos')`. Trả `{ok:true, kudoId}` hoặc `{ok:false, code, fieldErrors}` — **không throw** để UI hiện lỗi theo trường.
11. `lib/actions/heart-actions.ts`: gọi `rpc('toggle_heart')`. Trả **cùng hình dạng kết quả với hai action kia** — `{ok:true, hearted, heartCount}` hoặc `{ok:false, code}` với `code ∈ {'SELF_HEART','NOT_FOUND','UNAUTHENTICATED'}`. Ban đầu action này trả thẳng `{hearted, heartCount}` không có nhánh lỗi, khiến UI không phân biệt được "server từ chối" với "mạng hỏng". Ba action phải cùng một hình dạng để `kudo-card` xử lý lỗi một kiểu.
12. `lib/actions/secret-box-actions.ts`: gọi `rpc('open_secret_box')`; bắt `NO_UNOPENED_BOX` → trả `{ok:false, code:'NO_UNOPENED_BOX'}`.
13. Kiểm tay trong Studio: gọi từng RPC với `set request.jwt.claims` giả lập, đối chiếu với Success Criteria.

## Todo List

- [x] `npm i zod` (chỉ chạm khối `dependencies` của `package.json`)
- [x] Migration `0008` ba RPC + `set search_path = public, pg_temp` + `revoke execute from anon`
- [x] `toggle_heart`: `for update` + `on conflict do nothing` + tự tra `special_days` (không có tham số bonus)
- [x] `heart-actions.ts` trả `{ok:false, code}` như hai action kia
- [x] Nhóm "Chưa phân loại" cho `department_id is null`
- [x] Migration `0009` bucket + policy Storage
- [x] `lib/kudos/{cursor,star-count,kudo-card-mapper}.ts`
- [x] 3 file `lib/validations/*`
- [x] 4 file `lib/data/*` — đọc feed **chỉ** qua view
- [x] 3 file `lib/actions/*` — mở đầu bằng `requireUser()`
- [x] `getProfileStats` trả `null` cho người khác
- [x] Kiểm tay 8 kịch bản ở Success Criteria
- [x] Sinh lại `database.types.ts`

## Success Criteria

- Gửi kudo 0 hashtag → từ chối; 6 hashtag → từ chối; 1 và 5 hashtag → nhận.
- Gửi kudo cho chính mình qua RPC (bỏ qua UI) → từ chối bởi RPC **và** bởi CHECK.
- Upload `.pdf`/`.mp4`/`.txt` → từ chối ở action, không có file nào vào Storage.
- Gửi kudo lỗi giữa chừng (ví dụ hashtag không tồn tại) → **không** còn hàng mồ côi trong `kudos` (kiểm bằng `count(*)` trước/sau).
- `toggle_heart` trên kudo của chính mình → `{ok:false, code:'SELF_HEART'}`; trên kudo người khác → `heart_count` +1.
- **Race double-click**: gọi `toggle_heart` hai lần song song trên cùng kudo → kết thúc ở trạng thái nhất quán (đã tim HOẶC chưa tim), `heart_count` khớp `count(*)` thực trong `hearts`, và **không** có lỗi UNIQUE nào lọt lên UI.
- Cố truyền cờ bonus vào `toggle_heart` → không thể: chữ ký hàm không có tham số đó. Thêm hàng `special_days` cho hôm nay → tim mới tự động +2 mà client không làm gì.
- `listKudos({departmentId:'unassigned'})` → trả đúng kudos của người nhận chưa có phòng ban (kịch bản của **mọi** user đăng nhập thật).
- Thêm `today` vào `special_days` → tim mới cộng +2; xoá tim đó → trở lại đúng số cũ (không phải trừ 1).
- Đặt ngày hệ thống sang hôm sau rồi mới unlike → vẫn trừ đúng 2.
- `open_secret_box` gọi song song 2 lần với user chỉ có 1 hộp → đúng **một** lần thành công, lần kia `NO_UNOPENED_BOX`.
- Gọi `open_secret_box` 10.000 lần trên dữ liệu giả → phân phối 6 badge lệch < 2% so với 30/25/10/5/20/10.
- `listKudos` cuộn 5 trang liên tiếp trong khi có kudo mới chèn vào → không hàng nào lặp hoặc bị bỏ.
- `getProfileStats(A, B)` → `null`; `getProfileStats(A, A)` → đủ 5 chỉ số.
- `grep -rn "from('kudos')" lib/data` chỉ khớp ở chỗ ghi, không khớp ở chỗ đọc feed.

## Risk Assessment

| Rủi ro | K/năng × T/động | Giảm thiểu |
|---|---|---|
| Đặt luật nghiệp vụ ở client rồi quên ép ở server | Cao × **Rất cao** | Ba RPC là nơi duy nhất luật sống; Success Criteria bắt buộc test bằng cách bỏ qua UI |
| Double-open secret box do double-click | TB × Cao | `for update skip locked` trong RPC + disable nút sau lần bấm đầu (phase-16) |
| Thu hồi tim sai số sau nửa đêm | TB × TB | Đọc cờ từ hàng bị xoá; có case test đổi ngày |
| Keyset cursor rác từ URL làm sập trang | TB × TB | `decodeCursor` trả `null` thay vì throw, fallback về trang đầu |
| Card trên board và trên profile phân kỳ | TB × TB | Một `kudo-card-mapper.ts` duy nhất, cùng danh sách cột (TC_WEB_PROFILE_GUI_006) |
| Rich text `body` chứa payload XSS | TB × Cao | DB lưu thô; sanitize bắt buộc ở phase-16 khi render; không `dangerouslySetInnerHTML` chưa sanitize |
| Bộ lọc phòng ban hiểu nhầm là lọc theo người **gửi** | TB × TB | Ghi rõ ở bước 8: lọc theo phòng ban người **nhận** |
| Kudos ẩn danh vẫn lộ qua `kudos_images` | Thấp × Cao | Không select `sender_id` từ các bảng con; join luôn đi qua view |
| Double-click tim → lỗi UNIQUE thô lên UI hoặc trạng thái toggle sai | **Cao** × TB | `for update` + `on conflict do nothing` trong RPC; prop `pending` disable icon (phase-09); có case race trong Success Criteria |
| Client tự đặt `is_special_day_bonus` để +2 mọi ngày | TB × Cao | Không có tham số đó trong chữ ký; `revoke insert on hearts` ở phase-02 đóng đường vòng |
| Filter Phòng ban trả rỗng im lặng với mọi user thật | **Cao** × TB | Nhóm "Chưa phân loại" + case riêng trong Success Criteria |

## Security Considerations

- Ba RPC `security definer` → **bắt buộc** `set search_path = public` để chống chiếm quyền qua schema giả.
- `revoke execute ... from anon` cho cả ba RPC — guest không được ghi gì.
- Action nào cũng bắt đầu bằng `requireUser()`; không dựa vào việc "UI đã ẩn nút".
- Storage: user chỉ upload được vào thư mục mang uuid của chính mình → không đè file người khác.
- `searchSunners` giới hạn 100 ký tự và escape ký tự `%`/`_` trước khi `ilike` để tránh truy vấn quét toàn bảng.
- Không log `body` kudos ra console server (nội dung riêng tư).

## Next Steps

- phase-05 subscribe realtime lên `kudos`/`hearts`, dùng lại `kudo-card-mapper`.
- phase-16 thay mock của Track A bằng chính các hàm ở đây.
- phase-17 viết pgTAP cho ba RPC ở phase này (+ `admin_grant_secret_box` của phase-02, thành 4) + unit test cho `cursor`, `star-count`, các Zod schema.

## Rollback

Revert commit + `npx supabase db reset` (bỏ 0008/0009). Ảnh đã upload nằm trong Storage local, xoá bằng `npx supabase storage rm` hoặc reset volume. Không có dữ liệu thật.

## Kết quả thực thi

Hoàn thành 2026-08-05.
- **Đầu ra:** 2 migration (`0008_business_rpc.sql`, `0009_storage_kudos_images.sql`) + 17 file `lib/{kudos,validations,data,actions}/**` + `zod` vào deps + types được sinh lại.
- **Cơ chế kiểm soát:** tsc 0 · lint 0 · build compiled · db reset idempotent 2 lần.
- **12/12 hàm security definer:** có `search_path=public, pg_temp` ✓
- **3 RPC:** anon KHÔNG execute được, authenticated được ✓; `toggle_heart` chỉ 1 tham số (không có cửa cho client đặt bonus) ✓
- **Race double-click `toggle_heart`:** xử lý bằng `for update skip locked` + `on conflict do nothing` ✓
- **Phân phối badge:** 10.000 lần → lệch tối đa **0,74%** ✓ (ngưỡng 2%)
- **Đường đọc:** **0** lần `.from('kudos')` thật (1 khớp duy nhất là comment), 7 `public_kudos_feed` + 2 `my_sent_kudos` ✓
- **Bảo mật:** `postgres_changes` rỗng ✓ · bucket `kudos-images` + 2 policy tồn tại ✓
