# Review Phase-03 — Auth Google OAuth (trước commit)

**Phạm vi:** `supabase/migrations/0007_auth_bootstrap_trigger.sql`, `lib/auth/{dal,dto,route-guard,sign-in-with-google}.ts`,
`lib/actions/auth-actions.ts`, `app/auth/callback/route.ts`, `proxy.ts` (bàn giao), `supabase/config.toml`,
`supabase/seed.sql`, `lib/supabase/database.types.ts` (generated, không review nội dung).
465 dòng code mới/sửa. Đối chiếu `phase-03-auth-google-oauth.md` + `clarifications.md`.

## Đánh giá chung

Thiết kế bám sát mẫu chính thức Next 16 (`node_modules/next/dist/docs/01-app/02-guides/authentication.md`):
DAL + `React.cache()` + DTO + 2-lớp Proxy/DAL đúng khuôn — đối chiếu từng đoạn code với ví dụ trong doc thì khớp
gần như nguyên văn (kể cả pattern `verifySession` gọi được trong Route Handler, dòng 1505-1526 của doc). PKCE
flow được `@supabase/ssr` 0.12.4 hard-code (`createBrowserClient.js:40`, `createServerClient.js:33`:
`flowType: "pkce"`), nên câu hỏi "login-CSRF qua code đánh cắp" tự triệt tiêu — code_verifier cookie của nạn
nhân sẽ không khớp code của kẻ tấn công. Toàn bộ 9 điều đã verify trong yêu cầu đều đúng khi tôi dò lại bằng
`psql`/đọc code. Tìm thêm được **1 lỗi cấu hình sẽ chặn đứng luồng login thật** (mục Warning #1) — chưa lộ ra vì
PRE-REQ-01 (Google Cloud credentials) chưa có, các bước đã verify đều dùng phiên giả lập, không phải OAuth thật.

## Critical

Không có.

## Warning

| # | File:dòng | Vấn đề | Chứng minh | Cách sửa |
|---|---|---|---|---|
| 1 | `supabase/config.toml:344-349` | `redirect_uri` bỏ trống → GoTrue tự suy từ `api_url = "http://127.0.0.1"` (dòng 99) ra `http://127.0.0.1:54321/auth/v1/callback`. Nhưng PRE-REQ-01 (`phase-03-auth-google-oauth.md:9`, `.env.local.example`, `plan.md:58`) lại chỉ định đăng ký trên Google Cloud Console là `http://localhost:54321/auth/v1/callback`. Google so khớp `redirect_uri` theo **chuỗi tuyệt đối** — `127.0.0.1` ≠ `localhost` — nên khi PRE-REQ-01 xong và người dùng bấm nút Google thật, Google sẽ trả lỗi `redirect_uri_mismatch` ngay màn consent, chặn đứng toàn bộ luồng login thật (chặn Success Criteria mục 1 và bước kiểm tay #11 của phase). | Đã chạy thật trên Supabase local đang sống: `curl -sD - -o /dev/null "http://127.0.0.1:54321/auth/v1/authorize?provider=google"` → header `Location` chứa `redirect_uri=http%3A%2F%2F127.0.0.1%3A54321%2Fauth%2Fv1%2Fcallback` — xác nhận GoTrue thật sự gửi `127.0.0.1`, không phải `localhost` như tài liệu PRE-REQ-01 yêu cầu đăng ký. | Set tường minh `redirect_uri = "http://localhost:54321/auth/v1/callback"` trong khối `[auth.external.google]` (ghi đè suy diễn từ `api_url`), thay vì để trống. Không cần đổi `api_url`/`site_url` toàn cục (tránh ảnh hưởng dây chuyền các provider khác). |

## Suggestion

| # | File:dòng | Vấn đề | Đề xuất |
|---|---|---|---|
| 1 | `.env.local.example` (không nằm trong diff, đã commit ở `0f34f7a`) | Vẫn còn khối `GOOGLE_CLIENT_ID`/`GOOGLE_SECRET` — hai biến này **không được đọc bởi bất kỳ code nào** trong diff này (đã `grep` toàn repo, chỉ còn xuất hiện trong `plans/` và chính file example). Luồng thật dùng `SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID`/`SECRET` trong `.env` (đúng, đã kiểm trong `supabase/config.toml`). Đây là tàn dư từ trước khi có quyết định "Credential Google OAuth — chỗ đặt" trong `clarifications.md` (bổ sung sau Red Team, sau khi `.env.local.example` đã commit). Người thực hiện PRE-REQ-01 đọc theo `.env.local.example` sẽ điền nhầm biến, tưởng đã xong nhưng CLI Supabase không thấy giá trị (biến `env(...)` trong config.toml không resolve được, provider coi như chưa cấu hình đúng thay vì lỗi rõ ràng). | Xoá khối `GOOGLE_CLIENT_ID`/`GOOGLE_SECRET` khỏi `.env.local.example`, chỉ giữ trong `.env.example` (đã đúng). Không thuộc file ownership của phase-03 nên chỉ nêu ra, không tự sửa. |
| 2 | `app/auth/callback/route.ts` (toàn hàm `GET`) | Không có try/catch bao ngoài. Lỗi được xử lý cho nhánh `exchangeCodeForSession` và `sync_profile_from_google` (RPC trả `{error}` — không throw), nhưng nếu có exception đồng bộ bất ngờ khác (ví dụ cookie hỏng, thư viện `@supabase/ssr` throw) thì Next 16 sẽ trả trang lỗi 500 mặc định thay vì `/login?error=oauth` như ý đồ UX. Không phải lỗ hổng bảo mật (không rò dữ liệu, không phải "nuốt lỗi") — chỉ là propagate ngoài ý muốn. | Cân nhắc bọc thân hàm bằng try/catch, log rồi vẫn redirect `/login?error=oauth`, để giữ đúng UX "lỗi → về `/login?error=oauth`" ở mọi loại lỗi, không chỉ hai loại đã lường trước. |

## Đối chiếu 9 mục yêu cầu soi kỹ

| # | Mục | Kết quả |
|---|---|---|
| 1 | `app/auth/callback/route.ts` | `code` thiếu → redirect tĩnh, không có tham số `next`/`redirectTo` nào nhận từ query nên **không có open-redirect surface** (đích luôn là hằng số `/` hoặc `/login?error=oauth`). Lỗi `exchangeCodeForSession` chỉ log server-side (`console.error`), URL redirect không mang message. Đã login gọi lại callback không có case riêng nhưng không nguy hiểm (xem Suggestion #2). |
| 2 | `lib/auth/dal.ts` | `verifySession` dùng đúng khuôn official doc dòng 1143-1152 — `cache()` của React dedupe theo **render pass/request**, Next.js reset theo request (AsyncLocalStorage nội bộ); không có leak giữa các request vì đây chính là pattern được doc khuyến nghị dùng cả trong Route Handler (doc dòng 1505-1526). `requireAdmin()` dùng `createClient()` (server client có cookie) đúng ngữ cảnh. Không N+1 — `requireAdmin` = 1 lệnh `getUser` (đã cache) + 1 query `user_roles`. |
| 3 | `lib/auth/dto.ts` | Cột trả về khớp chính xác grant list ở `0006_views_and_rls.sql:104-106` (`id, full_name, avatar_url, department_id, received_kudos_count, received_hearts_count, created_at`) — không gọi `sent_kudos_count`, không lỗi 42501. Ngưỡng sao: `>=50→3, >=20→2, >=10→1`, kiểm biên bằng tay: 9→0, 10→1, 20→2, 49→2, 50→3, 51→3 — đúng. |
| 4 | `lib/auth/route-guard.ts` | `matchesPrefix` dùng `pathname === prefix \|\| startsWith(prefix + '/')` — `/profile` không khớp `/profiles-of-someone` (không có dấu `/` sau). Route nhạy cảm: `/profile`, `/admin` có trong `PROTECTED_PREFIXES`; không thấy route nào khác cần bảo vệ ở phase này (Track A chưa dựng). |
| 5 | `supabase/config.toml` | Không có giá trị literal — cả `client_id` và `secret` đều `env(SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID/SECRET)`, đúng tên biến có trong `.env` (đã kiểm `grep -o '^[A-Z_]*=' .env`). **Nhưng xem Warning #1** — `redirect_uri` để trống gây lệch host. |
| 6 | `supabase/seed.sql` | `on conflict do update` không mất dữ liệu: trigger insert trước (từ `raw_user_meta_data`, `avatar_url=NULL` vì seed đặt metadata `avatar_url:null`), seed update sau ghi đè bằng dicebear URL + `department_id` — đúng thứ tự thắng-thua mong muốn (seed thắng, vì đó là dữ liệu demo xác định). Đã chạy thật: `select count(*) from profiles` = 8, khớp 8 `auth.users`, không rollback. |
| 7 | `signOutAction` | Có `redirect('/')` sau `signOut()` (kể cả khi lỗi). CSRF: Next 16 tự chặn theo Origin/Host header cho Server Action (`node_modules/next/dist/docs/01-app/02-guides/data-security.md:546-552`, `server-actions.md:82`) — không cần thêm gì. |
| 8 | `sign-in-with-google.ts` | `redirectTo` dựng từ `window.location.origin` — giá trị này do trình duyệt tự set theo domain thật đang mở, không phải tham số đọc từ URL nên **không bị user thao túng qua link độc hại**. Rủi ro thật chỉ nằm ở việc origin đó có nằm trong `site_url`/`additional_redirect_urls` của Supabase hay không (đã cấu hình sẵn từ phase-01, không đổi ở diff này). |
| 9 | File ownership | `git status` xác nhận đúng: sửa `lib/supabase/database.types.ts` (generated), `proxy.ts` (bàn giao, đúng +1 import +1 lời gọi), `supabase/config.toml`, `supabase/seed.sql`; tạo mới đúng 4 nhóm `app/auth/**`, `lib/actions/auth-actions.ts`, `lib/auth/**`, `supabase/migrations/0007_*.sql`. Không có file ngoài phạm vi. |
| 10 | Ràng buộc repo | Mọi file ≤ 200 dòng (lớn nhất: `dal.ts` 89 dòng). Tên kebab-case đúng. Không thấy vi phạm YAGNI/KISS/DRY — không có state trùng lặp, RPC `sync_profile_from_google` gọn, không multiplex logic thừa. |

## Đã làm tốt

- Tách bootstrap (trigger DB, atomic) khỏi sync (RPC, theo request) đúng khuyến nghị Risk Assessment của plan — không có race 2-tab.
- `security definer` + `set search_path = public, pg_temp` áp dụng đủ cả 2 hàm mới, đã xác minh bằng `pg_proc.proconfig`.
- `sync_profile_from_google` khoá theo `auth.uid()` ngay trong câu UPDATE, không nhận `id` từ client — đúng nguyên tắc "policy chỉ xác thực ai ghi, RPC xác thực ghi cái gì" từ Red Team review phase-02.
- DTO/grant column list khớp nhau tuyệt đối giữa 3 lớp (SQL grant, TS Pick type, hàm map) — không có cột thừa/thiếu.
- Không có domain lock-in dù đây là lỗi "theo thói quen" phổ biến nhất mà Risk Assessment lo ngại.

## Hành động theo thứ tự

1. Set `redirect_uri = "http://localhost:54321/auth/v1/callback"` tường minh trong `[auth.external.google]` (Warning #1) — nếu không sửa, PRE-REQ-01 xong vẫn không login được, phải debug lại từ đầu.
2. Dọn `GOOGLE_CLIENT_ID`/`GOOGLE_SECRET` khỏi `.env.local.example` (Suggestion #1) — việc nhỏ, không chặn merge.
3. Cân nhắc try/catch bao `GET` trong `app/auth/callback/route.ts` (Suggestion #2) — không bắt buộc.

## Số liệu

- Lint: 0 lỗi trên các file review (`npx eslint` chạy lại, sạch).
- `any`: 0 lần dùng.
- File lớn nhất: 89 dòng (`dal.ts`), trong hạn 200.
- Critical: 0 · Warning: 1 · Suggestion: 2.

## Còn treo

- Warning #1 cần sửa trước hoặc ngay sau khi PRE-REQ-01 hoàn tất (không chặn commit code hiện tại, vì credentials thật chưa tồn tại để test — nhưng sẽ chặn ngay lần thử đăng nhập thật đầu tiên).
- Không kiểm tra được luồng đăng nhập Google thật đầu-cuối (thiếu PRE-REQ-01) — mọi khẳng định về OAuth exchange dựa trên đọc code + hành vi PKCE của thư viện, không phải test end-to-end thật.

**Status:** DONE_WITH_CONCERNS
**Summary:** Kiến trúc auth đúng khuôn Next 16 chính thức, RLS/DTO/route-guard đều khớp, không có lỗ hổng Critical. Tìm ra 1 Warning cụ thể (đã chứng minh bằng curl trên Supabase local đang chạy): `redirect_uri` suy diễn ra `127.0.0.1` trong khi PRE-REQ-01 lại đăng ký `localhost` trên Google Cloud Console — sẽ chặn đứng lần đăng nhập Google thật đầu tiên bằng lỗi `redirect_uri_mismatch`. Sửa 1 dòng trong `supabase/config.toml` trước khi PRE-REQ-01 bàn giao credentials.
**Concerns/Blockers:** Warning #1 nên vá trước khi coi phase-03 là "sẵn sàng nhận credential thật" — không chặn việc commit code hiện tại vì hành vi mọi thứ khác đã đúng và có thể sửa độc lập bằng 1 dòng config.
