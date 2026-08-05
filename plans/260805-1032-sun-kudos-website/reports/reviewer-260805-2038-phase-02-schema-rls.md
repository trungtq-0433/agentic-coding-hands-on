# Review — Phase-02 Sun* Kudos: schema/RLS/view/trigger/seed

**Phạm vi:** `supabase/migrations/0001-0006*.sql`, `supabase/seed.sql`, `scripts/count-departments.mjs` (mới); `lib/supabase/database.types.ts` (sinh tự động, chỉ xét commit hay không).
**Đối chiếu:** `phase-02-schema-migrations-rls.md`, `clarifications.md`.
**Phương pháp:** đọc toàn bộ 7 migration + seed + script; chạy `npx supabase db reset`; verify trực tiếp bằng `psql` (role-switch `set local role` + `request.jwt.claims`) trên DB local đã seed.

## Tóm tắt

Kiến trúc revoke+RPC+view đúng như plan, `db reset` xanh, TRUNCATE/INSERT/DELETE trực tiếp đều bị chặn (verify lại bằng psql, xem dưới). Nhưng có **1 lỗ rò ẩn danh Critical mới**, khác với lỗ TRUNCATE đã vá: cột `profiles.sent_kudos_count` được `grant select` công khai cho `anon`/`authenticated`, và bộ đếm này **cộng cả kudos ẩn danh**. Ghép với `public_kudos_feed` (công khai), bất kỳ ai cũng tính được chính xác **có bao nhiêu** kudos ẩn danh mỗi người đã gửi — đã chứng minh bằng số trên seed data, khớp 100% ground truth. Đây đúng là câu hỏi nghi vấn #1 của yêu cầu review, và tài liệu research của chính phase này (`researcher-...-momorph-requirements-synthesis.md`) đã cảnh báo trước lý do ẩn tab "Đã gửi" trên profile người khác — nhưng bản SQL không thực thi được ý đó ở tầng DB.

## Critical

| # | File:line | Vấn đề | Kịch bản khai thác (đã verify bằng psql) | Cách sửa |
|---|---|---|---|---|
| C1 | `supabase/migrations/0006_views_and_rls.sql:93` (`grant select on profiles to anon, authenticated;`) + `supabase/migrations/0005_triggers_and_indexes.sql:15-18` (`trg_kudos_counters_fn` cộng `sent_kudos_count` cho **mọi** kudos, không loại trừ `is_anonymous`) | **Đếm kudos ẩn danh bị lộ qua cột public `profiles.sent_kudos_count`** — phá vỡ đúng bất biến "che ẩn danh nằm ở DB" mà Key Insight #1 của phase này đặt ra. RLS chặn theo hàng không theo cột (plan tự nói câu này ở dòng 17), nên `profiles_select_all using (true)` + `grant select` không cột nào bị loại = mọi cột kể cả `sent_kudos_count` đều public. | Đã chạy trên DB đã seed (role `anon`/`authenticated` qua `profiles`+`public_kudos_feed`, không cần quyền gì đặc biệt): `inferred_anon_sent = profiles.sent_kudos_count - count(public_kudos_feed where sender_id = profile.id)`. Kết quả khớp **chính xác 100%** với số kudos ẩn danh thật của từng sender (ground truth truy vấn trực tiếp bảng `kudos` bằng quyền superuser): profile `...002`→1, `...004`→1, `...006`→2, `...008`→1, còn lại→0. 3/4 người có đúng 1 kudos ẩn danh — nghĩa là chỉ cần biết nghi phạm, đối chiếu `sent_kudos_count` là **xác nhận/phủ nhận 100%** họ có gửi ẩn danh không, và trong nhiều trường hợp (khi chỉ 1 người trong tập ứng viên có `inferred_anon_sent>0`) suy ra được **chính xác kudos nào** do ai gửi. Đây không phải lý thuyết — đã đo bằng SQL, không cần khai thác thêm gì. | 1) Không tính kudos ẩn danh vào `sent_kudos_count` khi trigger cộng — **không đủ**, vì `my_sent_kudos` (tab "Đã gửi" của chính chủ) vẫn cần biết tổng thật bao gồm ẩn danh để hiển thị đúng cho self. 2) **Cách đúng**: giữ trigger như hiện tại (đếm đúng tổng thật), nhưng **không` grant select` cột `sent_kudos_count` công khai** — dùng column-level grant Postgres: `revoke select on profiles from anon, authenticated; grant select (id, full_name, avatar_url, department_id, received_kudos_count, received_hearts_count, created_at) on profiles to anon, authenticated;` (loại `sent_kudos_count`), rồi lộ `sent_kudos_count` **chỉ cho chính chủ** — thêm cột đó vào `my_sent_kudos`/1 view riêng `my_profile_stats` với `where id = auth.uid()`, đúng pattern đã dùng cho `secret_box_grants_select_own`. |

Bằng chứng đo được (đã chạy, không phải suy diễn):

```
profile_id       | counter_total | visible_nonanon_sent(feed) | inferred_anon_sent | ground_truth_anon_sent
...002           | 4             | 3                          | 1                   | 1
...004           | 4             | 3                          | 1                   | 1
...006           | 4             | 2                          | 2                   | 2
...008           | 3             | 2                          | 1                   | 1
...001,003,005,007 | -           | -                          | 0                   | 0
```
`grantee=anon/authenticated, column_name=sent_kudos_count, privilege_type=SELECT` xác nhận trong `information_schema.column_privileges` — không có giới hạn cột nào đang tồn tại.

**Vì sao đây là Critical chứ không phải Warning:** chính báo cáo research của phase này (`reports/researcher-260805-1032-momorph-requirements-synthesis.md` dòng 16) đã ghi rõ: "*Dropdown hướng Kudos: self có 'Đã nhận/Đã gửi', người khác chỉ có 'Đã nhận' (**ẩn để không lộ số kudo ẩn danh đã gửi**)*" và `phase-11-ui-profile-ban-than.md:28` lặp lại "Profile người khác: không có tab 'Đã gửi', không có thẻ 5 chỉ số". Ý định sản phẩm đã tường minh: che số liệu này ở tầng UI cho profile người khác. Nhưng plan cũng tự khẳng định (Key Insight #1, Security Considerations): ranh giới thật phải nằm ở DB — ẩn tab trên UI không ngăn ai đó gọi thẳng PostgREST `GET /profiles?select=id,sent_kudos_count`. Migration hiện tại chưa thực thi được đúng ý định đó.

## Warning

| # | File:line | Vấn đề | Đề xuất |
|---|---|---|---|
| W1 | `supabase/seed.sql` (289 dòng) | Vượt quy ước "mỗi file ≤ 200 dòng" (`development-rules.md`, và chính phase-02 áp cho migration). Không sai chức năng, nhưng khó review/maintain khi cần sửa dữ liệu demo về sau. | Tách theo khối đã có sẵn comment (`-- === 1) ... ===`): ví dụ `seed.sql` (master data + users + profiles) + `seed_kudos_demo.sql` (kudos/hashtags/images/hearts/secret_box). Supabase CLI chạy 1 file `seed.sql` mặc định — nếu tách cần `\i` include hoặc gộp lại qua script, cân nhắc chi phí trước khi làm; nếu không đáng, ghi nhận ngoại lệ có chủ đích trong comment đầu file thay vì im lặng vượt giới hạn. |
| W2 | `supabase/migrations/00061_realtime_broadcast_triggers.sql` vs `phase-02-schema-migrations-rls.md:121,158` (liệt kê file là `0006b_realtime_broadcast_triggers.sql`) | File thật tên khác tên trong "Related Code Files"/Todo List của plan (đổi vì CLI Supabase từ chối `0006b`, đã giải thích rõ trong comment đầu file — hợp lý). Nhưng plan doc chưa cập nhật theo, người đọc sau tra theo plan sẽ tìm nhầm tên file. | Sửa `phase-02-schema-migrations-rls.md` 2 chỗ nêu trên thành `00061_realtime_broadcast_triggers.sql` để khớp thực tế (việc của agent triển khai, không phải reviewer, nhưng nêu ở đây vì ảnh hưởng truy vết). |

## Suggestion

| # | File:line | Ghi chú |
|---|---|---|
| S1 | `supabase/migrations/0006_views_and_rls.sql:38-53` (`my_sent_kudos`) | Không có cột `sender_id` — đã kiểm tra `phase-11`/`phase-16`: không nơi nào cần cột này (view đã filter `where sender_id = auth.uid()`, client vốn đã biết đó là chính mình). Kết luận: **cố ý, không phải bỏ sót**, không cần sửa. |
| S2 | `supabase/seed.sql:118-132` | `auth.users` seed không có dòng `auth.identities` tương ứng. Cột NOT NULL của `auth.users` (`id`, `is_sso_user`, `is_anonymous`) đều được set đủ nên không vỡ `db reset`/GoTrue ở mức schema. Vì domain email seed là `@sunkudos.demo` (không thật), không đụng OAuth thật ở phase-03. Không chặn, nhưng nếu sau này có script re-seed dùng `auth.admin.createUser` thật (đường dự phòng plan có nêu ở Risk Assessment) thì nhớ thêm `identities` để nhất quán. |
| S3 | `supabase/seed.sql:70-73` (update parent_id) | Có 2 phòng ban cấp 2 không có `parent_id`: `OPDC - HRF`, `OPDC - HRD` — vì nguồn CSV không có dòng gốc `OPDC` đứng riêng (đã đối chiếu bằng `scripts/count-departments.mjs`, không phải lỗi UPDATE). Hành vi nhất quán với cách xử lý `PAO - PAO` đã làm (không tự ý bịa dữ liệu tổ chức). Đề xuất: thêm 1 dòng comment ngắn cạnh khối UPDATE ghi nhận 2 trường hợp gốc thiếu cha này, để người đọc sau không tưởng là bug — giống cách đã làm với `PAO-PAO`. |

## Đã verify (không lặp phần user đã tự kiểm)

Bằng psql trên DB đã `db reset` + seed:

- 0 bảng thiếu RLS (`pg_class.relrowsecurity`), 12 bảng đúng, `kudos_mentions` không tồn tại.
- 7 hàm `security definer` (`is_admin`, `admin_grant_secret_box`, 3 trigger counter, 2 trigger broadcast) đều có `proconfig = {"search_path=public, pg_temp"}`.
- `departments` = 50, 0 trùng `code`; `badges` = 6, tổng `probability_weight` = 100; `hashtags` = 13.
- Ghi trực tiếp bị chặn thật (không chỉ đọc code): `truncate hearts`, `insert kudos`, `insert hearts (is_special_day_bonus=true)`, `delete hearts` — cả 4 đều `ERROR: permission denied` với role `authenticated` giả lập qua `set local request.jwt.claims`.
- `admin_grant_secret_box()`: user thường → `FORBIDDEN`; admin thật (`user_roles.role='admin'`) → chạy thành công, không lỗi.
- `auth.uid()` khi không có JWT (`request.jwt.claims` rỗng) → `NULL`; `my_sent_kudos` trả **0 dòng**, không lỗi, không lộ (vì `sender_id = NULL` luôn `false` trong SQL 3-valued logic) — đúng như thiết kế, không có lỗ ở đây.
- `pg_proc`/`information_schema.column_privileges` xác nhận không có giới hạn cột nào khác ngoài cái bị bỏ sót ở C1.
- `profiles.sent_kudos_count`/`received_kudos_count` khớp chính xác `count(*)` thật từ bảng `kudos` cho cả 8 profile demo — trigger counter tính đúng, không lệch.

## Đối chiếu Success Criteria (phase-02.md)

Tất cả các mục liệt kê đều đạt, **trừ** hàm ý ẩn danh bị phá vỡ gián tiếp qua C1 (Success Criteria có ghi rõ `select sender_id, sender_full_name from public_kudos_feed where is_anonymous = true` → toàn NULL — mục này **vẫn đúng theo nghĩa đen**, nhưng không đủ để bảo vệ ẩn danh trong thực tế vì đường vòng qua `profiles.sent_kudos_count` không nằm trong danh sách kiểm — đây là khoảng trống của chính bộ tiêu chí, nên khuyến nghị bổ sung 1 success criterion mới: "không cột public nào phân biệt được số kudos ẩn danh đã gửi của 1 user".

## Hành động theo thứ tự

1. **[Chặn merge]** Vá C1: column-level grant loại `sent_kudos_count` khỏi `profiles` public read; thêm đường đọc self-only cho cột này (view/RPC riêng, pattern giống `secret_box_grants_select_own`). Sau khi vá, chạy lại đúng phép đo ở trên (`inferred_anon_sent`) để xác nhận không còn tính được nữa (client anon/authenticated không còn truy cập cột này).
2. W2: sửa tên file trong `phase-02-schema-migrations-rls.md` cho khớp `00061_...`.
3. W1/S1/S2/S3: tuỳ chọn, không chặn merge.

## Số liệu

- Migration: 7 file, 610 dòng (không tính seed) — trong giới hạn 200 dòng/file.
- `seed.sql`: 289 dòng — vượt giới hạn 200 (W1).
- `npx supabase db reset`: exit 0.
- Tables thiếu RLS: 0/12.
- Hàm definer thiếu `search_path`: 0/7.
- Lint/tsc: không thuộc phạm vi review này (chỉ SQL); `database.types.ts` không review nội dung theo yêu cầu.

## Còn treo

- Không có mục nào cần hỏi thêm user — C1 có fix cụ thể, đủ để implementer tự làm không cần quyết định kiến trúc mới (đã có pattern `secret_box_grants_select_own` làm mẫu).
