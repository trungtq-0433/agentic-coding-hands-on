# Research: Supabase Local + Next.js 16.3.0 App Router / React 19.2.8 / Tailwind v4

Ngày: 2026-08-05. Nguồn Next.js: đọc trực tiếp `node_modules/next/dist/docs/` (next@16.3.0 thực tế trong repo — không suy từ training data). Nguồn Supabase: WebSearch + WebFetch vào docs chính thức supabase.com/docs.

## 1. Next 16 App Router — cái gì đổi so với 14/15 (ảnh hưởng plan này)

| Đề mục | Next 14/15 (quen thuộc) | Next 16.3.0 (thực tế trong repo) | Nguồn (path đã đọc) |
|---|---|---|---|
| **Middleware** | `middleware.ts` ở root | **Đổi tên thành Proxy**: file `proxy.ts` ở root, export `proxy` (hoặc default export) thay vì `middleware`. `middleware.ts` vẫn chạy nhưng **deprecated**, có codemod `npx @next/codemod@canary middleware-to-proxy .` | `01-app/03-api-reference/03-file-conventions/proxy.md` (dòng 15), `middleware.md` (dòng 3, 11-19) |
| **`params`/`searchParams`** | object đồng bộ | **Promise bắt buộc** `await params` / `await searchParams`. Next 15 còn cho phép sync tạm (deprecated), Next 16 nên coi là Promise-only. Có `PageProps<'/route'>` / `LayoutProps<'/route'>` helper type sinh tự động lúc `next dev/build/typegen`. | `03-file-conventions/page.md` (dòng 13-14, 40, 65, 240), `layout.md` (dòng 70, 89, 730) |
| **`cookies()`/`headers()`** | sync ở v14, deprecated-sync ở v15 | **Async bắt buộc**: `const cookieStore = await cookies()`. Set/delete cookie chỉ được phép trong Server Function (Server Action) hoặc Route Handler — **không set được trong Server Component render**. | `04-functions/cookies.md` (dòng 67-70, 81, 297-303) |
| **Server Actions / mutating data** | tương tự | Đổi thuật ngữ: **Server Function** là khái niệm rộng, **Server Action** là Server Function dùng cho `<form action>`/`formAction`. `refresh()` mới (từ `next/cache`) để refresh UI không revalidate tag. `updateTag` (Server Action only, expire ngay) vs `revalidateTag` (SWR, dùng được cả Route Handler). | `01-getting-started/07-mutating-data.md` (dòng 14-34, 383-421), `09-revalidating.md` (dòng 119-163) |
| **Caching mặc định** | `fetch` cache mặc định tuỳ version (13 cache, 14/15 no-store) | Repo hiện **không bật `cacheComponents`** (next.config.ts trống) → dùng model cũ: `fetch` **mặc định KHÔNG cache** (`{cache:'no-store'}` ngầm định), phải set `force-cache` để cache. Nếu bật `cacheComponents:true` thì chuyển hẳn sang model mới `"use cache"` + Partial Prerendering — **KHÔNG bật cho scope này** (thêm phức tạp không cần, YAGNI). | `02-guides/caching-without-cache-components.md` (dòng 11, 96-104), `01-getting-started/08-caching.md` (dòng 14, 20-30) |
| **Route Handlers (`route.ts`)** | tương tự | Không cache mặc định (trừ `GET` + `dynamic='force-static'`). Ctx params cũng là Promise: `ctx.params` → `await ctx.params`. Type `RouteContext<'/path'>` global. | `01-getting-started/15-route-handlers.md` (dòng 51-66, 191-198) |
| **Streaming/Suspense/`loading.js`** | tương tự về khái niệm | Không đổi cơ chế cơ bản: `loading.js` bọc Suspense tự động quanh `page.js`; dùng `<Suspense>` cho phần nhỏ hơn. Với model cũ (không bật Cache Components), layout đọc `cookies()`/uncached fetch sẽ **block cả navigation** thay vì stream — nên đẩy các data access xuống càng sâu càng tốt (page thay vì layout). | `01-getting-started/06-fetching-data.md` (dòng 122-172), `03-file-conventions/layout.md` (dòng 316-323) |
| **Server/Client Component boundary** | không đổi | Giữ nguyên `"use client"` semantics. `React.cache()` để dedupe fetch trong 1 request — dùng cho DAL pattern auth. | `01-getting-started/05-server-and-client-components.md`, `06-fetching-data.md` (dòng 544-588) |

**Điểm dễ dùng nhầm nhất với dev quen Next 14**: viết `middleware.ts` (vẫn chạy nhưng deprecated, nên đổi ngay sang `proxy.ts`), và destructure `params`/`searchParams` như object thường thay vì `await`.

## 2. Supabase local development workflow

Quy trình chuẩn (không link hosted project):

```
npx supabase init      # tạo supabase/config.toml
npx supabase start     # kéo Docker images, chạy full stack local
npx supabase migration new <name>   # tạo file SQL rỗng để viết tay
# hoặc
npx supabase db diff -f <name>      # diff schema đang có trong DB local → sinh migration
npx supabase db reset               # xoá sạch DB local, replay toàn bộ migrations/, rồi chạy seed.sql
npx supabase gen types typescript --local > lib/supabase/database.types.ts
```

Cấu trúc `supabase/` sinh ra: `config.toml` (commit được), `migrations/*.sql` (timestamp-prefixed, chạy tuần tự), `seed.sql` (chạy sau migrations mỗi lần `db reset`), tuỳ chọn `schemas/` (declarative schema).

Default ports/URL khi `supabase start` (đồng thuận nhiều nguồn độc lập — xác nhận qua search, KHÔNG phải doc chính thức single-source, nên double-check output thực tế của `supabase start` vì có thể lệch version CLI):

| Service | Port | URL |
|---|---|---|
| API Gateway (Kong) | 54321 | http://localhost:54321 |
| Postgres | 54322 | postgresql://postgres:postgres@localhost:54322/postgres |
| Studio | 54323 | http://localhost:54323 |
| Inbucket (email test) | 54324 | http://localhost:54324 |

Key local (in ra khi `supabase start` chạy xong, hoặc `supabase status`): **anon key** (public, dùng client) và **service_role key** (bí mật, bypass RLS, chỉ dùng server-side). Supabase đang chuyển dần sang tên mới **publishable key** (`sb_publishable_...`) thay anon, và **secret key** (`sb_secret_...`) thay service_role — cả hai cặp cùng tồn tại song song đến hết 2026. Với stack local mới cài, `supabase start` output có thể show cả 2 dạng tuỳ version CLI — cần đọc output thực tế lúc setup, không hard-code.

Seed data: viết `supabase/seed.sql` tay (INSERT trực tiếp) — khuyến nghị cho scope nhỏ (~9 màn) thay vì dump từ remote (không có hosted project để dump).

Lưu ý khi chỉ chạy local, không link:
- `supabase link` không cần thiết cho dev thuần local.
- `db reset` xoá sạch data mỗi lần — không dùng cho seed "một lần rồi để yên", phải coi seed.sql là nguồn sự thật.
- Gen types phải chạy lại **mỗi khi đổi schema** (sau migration mới + `db reset` hoặc `db push` local) — nên thêm vào `package.json` script để không quên (xem mục 7).

## 3. Kết nối Supabase ↔ Next.js App Router

**Chuẩn hiện tại: `@supabase/ssr`.** `@supabase/auth-helpers-nextjs` **deprecated chính thức** — Supabase không khuyến khích dùng, và cảnh báo rõ: không được trộn 2 package trong cùng app.

Cấu trúc client (3 file, mỗi file <30 dòng, tuân KISS):

```ts
// lib/supabase/client.ts — Browser Client (Client Components)
import { createBrowserClient } from '@supabase/ssr'
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
```

```ts
// lib/supabase/server.ts — Server Client (Server Components/Actions/Route Handlers)
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'   // xác nhận từ next/dist/docs/.../cookies.md
export async function createClient() {
  const cookieStore = await cookies()
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => cookieStore.getAll(),
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options))
          } catch {
            // gọi từ Server Component (không set được) — bỏ qua, để proxy.ts refresh session
          }
        },
      },
    }
  )
}
```

**Quy tắc cứng từ Supabase**: chỉ dùng `getAll`/`setAll`, **không** dùng `get`/`set`/`remove` riêng lẻ (API cũ đã bị xoá khỏi khuyến nghị vì gây lỗi cookie chunk).

**Xung đột thật với Next 16**: `cookies()` chỉ set được trong Server Function/Route Handler (theo doc Next.js), **không** set được khi render Server Component. `@supabase/ssr` xử lý việc này bằng try/catch nuốt lỗi trong `setAll`, và dựa vào `proxy.ts` (middleware cũ) để refresh + ghi session cookie trên mọi request. Đây **không phải bug của @supabase/ssr** — là hệ quả trực tiếp từ model Next.js, pattern try/catch là design chính thức, không phải workaround tạm.

Do Proxy thay Middleware ở Next 16, pattern "refresh session" trong ví dụ chính thức Supabase (viết cho Next 15 trở xuống dùng `middleware.ts`) cần đổi tên file thành `proxy.ts` — nội dung logic (dùng `request.cookies.getAll()`, `NextResponse.next()`, set cookie cả trên `request` và `response`) không đổi. Một nguồn (WebFetch tóm tắt trang "AI Prompt: Bootstrap Next.js v16 app with Supabase Auth" của chính Supabase) xác nhận Supabase đã cập nhật guide riêng cho Next 16, nhấn mạnh: "không chạy code nào giữa `createServerClient` và `supabase.auth.getUser()`" để tránh session bị treo.

**Lưu ý về độ tin cậy**: 1 lần WebFetch trả về `import { cookies } from 'next/handlers'` (sai — phải là `next/headers`, đã tự xác nhận qua đọc trực tiếp file docs Next.js `04-functions/cookies.md`). Đây là lỗi tóm tắt của tool fetch, không phải từ Supabase — báo để không copy nhầm.

## 4. Supabase Auth

- **Email/password**: dùng Server Action (`'use server'`) gọi `supabase.auth.signInWithPassword` / `signUp`, theo đúng pattern Next.js "Mutating Data" (form → Server Action → `redirect()`).
- **OAuth (Google Workspace)**: `supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo } })` từ Client Component, cần 1 Route Handler `app/auth/callback/route.ts` để `exchangeCodeForSession`. Muốn giới hạn domain `@sun-asterisk.com` (Google Workspace) → check `email`/`hd` claim sau khi có session, redirect nếu sai domain (Supabase không tự giới hạn theo Workspace domain).
- **Bảo vệ route — dùng CẢ HAI, không phải chọn 1**:
  - **Proxy (`proxy.ts`)**: optimistic check — đọc cookie, redirect nếu chưa có session. Chạy trên mọi request kể cả prefetch → **không** query DB ở đây (perf).
  - **Layout/Page (Server Component) + DAL**: secure check thật sự — `verifySession()` dùng `React.cache` để dedupe, gọi trong page/component cần data nhạy cảm. Doc Next.js **khuyến cáo rõ ràng**: đừng chỉ check ở layout vì layout không re-render mỗi navigation (Partial Rendering) — phải check gần chỗ dùng data nhất.
  - Kết luận: Proxy cho UX (redirect nhanh, tránh flash nội dung sai), DAL/Server Component cho security thật.
- **Session refresh**: `supabase.auth.getUser()` gọi trong `proxy.ts` mỗi request để refresh access token hết hạn và ghi lại cookie mới — đây là lý do Proxy bắt buộc phải có nếu dùng cookie-based session.

## 5. RLS — pattern user thường vs admin

| Tiêu chí | JWT custom claim (`app_metadata.role`) | Bảng `user_roles` |
|---|---|---|
| Hiệu năng RLS | Không cần join/subquery — đọc thẳng từ `auth.jwt()`, rẻ | Cần subquery/join mỗi row check — có thể ảnh hưởng ở scale lớn |
| Cập nhật role có hiệu lực | Chậm hơn — phải đợi JWT refresh (hoặc force refresh) | Ngay lập tức — bảng SQL là nguồn sự thật |
| Audit/thao tác quản trị | Khó (phải update qua Admin API, không có UI SQL trực tiếp) | Dễ — update bằng SQL/Studio, log qua trigger |
| An toàn khỏi user tự sửa | `app_metadata` chỉ server/admin sửa được (khác `user_metadata` — user sửa được, **không dùng cho role**) | An toàn tương đương nếu RLS chặn user tự UPDATE bảng này |
| Độ phức tạp setup | Cần Custom Access Token Auth Hook (PL/pgSQL, phải bật trong Dashboard/config.toml) | Chỉ cần bảng + policy, không cần Hook |

**Khuyến nghị cho scope này (2 role: user/admin, ~9 màn)**: **bảng `user_roles`** là lựa chọn ưu tiên, không phải custom claim. Lý do: scope nhỏ, không có hàng nghìn subscriber/query mỗi giây → lợi ích hiệu năng của JWT claim không đáng giá so với cái giá phải trả (setup Auth Hook phức tạp hơn, role đổi không có hiệu lực ngay — dở cho use case "admin gỡ quyền 1 user" cần tức thời). Vi phạm YAGNI nếu chọn JWT claim ở scale này. Dùng JWT claim là early optimization sai chỗ.

Pattern RLS đề xuất:
```sql
create table user_roles (
  user_id uuid references auth.users(id) primary key,
  role text not null default 'user' check (role in ('user','admin'))
);
alter table user_roles enable row level security;
-- chỉ chính chủ hoặc admin đọc được row của mình; không ai UPDATE trực tiếp qua client
create policy "self read" on user_roles for select
  using (auth.uid() = user_id);

-- Hàm helper security definer để tránh lặp code trong mọi policy khác
create or replace function is_admin() returns boolean
language sql security definer stable as $$
  select exists(select 1 from user_roles where user_id = auth.uid() and role = 'admin');
$$;

create policy "admin full access" on kudos for all
  using (is_admin()) with check (is_admin());
create policy "user own insert" on kudos for insert
  with check (auth.uid() = author_id);
```

**Test policy ở local**: `supabase test db` (pgTAP) cho unit test SQL, hoặc đơn giản hơn cho scope nhỏ — dùng Supabase Studio local (localhost:54323) → SQL Editor, chạy `set role authenticated; set request.jwt.claims = '{"sub":"<uuid>"}'; select * from kudos;` để giả lập user cụ thể và xác nhận RLS chặn/cho đúng.

## 6. Supabase Realtime cho "Live board" (kudos + thả tim)

| | Postgres Changes | Broadcast | Presence |
|---|---|---|---|
| Cơ chế | Logical replication WAL → authorize từng subscriber | Gửi thẳng qua WebSocket, không qua DB | Theo dõi ai đang online/state tạm |
| Latency | ~50-200ms (qua WAL) | <50ms | thấp |
| Giới hạn scale (có RLS) | ~3.000-4.000 msg/s tổng, single-thread theo thứ tự | Không giới hạn kiểu đó — throughput cao hơn nhiều vì không auth từng subscriber | tương tự broadcast |
| Ngưỡng khuyến nghị chuyển sang Broadcast | >~3.000 subscriber đồng thời cùng 1 thay đổi | dùng khi >10 event/s/user (cursor, typing...) | — |
| Phù hợp cho | Đồng bộ **data đã persist** (bảng kudos, nguồn sự thật DB) | Việc **ephemeral tần suất cao** (con trỏ, typing, animation "thả tim" bay lên) | "đang có N người xem board" |

**Khuyến nghị xếp hạng cho tính năng Live board + thả tim** (quy mô nội bộ công ty, không phải public app — không đến 3.000 concurrent):
1. **Postgres Changes trên bảng `kudos`** — persist mỗi kudos, RLS tự động lọc theo quyền xem, đơn giản nhất để code (1 `.on('postgres_changes', ...)`), không cần thêm hạ tầng broadcast riêng. Phù hợp KISS/YAGNI cho quy mô nội bộ Sun*.
2. **Broadcast riêng cho animation "thả tim"** nếu muốn hiệu ứng tim bay real-time không cần persist mỗi lần thả tim thành 1 row DB (ví dụ tim là aggregate counter, không phải record) — tránh ghi DB dồn dập. Nếu thiết kế "thả tim" = tăng counter trên đúng 1 row kudos hiện có (không tạo row mới), thì Postgres Changes trên UPDATE là đủ, không cần Broadcast.
3. Presence: **không cần** cho scope mô tả — thêm phức tạp không có yêu cầu rõ ràng (YAGNI), trừ khi có thêm feature "ai đang xem board".

**React 19 Client Component — cleanup & StrictMode**:
```tsx
'use client'
useEffect(() => {
  const channel = supabase
    .channel('kudos-changes')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'kudos' }, handlePayload)
    .subscribe()
  return () => { supabase.removeChannel(channel) }
}, [])
```
StrictMode dev double-invoke effect → mount/unmount/mount lại → subscribe rồi unsubscribe rồi subscribe lại. Miễn cleanup gọi đúng `removeChannel`/`unsubscribe`, không leak — đây là hành vi supabase-js hỗ trợ sẵn (channel instance mới mỗi lần effect chạy, không share state global), không cần workaround riêng.

## 7. Type generation

```
npx supabase gen types typescript --local > lib/supabase/database.types.ts
```

Wire vào client để type-safe:
```ts
import type { Database } from './database.types'
export function createClient() {
  return createBrowserClient<Database>(url, anonKey)   // generic Database
}
```
Từ đó `supabase.from('kudos').select()` tự suy kiểu cột.

**Script nên thêm `package.json`**:
```json
{
  "scripts": {
    "supabase:start": "supabase start",
    "supabase:stop": "supabase stop",
    "supabase:reset": "supabase db reset",
    "supabase:types": "supabase gen types typescript --local > lib/supabase/database.types.ts"
  }
}
```
Vì CLI chưa cài global, đổi `supabase` → `npx supabase` trong từng script trên (repo dùng npx theo constraint đã cho).

## 8. Cấu trúc thư mục khuyến nghị (~9 màn, ~9 shared component, mỗi file <200 dòng)

```
app/
  layout.tsx                     # root layout, <html>/<body>, ThemeProvider nếu cần
  page.tsx                       # landing / redirect
  (auth)/
    login/page.tsx
    signup/page.tsx
  (dashboard)/
    layout.tsx                   # nav chung, KHÔNG check auth ở đây (chỉ optimistic UI)
    dashboard/page.tsx
    board/page.tsx                # Live board — Client Component con nhận initial data từ Server Component cha
    kudos/[id]/page.tsx
    profile/page.tsx
    admin/
      page.tsx                    # admin dashboard — auth check qua DAL, không qua layout
      users/page.tsx
  auth/
    callback/route.ts             # OAuth exchange code
  actions/
    auth-actions.ts                # <200 dòng: signup/login/logout Server Actions
    kudos-actions.ts               # create/update kudos Server Actions
  api/
    kudos/route.ts                 # nếu cần REST cho bên thứ 3 (thường không cần — Server Actions đủ)
proxy.ts                          # session refresh + optimistic redirect (KHÔNG middleware.ts)
lib/
  supabase/
    client.ts                     # createBrowserClient
    server.ts                     # createServerClient (await cookies())
    database.types.ts             # generated, KHÔNG sửa tay
  auth/
    dal.ts                        # verifySession() cache-wrapped, getUser()
    dto.ts                        # shape data trả cho client (ẩn field nhạy cảm)
  validations/
    kudos-schema.ts                # Zod schemas
components/
  ui/                              # ~9 shared: button.tsx, card.tsx, avatar.tsx, badge.tsx,
                                    # kudos-card.tsx, heart-button.tsx (Client), nav-bar.tsx,
                                    # loading-skeleton.tsx, empty-state.tsx
supabase/
  config.toml
  migrations/*.sql
  seed.sql
```

Nguyên tắc áp KISS/YAGNI/DRY:
- Không tạo `services/` layer trừu tượng riêng ngoài `lib/supabase` + `lib/auth` — 9 màn không cần thêm tầng.
- Mỗi Server Action file gom theo domain (`kudos-actions.ts`, `auth-actions.ts`), không 1 file 1 action (tránh nổ số file, nhưng vẫn <200 dòng/file nhờ tách domain).
- `proxy.ts` duy nhất ở root — theo đúng convention Next 16 (chỉ 1 file proxy được support, tách logic ra module riêng rồi import vào nếu phức tạp).
- Route Handler (`api/`) chỉ dùng khi thật sự cần (webhook, third-party) — mặc định dùng Server Actions cho mutation nội bộ, tránh DRY vi phạm (2 đường vào cùng logic).

## Khuyến nghị xếp hạng tổng hợp

1. **`@supabase/ssr`** (không cân nhắc `auth-helpers-nextjs` — đã deprecated, rủi ro maintenance = 0 lý do chọn).
2. **`proxy.ts`** thay `middleware.ts` ngay từ đầu — tránh nợ kỹ thuật codemod sau này.
3. **`user_roles` table** cho role, không JWT custom claim — đúng KISS/YAGNI cho quy mô 2 role/nội bộ; chỉ đổi sang JWT claim nếu sau này đo được RLS join là bottleneck thật.
4. **Postgres Changes** cho kudos board, không Broadcast — quy mô nội bộ Sun* chắc chắn dưới ngưỡng 3.000 subscriber; Broadcast chỉ thêm khi có nhu cầu ephemeral tần suất cao đo được.
5. **Không bật `cacheComponents`** cho phase này — model cache cũ đơn giản hơn, đủ cho CRUD + realtime; bật `cacheComponents` là quyết định kiến trúc lớn nên tách plan riêng nếu cần sau.
6. **Seed.sql viết tay**, không dump — không có hosted project để dump, và dữ liệu demo kudos dễ viết tay.

## Câu hỏi chưa giải quyết / cần xác nhận thêm

1. Local CLI hiện tại (chưa cài, dùng `npx supabase`) — chưa chạy thử `supabase start` thật trong máy này để xác nhận version CLI cụ thể in ra "anon key" hay "publishable key" theo tên mới. Cần chạy thử lúc implement.
2. Giới hạn domain Google Workspace (@sun-asterisk.com) khi OAuth — chưa tìm thấy config sẵn có phía Supabase Dashboard cho việc chặn domain; có thể cần tự check `hd` claim sau callback (đã nêu) — cần xác nhận lại field chính xác Google trả về qua Supabase OAuth response lúc code thật.
3. Custom Access Token Auth Hook (nếu sau này đổi sang JWT claim) yêu cầu bật qua Dashboard hoặc `config.toml` — local CLI có hỗ trợ bật hook này trong `[auth.hook.custom_access_token]` hay không chưa verify trực tiếp (chỉ có qua search, không WebFetch riêng phần này).
4. Có 1 WebFetch trả về snippet sai `next/handlers` thay vì `next/headers` — đã tự sửa dựa trên doc Next.js đọc trực tiếp, nhưng đáng lưu ý để không tin mù các trích dẫn code từ nguồn thứ cấp (blog/medium) mà không đối chiếu docs gốc.
5. Chưa test thực tế RLS policy bằng pgTAP (`supabase test db`) — chỉ mô tả cách làm, chưa chạy case cụ thể cho schema kudos vì schema chưa tồn tại ở bước research này.
