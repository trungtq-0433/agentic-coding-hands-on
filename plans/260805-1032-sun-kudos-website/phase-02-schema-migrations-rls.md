# Phase 02 — Schema, migrations, RLS, seed

**Track:** B · **Priority:** P1 · **Status:** pending · **Effort:** 6h
**Phụ thuộc:** phase-01 · **Mở khoá:** phase-03
**KHÔNG có quan hệ blocks/blockedBy với bất kỳ phase Track A nào.**

## Context Links

- Data model đề xuất: [`reports/researcher-260805-1032-momorph-requirements-synthesis.md`](./reports/researcher-260805-1032-momorph-requirements-synthesis.md) §2
- Ma trận quyền (input RLS): cùng report §3
- Business rules: cùng report §4
- Pattern RLS + `user_roles` + test policy: [`reports/researcher-260805-1032-nextjs16-supabase-local.md`](./reports/researcher-260805-1032-nextjs16-supabase-local.md) §5
- Danh sách seed gốc: `research/momorph/csv/spec-dropdown-hashtag-filter-JWpsISMAaM.csv` (13 hashtag), `spec-dropdown-phong-ban-WXK5AYB_rG.csv` (**50** phòng ban — đếm bằng parser, xem bước 8b), `spec-open-secret-box-J3-4YFIpMM.csv` (6 huy hiệu + tỉ lệ)

## Overview

Toàn bộ schema Postgres, index, RLS policy, hai view bảo mật và seed dữ liệu demo. Đây là phase mang nhiều rủi ro bảo mật nhất của cả plan — quyết định "che danh tính người gửi ẩn danh ở tầng DB, không ở tầng UI" nằm ở đây.

## Key Insights

1. **Che ẩn danh phải nằm ở DB, không ở UI.** RLS chặn theo *hàng*, không theo *cột*; feed Kudos lại là public. Nếu để component tự ẩn tên người gửi thì bất kỳ ai gọi thẳng PostgREST đều đọc được `sender_id`. → dựng view `public_kudos_feed` trả `sender_*` = NULL khi `is_anonymous`, và **thu hồi quyền SELECT trực tiếp trên bảng `kudos` với `anon`/`authenticated`**.
2. **Sent-list dùng definer view.** `my_sent_kudos` với `security_invoker = false` (mặc định của Postgres), mệnh đề `where sender_id = auth.uid()` chính là ranh giới an ninh — đúng như TC_WEB_PROFILE_SEC_002/003 mô tả.
3. **Role đặt ở bảng `user_roles` riêng, không phải cột `profiles.role`.** Report Next/Supabase §5 xếp hạng: scope 2 role thì bảng đơn giản hơn Custom Access Token Hook, và gỡ quyền có hiệu lực tức thì. Bonus: `profiles` giữ đúng các cột hiển thị công khai, khớp TC_WEB_PROFILE_SEC_004 ("không lộ email/auth identifier"). **Đây là điều chỉnh có chủ đích so với đề xuất `profiles.role` ở report requirements §2.**
4. **Đếm tim phải denormalize.** Highlight Kudos xếp top-5 theo tim và Realtime cần một sự kiện UPDATE để bám. → `kudos.heart_count` do trigger trên `hearts` duy trì; trọng số 2 khi `is_special_day_bonus`.
5. **Hoa-thị cũng denormalize.** `profiles.received_kudos_count` do trigger duy trì (mọi card đều hiển thị hoa-thị → tính lại mỗi lần render là N+1).
6. **`kudos.anonymous_alias` bị loại bỏ** — clarifications gap #4 chốt nhãn cố định, không có field tự nhập.
7. **Không dựng `awards`, `event_config`, `notifications`, `kudos_mentions`.** Ba cái đầu: gap #10 (tĩnh), gap #1 (env var), gap #14 (chưa có spec trigger). **`kudos_mentions` bị bỏ khỏi MVP** — không màn nào ĐỌC nó: không có notification, không có trang "kudos nhắc tới tôi", không có truy vấn nào trong 18 màn cần nó. Ghi vào một bảng mà không ai đọc là chi phí thuần (migration + RLS + tham số RPC + type). `@mention` vẫn giữ ở UI, sống trong `body` dưới dạng text. Dựng lại khi có tính năng thật cần đọc.
8. `db reset` xoá sạch dữ liệu mỗi lần → `seed.sql` là **nguồn sự thật** cho dữ liệu demo, không phải "chạy một lần rồi để yên".
9. **RLS chỉ chặn được cái nó được giao chặn.** Phase-04 đặt mọi luật nghiệp vụ trong RPC, nhưng nếu `authenticated` vẫn còn quyền INSERT thẳng vào `kudos`/`hearts` thì client chỉ cần gọi PostgREST là đi vòng qua toàn bộ RPC: gửi kudo 0 hashtag, thả tim kudo của chính mình, tự set `is_special_day_bonus = true` để +2 tim mọi ngày. → **`revoke` quyền ghi trực tiếp trên `kudos`, `kudos_hashtags`, `kudos_images`, `hearts`**, đúng cách đã làm với `secret_box_grants`. Policy INSERT `with check (auth.uid() = sender_id)` là **không đủ** — nó xác thực *ai ghi*, không xác thực *ghi cái gì*.
10. **`revoke select on kudos` giết Realtime Postgres Changes.** Postgres Changes uỷ quyền từng subscriber bằng chính RLS/grant của bảng; bảng đã bị thu quyền SELECT thì không sự kiện nào tới được client. Hai lựa chọn loại trừ nhau, và **an toàn thắng tiện lợi**: giữ `revoke`, chuyển realtime sang **Broadcast phát từ trigger** với payload chỉ mang id (chi tiết ở phase-05). Đây là quyết định kiến trúc chứ không phải chi tiết triển khai — nếu ai đó "sửa" bằng cách bỏ `revoke` để Postgres Changes chạy lại thì lỗ hổng ẩn danh mở lại ngay.

## Requirements

### Chức năng
- 12 bảng + 2 view + 5 trigger, đủ phục vụ 18 màn.
- Seed: **50 phòng ban**, 13 hashtag, 6 huy hiệu đúng trọng số 30/25/10/5/20/10, 3–5 ngày đặc biệt, ~8 profile demo, ~30 kudos demo (có cả ẩn danh), một ít tim, vài `secret_box_grants` chưa mở.
- Ràng buộc DB: `sender_id <> recipient_id`, UNIQUE(`kudos_id`,`user_id`) trên `hearts`, ≤5 hashtag & ≤5 ảnh mỗi kudos.
- **Thu hồi quyền ghi trực tiếp** trên `kudos`, `kudos_hashtags`, `kudos_images`, `hearts` — mọi ghi qua RPC.
- Trigger phát Broadcast làm tín hiệu realtime (payload chỉ id).
- RPC admin cấp thêm Secret Box giữa sự kiện.

### Phi chức năng
- Mỗi file migration một mối quan tâm, ≤ 200 dòng.
- Mọi bảng đều `enable row level security` — không sót bảng nào.
- `npx supabase db reset` chạy sạch từ đầu tới cuối, không lỗi.

## Architecture

### Bảng

| Bảng | Cột chính | Ghi chú thiết kế |
|---|---|---|
| `departments` | `id`, `code` unique, `name`, `parent_id` self-FK null | Phân cấp suy từ tên lồng nhau ("CEVC2 - CySS"). **50 mục**, đếm bằng parser (xem Implementation Steps bước 8b), không đếm tay |
| `profiles` | `id` uuid PK FK `auth.users`, `full_name`, `avatar_url`, `department_id`, `received_kudos_count` int default 0, `sent_kudos_count` int default 0, `received_hearts_count` int default 0, `created_at` | **Không** có email/role. Ba counter do trigger duy trì |
| `user_roles` | `user_id` uuid PK FK `auth.users`, `role` text check in ('user','admin') | Tách khỏi `profiles` vì lý do ở Key Insight #3 |
| `hashtags` | `id`, `name` unique, `sort_order` | Seed 13 dòng |
| `kudos` | `id`, `sender_id`, `recipient_id`, `body` text, `is_anonymous` bool default false, `status` text default 'active', `heart_count` int default 0, `created_at` | CHECK `kudos_no_self` |
| `kudos_hashtags` | PK(`kudos_id`,`hashtag_id`) | Số lượng 1–5 ép ở RPC (phase-04) + trigger đếm |
| `kudos_images` | `id`, `kudos_id`, `url`, `position` smallint check 0..4 | ≤5 |
| `hearts` | `id`, `kudos_id`, `user_id`, `is_special_day_bonus` bool, `created_at`, UNIQUE(`kudos_id`,`user_id`) | Cờ bonus **do RPC tra `special_days` mà đặt**, client không truyền vào được (đã `revoke insert`); dùng lại lúc DELETE |
| `special_days` | `id`, `day` date unique, `note` | Seed tay, chưa có UI admin |
| `badges` | `id`, `code` unique, `name`, `image_url`, `probability_weight` int | 30/25/10/5/20/10 (tổng 100) |
| `profile_badges` | PK(`profile_id`,`badge_id`), `awarded_at` | Bộ sưu tập 6 slot trên Profile |
| `secret_box_grants` | `id`, `profile_id`, `status` check in ('unopened','opened'), `badge_id` null, `opened_at` null, `created_at` | Ledger; **rule cấp phát để ngỏ** (clarifications gap #9) |

Cố tình **không dựng**: `awards` (tĩnh), `event_config` (env var), `notifications` (chưa có spec trigger — gap #14), **`kudos_mentions`** (không màn nào đọc — xem Key Insight #7). Cả bốn dựng lại khi có tính năng thật cần đến, không dựng sẵn.

### View

```
public_kudos_feed  (security_invoker = false)
  → mọi cột kudos + sender_id/full_name/avatar_url/department NULL khi is_anonymous
  → grant select to anon, authenticated
  → dùng cho: Live board All Kudos, Highlight, Profile "Đã nhận"

my_sent_kudos      (security_invoker = false)
  → where sender_id = auth.uid(), KHÔNG che ẩn danh (tự xem thì thấy)
  → grant select to authenticated (KHÔNG grant anon)
  → dùng cho: Profile self → tab "Đã gửi"
```

### Trigger

| Trigger | Trên | Việc |
|---|---|---|
| `trg_kudos_counters` | `kudos` AFTER INSERT/DELETE | `profiles.received_kudos_count` (+recipient), `sent_kudos_count` (+sender) |
| `trg_heart_counters` | `hearts` AFTER INSERT/DELETE | `kudos.heart_count` ±(2 nếu bonus, ngược lại 1); `profiles.received_hearts_count` của recipient tương ứng. Đọc `NEW.is_special_day_bonus` khi INSERT và **`OLD.is_special_day_bonus` khi DELETE** — không tính lại theo `now()`. Cờ này đáng tin **vì và chỉ vì** đã `revoke insert on hearts from authenticated`: chỉ RPC đặt được nó |
| `trg_kudos_hashtag_limit` | `kudos_hashtags` BEFORE INSERT | RAISE nếu kudos đã có 5 hashtag |
| `trg_kudos_broadcast` | `kudos` AFTER INSERT/UPDATE | `realtime.send()` lên topic `kudos-board`, payload **chỉ** `{kudos_id, event:'insert'\|'update'}` |
| `trg_hearts_broadcast` | `hearts` AFTER INSERT/DELETE | `realtime.send()` lên topic `user-hearts:<user_id>`, payload `{kudos_id, hearted:bool}` |

### Chính sách RLS (rút gọn)

**Nguyên tắc: đọc thì qua view, ghi thì qua RPC. Không bảng nghiệp vụ nào nhận ghi trực tiếp từ client.**

| Bảng | anon | authenticated | Ghi chú |
|---|---|---|---|
| `profiles` | SELECT all | SELECT all | Chỉ cột public tồn tại; không UPDATE cho ai (profile read-only) |
| `departments`, `hashtags`, `badges`, `special_days` | SELECT | SELECT | master data, chỉ đọc |
| `kudos` | ✗ (revoke ALL) | ✗ SELECT (revoke), **✗ INSERT/UPDATE/DELETE (revoke)** | đọc qua `public_kudos_feed`/`my_sent_kudos`; ghi qua `create_kudos()` |
| `kudos_hashtags`, `kudos_images` | SELECT | SELECT; **✗ INSERT/UPDATE/DELETE (revoke)** | ghi qua `create_kudos()` |
| `hearts` | SELECT (để đếm) | SELECT; **✗ INSERT/DELETE (revoke)** | ghi qua `toggle_heart()`, hàm tự tra `special_days` |
| `user_roles` | ✗ | SELECT chính chủ; ✗ ghi | `is_admin()` là security definer |
| `profile_badges` | SELECT | SELECT; ✗ ghi | bộ sưu tập công khai; ghi qua `open_secret_box()` |
| `secret_box_grants` | ✗ | SELECT chính chủ; ✗ ghi | mở qua `open_secret_box()`, cấp qua `admin_grant_secret_box()` |

Vì sao `revoke` chứ không chỉ dựa vào policy: policy `with check (auth.uid() = sender_id)` chỉ trả lời *"ai đang ghi"*. Nó **không** chặn được kudo 0 hashtag, tim vào kudo của chính mình, hay `is_special_day_bonus = true` do client tự đặt. Những luật đó sống trong RPC, nên đường vào trực tiếp phải đóng.

Helper: `is_admin() returns boolean language sql security definer stable **set search_path = public, pg_temp**`.
Hàm `security definer` **luôn** phải cố định `search_path` — nếu không, kẻ tấn công tạo schema riêng chứa hàm/bảng cùng tên và chiếm được quyền của owner. Ba RPC phase-04 đã theo quy tắc này; `is_admin()` và `handle_new_user()` (phase-03) phải theo cùng.

## Related Code Files

**Tạo mới**
- `supabase/migrations/0001_core_master_tables.sql` — departments, hashtags, badges, special_days
- `supabase/migrations/0002_profiles_and_roles.sql` — profiles, user_roles, `is_admin()`
- `supabase/migrations/0003_kudos_tables.sql` — kudos, kudos_hashtags, kudos_images, hearts (**không có `kudos_mentions`**)
- `supabase/migrations/0004_secret_box_tables.sql` — profile_badges, secret_box_grants, RPC `admin_grant_secret_box()`
- `supabase/migrations/0005_triggers_and_indexes.sql` — 3 trigger counter + 7 index
- `supabase/migrations/0006_views_and_rls.sql` — 2 view, toàn bộ grant/revoke, policy
- `supabase/migrations/0006b_realtime_broadcast_triggers.sql` — 2 trigger phát Broadcast
- `supabase/seed.sql`
- `scripts/count-departments.mjs` — parser đếm phòng ban từ CSV nguồn (chống đếm tay sai)

**Sửa:** `lib/supabase/database.types.ts` (sinh lại, **không sửa tay**)

**Xoá:** không

**File ownership (glob):** `supabase/migrations/000[1-6]*_*.sql`, `supabase/seed.sql`, `lib/supabase/database.types.ts`, `scripts/count-departments.mjs`
Phase-03 sở hữu `0007_*.sql`, phase-04 sở hữu `0008_*` và `0009_*` — ba phase không chạm cùng file.

## Implementation Steps

1. `npx supabase migration new core_master_tables` … lặp cho 6 migration, viết SQL tay (không `db diff` — schema chưa tồn tại ở đâu để diff).
2. `0001`: 4 bảng master, đều `enable row level security` + policy `select using (true)`.
3. `0002`: `profiles` (FK `auth.users` ON DELETE CASCADE), `user_roles`, hàm `is_admin()` **có `set search_path = public, pg_temp`**. **Không** thêm cột email/role vào `profiles`.
4. `0003`: `kudos` + CHECK `kudos_no_self`; `kudos_hashtags`, `kudos_images`; `hearts` + UNIQUE(`kudos_id`,`user_id`). **Không tạo `kudos_mentions`.**
5. `0004`: `profile_badges`, `secret_box_grants`, và RPC `admin_grant_secret_box(p_profile_ids uuid[], p_count int)` — `security definer`, `set search_path = public, pg_temp`, mở đầu bằng `if not is_admin() then raise exception 'FORBIDDEN'; end if;`. Đây là đường cấp hộp giữa sự kiện (xem Runbook cuối file).
6. `0005`: 3 trigger counter + index: `kudos(recipient_id, created_at desc, id desc)`, `kudos(sender_id, created_at desc, id desc)`, `kudos(heart_count desc, created_at desc)`, `hearts(kudos_id)`, `hearts(user_id)`, `kudos_hashtags(hashtag_id)`, `profiles(department_id)`. Cặp `(created_at desc, id desc)` là để keyset cursor không lặp/nhảy hàng.
7. `0006`: 2 view + toàn bộ grant/revoke/policy. Khối `revoke` phải viết tường minh, **không** dựa vào mặc định:
   ```sql
   revoke all on kudos from anon, authenticated;
   revoke insert, update, delete on kudos_hashtags, kudos_images from anon, authenticated;
   revoke insert, update, delete on hearts from anon, authenticated;
   grant select on kudos_hashtags, kudos_images, hearts to anon, authenticated;
   grant select on public_kudos_feed to anon, authenticated;
   grant select on my_sent_kudos to authenticated;   -- KHÔNG grant anon
   ```
7b. `0006b`: 2 trigger Broadcast. Payload **tối thiểu**, chỉ id và loại event — tuyệt đối không kèm `sender_id`, `body`, hay bất cứ cột nội dung nào. Trigger là `security definer` + `set search_path`. Lý do payload nghèo: kênh Broadcast không đi qua RLS của bảng, nên bất cứ thứ gì nhét vào payload là công khai với người nghe kênh.
8. `supabase/seed.sql`: theo đúng thứ tự departments → hashtags → badges → special_days → auth.users demo (dùng `auth.admin` insert hoặc INSERT thẳng `auth.users` với `encrypted_password` giả) → profiles → user_roles (1 admin) → kudos → kudos_hashtags → hearts → secret_box_grants. Seed phải để trigger tự tính counter, **không** ghi cứng `heart_count`. Seed chạy với quyền owner nên không vướng `revoke`.
8b. **Đếm phòng ban bằng parser, không bằng mắt.** `scripts/count-departments.mjs` đọc `research/momorph/csv/spec-dropdown-phong-ban-WXK5AYB_rG.csv`, tách theo tập mã gốc (`CTO SPD FCOV CEVC1-4 CEVEC STVC OPDC GEU PAO IAV CPV BDV`) và in ra danh sách. Kết quả đã chạy: **50 mục, 0 trùng lặp**.
   **Bất thường ở nguồn:** mục thứ 50 là `PAO - PAO` — một phòng ban con trùng tên cha (`PAO` là mục 33). Không phải dòng lặp, mà gần như chắc chắn là lỗi nhập liệu bên soạn spec. **Xử lý:** vẫn seed đủ 50 với `code = 'PAO-PAO'`, `parent_id → PAO`, kèm comment `-- FIXME(nguồn): trùng tên cha, chờ xác nhận từ người soạn spec`. Không tự ý gộp hay bỏ — dữ liệu tổ chức không phải chỗ để agent tự quyết. Đã ghi vào `clarifications.md` mục "Còn treo".
9. `npx supabase db reset` → không lỗi. `npm run supabase:types` → `database.types.ts` đầy đủ.
10. Kiểm RLS thủ công trong Studio SQL Editor: `set role authenticated; set request.jwt.claims = '{"sub":"<uuid-user-A>"}'; select * from my_sent_kudos;` → chỉ ra kudos của A. Đổi sub sang user B → chỉ ra kudos của B. `select sender_id from public_kudos_feed where is_anonymous;` → toàn NULL.

## Todo List

- [ ] 7 file migration `0001`–`0006` + `0006b`
- [ ] Mọi bảng `enable row level security`, không sót
- [ ] `is_admin()` có `set search_path = public, pg_temp`
- [ ] CHECK `kudos_no_self` + UNIQUE `hearts(kudos_id,user_id)`
- [ ] 3 trigger counter + 7 index + 2 trigger Broadcast (payload chỉ id)
- [ ] View `public_kudos_feed` (che ẩn danh) + `my_sent_kudos` (definer, self-only)
- [ ] Khối `revoke` đủ 4 bảng: `kudos` (all), `kudos_hashtags`/`kudos_images`/`hearts` (ghi)
- [ ] RPC `admin_grant_secret_box()` + runbook hết hộp
- [ ] `scripts/count-departments.mjs` + seed đủ **50** phòng ban (có `PAO - PAO` kèm FIXME)
- [ ] `seed.sql` đủ 13 hashtag / 6 badge đúng trọng số / demo data
- [ ] `npx supabase db reset` xanh
- [ ] `npm run supabase:types` sinh lại type
- [ ] Kiểm RLS bằng 2 phiên giả lập + kiểm ghi trực tiếp bị chặn

## Success Criteria

- `npx supabase db reset` exit 0, không warning về bảng thiếu RLS.
- `select count(*) from badges` = 6 và `sum(probability_weight)` = 100.
- `select count(*) from departments` = **50** (khớp output `scripts/count-departments.mjs`); `select count(*) from hashtags` = 13.
- `select count(*) from pg_tables where tablename = 'kudos_mentions'` = 0.
- **Ghi trực tiếp bị chặn** — với phiên `authenticated` giả lập, cả 4 lệnh sau đều lỗi quyền:
  `insert into kudos(...)` · `insert into kudos_hashtags(...)` · `insert into hearts(...)` · `delete from hearts where ...`
- `select prosecdef, proconfig from pg_proc where proname in ('is_admin','handle_new_user')` → cả hai có `search_path=public, pg_temp`.
- Gọi `admin_grant_secret_box()` bằng phiên user thường → `FORBIDDEN`; bằng phiên admin → số hàng `unopened` tăng đúng.
- Giả lập user A: `select * from my_sent_kudos` trả **đúng** số kudos A gửi (kể cả ẩn danh); giả lập user B: không thấy hàng nào của A.
- `select sender_id, sender_full_name from public_kudos_feed where is_anonymous = true` → toàn NULL.
- `insert into kudos(sender_id, recipient_id, ...) values (X, X, ...)` bị từ chối bởi CHECK.
- Thả tim 2 lần cùng user cùng kudos → lỗi UNIQUE.
- Thả tim vào ngày có trong `special_days` → `kudos.heart_count` +2; xoá tim đó → về đúng giá trị cũ.
- `lib/supabase/database.types.ts` có type cho cả **12** bảng và 2 view.

## Risk Assessment

| Rủi ro | K/năng × T/động | Giảm thiểu |
|---|---|---|
| Quên `revoke` trên `kudos` → lộ `sender_id` của kudos ẩn danh qua PostgREST | TB × **Rất cao** | Có mục riêng trong Success Criteria; phase-17 có test tích hợp gọi thẳng REST bằng anon key |
| View tạo nhầm `security_invoker = true` → RLS đá ngược, Sent-list rỗng | TB × Cao | Viết tường minh `with (security_invoker = false)` và kiểm bằng 2 phiên giả lập |
| Trigger counter lệch khi seed hoặc khi xoá kudos | TB × TB | Trigger xử lý cả INSERT lẫn DELETE; test đối chiếu counter với `count(*)` ở phase-17 |
| Thu hồi tim sai số sau khi qua ngày | TB × TB | Đọc `is_special_day_bonus` **từ chính hàng bị xoá**, không tính lại theo `now()` |
| Seed `auth.users` bằng tay sai định dạng → `db reset` fail | Cao × Thấp | Dùng đúng cột bắt buộc; nếu vướng thì chuyển sang script Node gọi `auth.admin.createUser` chạy sau reset |
| Đổi schema về sau làm `database.types.ts` lệch | TB × TB | Quy ước: mọi migration mới kèm chạy `npm run supabase:types` trong cùng commit |
| Chỉ dựa policy `with check` mà quên `revoke` → client đi vòng qua RPC bằng PostgREST | TB × **Rất cao** | Khối `revoke` tường minh ở bước 7 + 4 case "ghi trực tiếp bị chặn" trong Success Criteria + pgTAP phase-17 |
| Ai đó gỡ `revoke select on kudos` để "sửa" realtime | TB × **Rất cao** | Key Insight #10 ghi rõ đánh đổi; realtime đã chuyển sang Broadcast nên không còn lý do gỡ; pgTAP đỏ nếu gỡ |
| Nhét nội dung vào payload Broadcast cho tiện | TB × Cao | Bước 7b ghi rõ payload chỉ id; Success Criteria phase-05 kiểm bằng phiên anon |
| Hàm `security definer` thiếu `search_path` → chiếm quyền qua schema giả | TB × Cao | Bước 3/5/7b + case `pg_proc` trong Success Criteria |
| Đếm phòng ban bằng mắt rồi seed thiếu | **Cao** × TB | `scripts/count-departments.mjs` là nguồn số; bản kế hoạch đầu ghi nhầm 48, parser cho ra 50 |
| Hết Secret Box giữa sự kiện, không có đường cấp thêm | TB × Cao | RPC `admin_grant_secret_box()` + runbook cuối file |

## Security Considerations

- Ranh giới an ninh của Sent-list là **mệnh đề WHERE trong definer view**, không phải điều kiện `if` trong React. Không được thay bằng lọc phía client.
- Ranh giới ẩn danh là **view `public_kudos_feed`**, không phải component. Bất kỳ query nào của app chạm thẳng bảng `kudos` để đọc feed đều là lỗi bảo mật.
- **Ranh giới luật nghiệp vụ là `revoke` + RPC.** Policy chỉ xác thực danh tính người ghi; nội dung ghi hợp lệ hay không là việc của RPC. Bỏ `revoke` = mở lại toàn bộ đường lách (kudo 0 hashtag, tự-tim, tự set bonus +2).
- **Payload Broadcast không đi qua RLS** — mọi thứ nhét vào đó là công khai. Chỉ id, không nội dung.
- Ba hàm `security definer` ở phase này (`is_admin`, `admin_grant_secret_box`, 2 trigger broadcast) đều cố định `search_path`.
- `secret_box_grants` cấm hoàn toàn INSERT/UPDATE từ client — chỉ RPC ở phase-04 được đụng. Đây là điều TC bảo mật của Open Secret Box đòi ("số hộp phải từ server, không thao túng client-side").
- Không cột nào chứa email hay auth identifier lọt vào `profiles`.
- `body` của kudos là rich text → sanitize XSS ở tầng ứng dụng khi render (phase-16), DB chỉ lưu thô.

## Next Steps

- phase-03 bootstrap hàng `profiles` + `user_roles` lúc đăng nhập lần đầu.
- phase-04 thêm `0008_business_rpc.sql` (create_kudos / toggle_heart / open_secret_box).
- Track A không phụ thuộc phase này.

## Runbook — hết Secret Box giữa sự kiện

Rule cấp phát hộp vẫn còn treo (clarifications gap #9), nên hộp **sẽ** hết nếu sự kiện chạy dài. Không có rule tự động, nhưng phải có đường cấp tay — nếu không, tính năng chết giữa chừng mà không ai sửa được.

```sql
-- cấp thêm 2 hộp cho toàn bộ Sunner đang hoạt động (chạy bằng phiên admin)
select admin_grant_secret_box(array(select id from profiles), 2);

-- cấp cho một nhóm cụ thể
select admin_grant_secret_box(array['<uuid-1>','<uuid-2>']::uuid[], 1);

-- kiểm tồn kho trước khi cấp
select status, count(*) from secret_box_grants group by status;
```

Người chạy: bất kỳ ai có `user_roles.role = 'admin'`, qua Studio SQL Editor (`localhost:54323`). Hàm tự chặn người không phải admin. Khi có rule earn thật, thay chỗ này bằng trigger — runbook này là giải pháp cầu, không phải đích đến.

## Rollback

Xoá file migration tương ứng rồi `npx supabase db reset` — DB local dựng lại từ đầu, không có dữ liệu thật để mất. Nếu đã lỡ sinh migration sai, **không sửa file cũ đã chạy trên máy khác**; thêm migration đảo chiều.
