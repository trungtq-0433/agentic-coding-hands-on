# Phase 03 — Auth Google OAuth

**Track:** B · **Priority:** P1 · **Status:** pending · **Effort:** 3h
**Phụ thuộc:** phase-02 **+ PRE-REQ-01 (Google OAuth client)** · **Mở khoá:** phase-04
**KHÔNG có quan hệ blocks/blockedBy với bất kỳ phase Track A nào.**

> ## ⛔ PRE-REQ-01 — chặn phase này, KHÔNG phải việc của agent
> Tạo OAuth client trên Google Cloud Console cần **quyền admin trên tổ chức Google Workspace của Sun\***. Agent không có và không nên có quyền đó. Đây là action-item giao cho người thật, **khởi động từ ngày 0, chạy song song với phase-01/02**, không phải bước 1 nằm trong 3h của phase này.
> - **Đầu ra cần có:** `GOOGLE_CLIENT_ID` + `GOOGLE_SECRET`, với Authorized redirect URI = `http://localhost:54321/auth/v1/callback` (cổng **Supabase**, không phải cổng Next 3000).
> - **Người làm:** người có quyền Google Cloud Console của tổ chức. **Chưa được giao — xem plan.md mục Pre-requisites.**
> - **Chuỗi bị chặn nếu trễ:** phase-03 → 04 → 05 → 16. Tức là gần như toàn bộ Track B từ auth trở đi. Track A **không** bị ảnh hưởng.
> - **Đường đi tiếp khi chờ:** phase-04 vẫn code và test được bằng phiên giả lập trong Studio (`set request.jwt.claims`) — chỉ luồng đăng nhập thật là phải chờ.

## Context Links

- Auth pattern + DAL + hai lớp bảo vệ route: [`reports/researcher-260805-1032-nextjs16-supabase-local.md`](./reports/researcher-260805-1032-nextjs16-supabase-local.md) §4
- Ma trận quyền: [`reports/researcher-260805-1032-momorph-requirements-synthesis.md`](./reports/researcher-260805-1032-momorph-requirements-synthesis.md) §3
- Spec/TC gốc: `research/momorph/csv/spec-login-GzbNeVGJHz.csv`, `tc-login-GzbNeVGJHz.csv`

## Overview

Một nút Google duy nhất, mọi tài khoản Google đều vào được (spec item 2.2.1, tường minh — **không** giới hạn domain `@sun-asterisk.com`). Sau khi có session: bootstrap `profiles` + `user_roles` nếu chưa có, rồi về `/`.

## Key Insights

1. **Không giới hạn domain.** Clarifications ghi rõ "MỌI tài khoản Google đều được phép". Câu hỏi treo #2 của report Next/Supabase (check claim `hd`) **không áp dụng** cho phase này — đừng cài chặn domain.
2. **Redirect sau login là `/`**, không phải `/todo` (placeholder trong spec) — clarifications gap #2.
3. **Bảo vệ route dùng CẢ HAI lớp**, không chọn một: `proxy.ts` là kiểm tra lạc quan cho UX; `verifySession()` trong DAL là kiểm tra thật, gọi sát chỗ dùng dữ liệu. Doc Next.js cảnh báo rõ: đừng chỉ check ở layout vì layout không re-render mỗi lần navigate (Partial Rendering).
4. **`exchangeCodeForSession` phải nằm trong Route Handler**, vì đó là một trong hai chỗ duy nhất Next 16 cho phép ghi cookie.
5. **Bootstrap profile bằng DB trigger, không bằng code app.** Trigger `on auth.users AFTER INSERT` chèn `profiles` + `user_roles` mặc định — chạy đúng một lần, nguyên tử, không phụ thuộc đường vào. Code app chỉ *đồng bộ lại* `full_name`/`avatar_url` từ metadata Google mỗi lần đăng nhập (Google có thể đổi ảnh).
6. Người đã đăng nhập mở `/login` phải bị đá về `/` (TC f62b0c97).

## Requirements

### Chức năng
- `signInWithGoogle()` từ Client Component → `signInWithOAuth({ provider: 'google', options: { redirectTo: <origin>/auth/callback } })`.
- `GET /auth/callback` → `exchangeCodeForSession(code)` → đồng bộ profile → `redirect('/')`. Lỗi → `/login?error=oauth`.
- `signOut()` Server Action → `supabase.auth.signOut()` → `redirect('/')`, không có dialog xác nhận (spec dropdown-profile-admin).
- Route guard: `/profile`, `/admin` yêu cầu session. `/admin` yêu cầu thêm role `admin`.
- `getCurrentUser()` / `getCurrentProfile()` / `isCurrentUserAdmin()` cho tầng trên dùng lại.

### Phi chức năng
- `verifySession()` bọc `React.cache()` để một request chỉ hỏi Supabase một lần.
- DTO chỉ trả các cột được phép hiển thị — không bao giờ trả email hay `auth.users.id` ra client ngoài chính chủ.

## Architecture

### Luồng đăng nhập

```
/login  (Client Component nút Google — UI do Track A phase-07 dựng)
   │ onGoogleLogin()  ← callback prop, phase-16 nối vào lib/actions/auth-actions.ts
   ▼
supabase.auth.signInWithOAuth({provider:'google', redirectTo:'/auth/callback'})
   ▼ Google consent
GET /auth/callback?code=...       (app/auth/callback/route.ts)
   ├─ await exchangeCodeForSession(code)      → set cookie session
   ├─ syncProfileFromIdentity(user)           → upsert full_name/avatar_url
   └─ redirect('/')
```

Lần đầu tiên user tồn tại, trigger DB đã tạo sẵn hàng `profiles` + `user_roles(role='user')`; `syncProfileFromIdentity` chỉ UPDATE.

### Ba lớp kiểm soát

| Lớp | File | Việc | Không làm |
|---|---|---|---|
| Proxy | `proxy.ts` + `lib/auth/route-guard.ts` | Đọc user từ session cookie, redirect `/profile`,`/admin` khi thiếu; đá `/login` về `/` khi đã có session | **Không query DB** (chạy cả trên prefetch) |
| DAL | `lib/auth/dal.ts` | `verifySession()` cached, `requireUser()`, `requireAdmin()` — gọi trong page/Server Action | — |
| RLS | phase-02 | Chốt chặn cuối ở DB | — |

`proxy.ts` chỉ thêm **một** import và **một** lời gọi; toàn bộ bảng route nằm trong `lib/auth/route-guard.ts` (`PROTECTED_PREFIXES`, `ADMIN_PREFIXES`, `GUEST_ONLY_PREFIXES`).

## Related Code Files

**Tạo mới**
- `supabase/migrations/0007_auth_bootstrap_trigger.sql` — trigger `handle_new_user()` trên `auth.users`
- `app/auth/callback/route.ts` — Route Handler, `await ctx.params` không cần (không có param), nhưng `cookies()` là async
- `lib/actions/auth-actions.ts` — `'use server'`: `signOutAction()`
- `lib/auth/dal.ts` — `verifySession`, `requireUser`, `requireAdmin`, `getCurrentProfile`, `isCurrentUserAdmin`
- `lib/auth/dto.ts` — `toPublicProfile()` lọc cột
- `lib/auth/route-guard.ts` — bảng route + `evaluateRouteAccess(pathname, user)`
- `lib/auth/sign-in-with-google.ts` — helper client-side gọi `signInWithOAuth`

**Sửa**
- `proxy.ts` (thêm 1 import + 1 lời gọi — phase-01 sở hữu file, phase-03 nhận bàn giao vì hai phase **chain tuần tự**, không song song)
- `supabase/config.toml` — bật `[auth.external.google]` cho stack local, `client_id`/`secret` đọc từ biến env

**Xoá:** không

**File ownership (glob):** `lib/auth/**`, `lib/actions/auth-actions.ts`, `app/auth/**`, `supabase/migrations/0007_*.sql`, và bàn giao `proxy.ts` từ phase-01.

## Implementation Steps

1. **Nhận `GOOGLE_CLIENT_ID`/`GOOGLE_SECRET` từ PRE-REQ-01** (xem đầu file — việc của người có quyền Workspace, không phải của agent). Không có hai giá trị này thì dừng ở đây và báo BLOCKED, đừng dựng provider giả.
2. `supabase/config.toml`: `[auth.external.google] enabled = true`, `client_id = "env(GOOGLE_CLIENT_ID)"`, `secret = "env(GOOGLE_SECRET)"`, `redirect_uri` mặc định. Thêm 2 biến vào `.env.local` + `.env.local.example` (**không** tiền tố `NEXT_PUBLIC_`). `npx supabase stop && start` để nạp lại config.
3. `0007_auth_bootstrap_trigger.sql`: hàm `handle_new_user()` `security definer` **`set search_path = public, pg_temp`** (bắt buộc — hàm này chạy với quyền owner trên `auth.users`, thiếu `search_path` là lỗ chiếm quyền) chèn `profiles(id, full_name, avatar_url)` từ `new.raw_user_meta_data` và `user_roles(user_id,'user')`; trigger `after insert on auth.users`.
4. `lib/auth/sign-in-with-google.ts`: dùng browser client, `redirectTo: ${window.location.origin}/auth/callback`.
5. `app/auth/callback/route.ts`: đọc `code` từ `new URL(request.url).searchParams`; nếu thiếu → redirect `/login?error=oauth`. Gọi `exchangeCodeForSession`, rồi `syncProfileFromIdentity`, rồi `NextResponse.redirect(new URL('/', request.url))`.
6. `lib/auth/dal.ts`: `export const verifySession = cache(async () => { const s = await createClient(); const { data: { user } } = await s.auth.getUser(); return user ?? null })`. `requireUser()` không có user → `redirect('/login')`. `requireAdmin()` không phải admin → `redirect('/')`.
7. `lib/auth/dto.ts`: `toPublicProfile` chỉ giữ `id, full_name, avatar_url, department, received_kudos_count, star_count`. Không bao giờ trả `email`.
8. `lib/auth/route-guard.ts`: `PROTECTED_PREFIXES = ['/profile','/admin']`, `ADMIN_PREFIXES = ['/admin']`, `GUEST_ONLY_PREFIXES = ['/login']`. Hàm thuần, dễ unit test.
9. `proxy.ts`: sau `updateSession`, gọi `evaluateRouteAccess(pathname, user)`; trả `redirect` khi cần.
10. `lib/actions/auth-actions.ts`: `signOutAction` `'use server'` → `signOut()` → `redirect('/')`.
11. Chạy tay: đăng nhập → kiểm `select * from profiles where id = <uid>` có hàng; đăng xuất; mở `/profile` ở tab ẩn danh → bị đá `/login`.

## Todo List

- [ ] **PRE-REQ-01 đã xong** (client id/secret trong tay) — nếu chưa: BLOCKED, không tự dựng thay
- [ ] `supabase/config.toml` bật provider google, env `GOOGLE_CLIENT_ID` / `GOOGLE_SECRET`
- [ ] Migration `0007` trigger `handle_new_user` **có `set search_path = public, pg_temp`**
- [ ] `lib/auth/sign-in-with-google.ts`
- [ ] `app/auth/callback/route.ts` + xử lý lỗi
- [ ] `lib/auth/dal.ts` (`React.cache`) + `dto.ts`
- [ ] `lib/auth/route-guard.ts` + nối vào `proxy.ts`
- [ ] `signOutAction`
- [ ] Kiểm tay 4 kịch bản: login, logout, guest vào `/profile`, user thường vào `/admin`

## Success Criteria

- Bấm nút Google → về `/` với session, không phải `/todo`.
- Đăng nhập lần đầu: bảng `profiles` và `user_roles` mỗi bảng thêm đúng **một** hàng; đăng nhập lần hai: **không** thêm hàng nào.
- Guest mở `/profile` → 302 `/login`. Sau khi login mở lại → thấy trang.
- User đã login mở `/login` → 302 `/`.
- User role `user` mở `/admin` → 302 `/`; đổi `user_roles.role` thành `admin` trong Studio rồi F5 → **vào được ngay**, không cần đăng xuất (bằng chứng cho lựa chọn bảng `user_roles` thay vì JWT claim).
- Đăng nhập bằng tài khoản Gmail **ngoài** `@sun-asterisk.com` → thành công (đúng spec).
- `grep -rn "email" lib/auth/dto.ts` không khớp.
- `select proconfig from pg_proc where proname = 'handle_new_user'` → chứa `search_path=public, pg_temp`.
- Đăng nhập thật xong, avatar Google hiển thị được (bằng chứng `images.remotePatterns` ở phase-01 đã đúng).

## Risk Assessment

| Rủi ro | K/năng × T/động | Giảm thiểu |
|---|---|---|
| **PRE-REQ-01 trễ vì chờ quyền tổ chức** → chặn 03→04→05→16 | **Cao** × Cao | Khởi động từ ngày 0 song song phase-01/02; phase-04 vẫn code/test được bằng phiên giả lập trong khi chờ |
| Nhầm redirect URI sang cổng Next (3000) thay vì Supabase (54321) | Cao × TB | Ghi trong PRE-REQ-01; lỗi hiện ngay ở màn Google, dễ nhận ra |
| `handle_new_user()` thiếu `search_path` | TB × Cao | Bước 3 + case `pg_proc` trong Success Criteria |
| Tự ý thêm chặn domain `@sun-asterisk.com` theo thói quen | TB × Cao | Success criteria có case Gmail ngoài domain **phải** thành công |
| Chèn code giữa `createServerClient` và `getUser()` trong proxy → session treo | TB × Cao | Đã cô lập trong `proxy-session.ts` từ phase-01; code review kiểm hai dòng liền nhau |
| Bootstrap profile bằng code app → race khi mở 2 tab cùng lúc | TB × TB | Đẩy về trigger DB (nguyên tử), app chỉ UPDATE |
| Chỉ check auth ở layout → Partial Rendering bỏ lọt | TB × Cao | `requireUser()` gọi trong page, không trong layout; ghi thành quy ước |
| Secret Google lọt vào git | Thấp × Rất cao | Chỉ ở `.env.local` (đã gitignore); `.env.local.example` để trống giá trị |

## Security Considerations

- `GOOGLE_SECRET` **không** có tiền tố `NEXT_PUBLIC_`.
- `proxy.ts` không phải hàng rào an ninh — mọi page/action nhạy cảm vẫn phải tự gọi `requireUser()`/`requireAdmin()`.
- DTO là ranh giới chống rò dữ liệu: TC_WEB_PROFILE_SEC_004 cấm lộ email/auth identifier trên màn Profile.
- Đăng xuất phải làm mất hiệu lực cookie phía server (`signOut()`), không chỉ xoá state client.

## Next Steps

- phase-04 dùng `requireUser()` trong mọi Server Action ghi dữ liệu.
- phase-16 nối `onGoogleLogin` / `onSignOut` vào UI Track A.
- Màn `/admin` thật vẫn để ngỏ (clarifications gap #3) — phase-16 chỉ dựng placeholder có role guard.

## Rollback

Revert commit + `npx supabase db reset` (bỏ migration 0007). Người dùng local mất session, không có hệ quả lan.
