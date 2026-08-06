# Phase 01 — Nền tảng Supabase + Next 16

**Track:** B (backend/logic) · **Priority:** P1 · **Status:** completed · **Effort:** 3h
**Phụ thuộc:** không · **Mở khoá:** phase-02
**KHÔNG có quan hệ blocks/blockedBy với bất kỳ phase Track A nào.**

## Context Links

- Quyết định đã chốt: [`clarifications.md`](./clarifications.md)
- Ràng buộc Next 16 + Supabase local: [`reports/researcher-260805-1032-nextjs16-supabase-local.md`](./reports/researcher-260805-1032-nextjs16-supabase-local.md) §1, §2, §3, §7, §8
- Doc gốc Next 16 (đọc trực tiếp, không dựa trí nhớ): `node_modules/next/dist/docs/01-app/03-api-reference/03-file-conventions/proxy.md`, `.../04-functions/cookies.md`

## Overview

Dựng bộ khung chạy được: Supabase local lên, Next 16 nối được vào nó, session refresh hoạt động, i18n có chỗ đứng, script typegen sẵn sàng. Kết thúc phase này repo **chưa có bảng nào** — schema là việc của phase-02.

## Key Insights

1. **Next 16 đã đổi tên Middleware → Proxy.** File là `proxy.ts` ở root, export tên `proxy`. `middleware.ts` vẫn chạy nhưng deprecated → viết `proxy.ts` ngay từ đầu, không nợ codemod.
2. **`cookies()` là async và chỉ *ghi* được trong Server Function / Route Handler.** Server Component render không set cookie được — đây là lý do `@supabase/ssr` bọc `setAll` trong try/catch và vì sao `proxy.ts` **bắt buộc** phải có để refresh session.
3. Chỉ dùng `getAll`/`setAll` trong cấu hình cookie của `@supabase/ssr`. API `get`/`set`/`remove` lẻ đã bị loại khỏi khuyến nghị (gây lỗi cookie chunk).
4. **Không bật `cacheComponents`** trong `next.config.ts` — giữ model cache cũ (`fetch` mặc định no-store). Bật nó là quyết định kiến trúc lớn, ngoài scope.
5. Countdown lấy từ **env var**, không có bảng `event_config` (clarifications gap #1). Hai biến độc lập.
5b. **`NEXT_PUBLIC_*` bị inline vào bundle lúc `next build`, KHÔNG đọc lại lúc chạy.** Doc Next: *"After being built, your app will no longer respond to changes to these environment variables… frozen with the value evaluated at build time"* (`node_modules/next/dist/docs/01-app/02-guides/environment-variables.md:166`). Hệ quả vận hành phải nói thẳng: **đổi mốc countdown = sửa `.env` RỒI `next build` lại. Restart process là KHÔNG đủ.** Đây là cái giá đã chấp nhận khi chọn env var thay bảng `event_config` — không phải lỗi, nhưng phải ghi vào runbook.
6b. **`next.config.ts` phải khai `images.remotePatterns`.** File hiện đang trống. `next/image` chặn mọi host lạ → avatar Google (`lh3.googleusercontent.com`) và ảnh Supabase Storage local sẽ throw. Lỗi này **không lộ với seed demo**, chỉ bung ra lúc đăng nhập Google thật. `images.domains` đã deprecated (`version-16.md:878`) → dùng `remotePatterns`.
6. i18n **tự cuộn, không thêm dependency**: locale nằm ở cookie `NEXT_LOCALE`, không có prefix trên URL → `next-intl` (chủ yếu giải bài toán i18n routing) là thừa. YAGNI.
7. CLI Supabase chưa cài global → mọi lệnh đi qua `npx supabase`.

## Requirements

### Chức năng
- `npx supabase start` lên đủ stack local; ghi lại URL + key thực tế mà CLI in ra (**không hard-code theo tài liệu** — tên key có thể là `anon` hoặc `publishable` tuỳ version CLI).
- Browser client + Server client `@supabase/ssr`, đều generic hoá theo type `Database`.
- `proxy.ts` refresh session mọi request + chặn toàn site về `/prelaunch` khi chưa tới `NEXT_PUBLIC_LAUNCH_GATE_AT`.
- Đổi ngôn ngữ VN/EN qua cookie `NEXT_LOCALE`, mặc định `vi`.

### Phi chức năng
- Mỗi file < 200 dòng; file JS/TS đặt tên kebab-case.
- Không commit `.env.local`; chỉ commit `.env.local.example`.
- `npm run build` và `npx tsc --noEmit` phải sạch khi kết thúc phase.

## Architecture

### Luồng dữ liệu request

```
Browser request
  └→ proxy.ts
       ├─ createServerClient(cookies từ request)
       ├─ await supabase.auth.getUser()      ← KHÔNG chạy code nào giữa 2 dòng này
       ├─ isBeforeLaunchGate()? → rewrite/redirect /prelaunch
       └─ NextResponse.next() + ghi cookie session mới lên CẢ request và response
  └→ app/layout.tsx  (đọc cookie NEXT_LOCALE → nạp dictionary → LocaleProvider)
  └→ page.tsx (Server Component)  → lib/supabase/server.ts → Postgres local
```

### Cách chia module (giữ proxy.ts mỏng)

`proxy.ts` chỉ điều phối; logic nằm ở module riêng để phase-03 mở rộng route guard mà không phình file:

```
proxy.ts                      ← ~40 dòng, orchestrator (phase-01 sở hữu)
lib/launch-gate.ts            ← isBeforeLaunchGate(now) thuần, không I/O (phase-01)
lib/supabase/proxy-session.ts ← updateSession(request) trả {response, user} (phase-01)
lib/auth/route-guard.ts       ← phase-03 tạo, proxy.ts import thêm 1 dòng
```

### i18n

```
locales/vi/common.json  locales/en/common.json      ← phase-01 seed 2 file này
lib/i18n/config.ts        ← LOCALES = ['vi','en'], DEFAULT_LOCALE = 'vi'
lib/i18n/get-dictionary.ts← server-side: đọc cookie NEXT_LOCALE → import JSON namespace
lib/i18n/locale-provider.tsx ← 'use client' context, hook useT(namespace)
lib/actions/set-locale.ts ← Server Action ghi cookie NEXT_LOCALE (được phép set ở đây)
```
Mỗi phase Track A về sau sở hữu namespace JSON riêng của mình (`login.json`, `profile.json`…) → không hai phase nào ghi cùng một file locale.

## Related Code Files

**Tạo mới**
- `supabase/config.toml` (sinh bởi `npx supabase init`)
- `lib/supabase/client.ts`, `lib/supabase/server.ts`, `lib/supabase/proxy-session.ts`
- `lib/launch-gate.ts`
- `lib/i18n/config.ts`, `lib/i18n/get-dictionary.ts`, `lib/i18n/locale-provider.tsx`
- `lib/actions/set-locale.ts`
- `locales/vi/common.json`, `locales/en/common.json`
- `proxy.ts`
- `.env.local.example`, `.env.local` (không commit)

**Sửa**
- `package.json` (thêm dependency + script) — **bàn giao**: phase-04 thêm `zod`, phase-17 thêm devDeps + scripts. Ba phase này chain tuần tự nên không giẫm chân; mỗi phase chỉ chạm khối của mình.
- `app/layout.tsx` (bọc `LocaleProvider`, set `lang` theo locale — `await cookies()`)
- `next.config.ts` (đang trống — thêm `images.remotePatterns`)
- `.gitignore` (thêm `.env.local`, `supabase/.temp`, `supabase/.branches`)

**Xoá:** không

**File ownership (glob):** `supabase/config.toml`, `lib/supabase/{client,server,proxy-session,database.types}.ts`, `lib/launch-gate.ts`, `lib/i18n/**`, `lib/actions/set-locale.ts`, `locales/*/common.json`, `proxy.ts`, `app/layout.tsx`, `next.config.ts`, `package.json`, `.env.local.example`, `.gitignore`, `docs/runbook-su-kien.md`

## Bàn giao kiểm soát sau thực thi

Phase-07 (UI Login) sửa file của phase-01 theo khuôn bàn giao có kiểm soát, **cùng mô hình 01→03, 01→04, 01→17** (hai phase cùng chạm một file thì sớm → muộn bàn giao tuần tự nên không giẫm chân):

- **`lib/i18n/get-dictionary.ts`:** thêm tham số `namespace` tùy chọn, dùng `import()` template literal thay `fs.readFile` để bundler gói JSON sẵn. (Phase-06 dùng `getDictionary` qua `lib/i18n/get-dictionary.ts`; phase-07 tổng quát hoá thành hook `useNamespaceTranslation` dùng cơ chế chung.)
- **`components/ui/use-common-ui-text.ts`** (phase-06, không phase-01 sở hữu) → migrate từ `getDictionary` sang `useNamespaceTranslation`, nằm ở track A chứ không track B, nhưng là bàn giao cưỡng chế qua hook phase-07 phát hành.

**Quy ước:** Từ phase-08+ nếu muốn sửa `lib/i18n/**` hoặc bất kỳ file "phase-01 sở hữu" nào phải làm theo cùng khuôn này (thông qua 1-2 dòng import/interface mới, không phình file hơn 5 dòng), hoặc mở task riêng bàn giao tuần tự với phase-01 chủ file.

## Implementation Steps

1. `npm i @supabase/supabase-js @supabase/ssr` — **không** cài `@supabase/auth-helpers-nextjs` (đã deprecated, cấm trộn hai package).
2. `npx supabase init` → sinh `supabase/config.toml`. `npx supabase start` → **chép nguyên văn** API URL + key từ output vào `.env.local`.
3. Viết `.env.local.example` với 4 biến: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_LAUNCH_GATE_AT`, `NEXT_PUBLIC_EVENT_START_AT`. Hai biến thời gian ghi ISO-8601 có offset `+07:00` (vd `2025-11-20T09:00:00+07:00`). Ghi comment ngay trong file: `# đổi giá trị này BẮT BUỘC chạy lại "next build" — restart không đủ`.
3b. **`next.config.ts`**: khai `images.remotePatterns` cho hai host — `{protocol:'https', hostname:'lh3.googleusercontent.com'}` (avatar Google) và `{protocol:'http', hostname:'127.0.0.1', port:'54321', pathname:'/storage/v1/object/public/**'}` (Supabase Storage local). Không dùng `images.domains` (deprecated).
4. `lib/supabase/client.ts` — `createBrowserClient<Database>(url, key)`.
5. `lib/supabase/server.ts` — `async function createClient()`, bên trong `const cookieStore = await cookies()`, cấu hình `cookies: { getAll, setAll }`, `setAll` bọc try/catch nuốt lỗi (gọi từ Server Component là hợp lệ, để `proxy.ts` lo ghi cookie).
6. `lib/launch-gate.ts` — hàm thuần `isBeforeLaunchGate(now: Date): boolean` đọc `NEXT_PUBLIC_LAUNCH_GATE_AT`; env thiếu/không parse được → trả `false` (fail-open, không khoá nhầm cả site).
7. `lib/supabase/proxy-session.ts` — `updateSession(request)`: tạo server client từ `request.cookies.getAll()`, gọi `supabase.auth.getUser()` **ngay sau khi tạo client, không chèn code nào ở giữa**, ghi cookie mới lên cả `request` lẫn `response`.
8. `proxy.ts` — export `proxy(request)`; gọi `updateSession`, rồi kiểm tra launch gate. Export `config.matcher` loại trừ `_next/static`, `_next/image`, `favicon.ico`, `*.svg|png|jpg`, và `/prelaunch` (tránh redirect vòng).
9. `lib/i18n/*` + 2 file `locales/*/common.json` (nội dung tối thiểu: nav, nút chung, thông báo lỗi chung). `lib/actions/set-locale.ts` là `'use server'` — chỉ ở đây mới `cookieStore.set('NEXT_LOCALE', …)` được.
10. `app/layout.tsx`: `const locale = (await cookies()).get('NEXT_LOCALE')?.value ?? 'vi'`, set `<html lang={locale}>`, bọc `<LocaleProvider>`. **Không** render Header/Footer ở đây (Header thuộc Track A phase-06; layout dựng Header sẽ tạo phụ thuộc chéo track).
11. Thêm script `package.json`: `supabase:start`, `supabase:stop`, `supabase:reset`, `supabase:types` (`npx supabase gen types typescript --local > lib/supabase/database.types.ts`), `typecheck` (`tsc --noEmit`).
12. Chạy `npm run supabase:types` lần đầu để có `database.types.ts` (rỗng nhưng hợp lệ) → `tsc` không đỏ.
13. `npx tsc --noEmit` + `npm run build` phải xanh.

## Todo List

- [x] Cài `@supabase/supabase-js` + `@supabase/ssr`
- [x] `npx supabase init` + `npx supabase start`, ghi key thật vào `.env.local`
- [x] `.env.local.example` (4 biến) + comment cảnh báo rebuild + cập nhật `.gitignore`
- [x] `next.config.ts` khai `images.remotePatterns` (Google avatar + Supabase Storage local)
- [x] Ghi runbook "đổi mốc countdown" vào `docs/runbook-su-kien.md`
- [x] `lib/supabase/client.ts`, `server.ts`, `proxy-session.ts`
- [x] `lib/launch-gate.ts`
- [x] `proxy.ts` + `config.matcher`
- [x] `lib/i18n/**` + `locales/{vi,en}/common.json` + `lib/actions/set-locale.ts`
- [x] `app/layout.tsx` nạp locale (await cookies)
- [x] 5 script trong `package.json`
- [x] `tsc --noEmit` + `npm run build` xanh

## Success Criteria

- `npx supabase status` liệt kê đủ API/DB/Studio; Studio mở được ở `localhost:54323`.
- Ở root repo **có `proxy.ts`, KHÔNG có `middleware.ts`**.
- `grep -rn "middleware" proxy.ts` không khớp; `grep -rn "cookies()" lib app | grep -v await` trả rỗng.
- Đặt `NEXT_PUBLIC_LAUNCH_GATE_AT` ở tương lai → mọi URL (`/`, `/kudos`, `/login`) đều đáp về `/prelaunch`. Đặt ở quá khứ → truy cập bình thường, `/prelaunch` đá về `/`.
- Đổi cookie `NEXT_LOCALE` từ `vi` sang `en` → chuỗi trong `common.json` đổi theo, `<html lang>` đổi theo.
- **Kiểm chứng hành vi inline**: `next build` → `next start` → sửa `NEXT_PUBLIC_LAUNCH_GATE_AT` trong `.env.local` → restart process → countdown **KHÔNG đổi** (đúng như mong đợi); chạy lại `next build` → countdown **đổi**. Ghi kết quả này vào runbook để người vận hành không mất buổi chiều đi tìm.
- `next.config.ts` có `images.remotePatterns`; render `<Image src="https://lh3.googleusercontent.com/...">` không throw.
- `npm run build` exit 0.

## Runbook — đổi mốc thời gian countdown

```
1. sửa NEXT_PUBLIC_LAUNCH_GATE_AT và/hoặc NEXT_PUBLIC_EVENT_START_AT trong .env.local
2. npm run build      ← BẮT BUỘC, không được bỏ
3. npm start
```
Bỏ bước 2 thì giá trị cũ vẫn nằm trong bundle JS đã gửi xuống trình duyệt.

## Risk Assessment

| Rủi ro | K/năng × T/động | Giảm thiểu |
|---|---|---|
| Viết `middleware.ts` theo thói quen Next 14 | Cao × Cao | Success criteria có bước grep; phase-17 thêm test khẳng định file không tồn tại |
| Tên key CLI in ra là `publishable`/`secret` (tên mới) chứ không phải `anon` | TB × TB | Bước 2 bắt buộc chép từ output thật, không copy từ tài liệu |
| Launch gate khoá nhầm cả site do env sai định dạng | TB × Cao | `isBeforeLaunchGate` fail-open khi parse lỗi + log cảnh báo |
| Redirect vòng vô hạn `/prelaunch` → `/prelaunch` | TB × Cao | Loại `/prelaunch` khỏi `config.matcher` và thêm early-return theo pathname |
| Docker chưa chạy → `supabase start` fail | TB × Thấp | Kiểm tra `docker info` trước; ghi vào README bước chuẩn bị |
| Sửa `.env` rồi restart, tưởng countdown đã đổi (thực tế vẫn giá trị build cũ) | **Cao** × TB | Runbook + comment trong `.env.local.example` + case kiểm chứng trong Success Criteria |
| `next/image` throw với avatar Google — chỉ lộ khi login thật, không lộ với seed | TB × Cao | `images.remotePatterns` ngay ở phase-01, trước khi phase-03 bật OAuth |

## Security Considerations

- `.env.local` **không bao giờ** vào git. Chỉ `anon`/`publishable` key mới được đặt tiền tố `NEXT_PUBLIC_`; `service_role`/`secret` key tuyệt đối không có tiền tố đó và phase này **không dùng tới**.
- `proxy.ts` là kiểm tra *lạc quan* phục vụ UX. Bảo mật thật nằm ở RLS (phase-02) + DAL (phase-03) — không được coi proxy là hàng rào an ninh.
- Không truy vấn DB trong `proxy.ts` (chạy trên mọi request kể cả prefetch).

## Kết quả thực thi

**Thống kê file:**
- Tạo mới 10: `proxy.ts` (59 dòng), `lib/launch-gate.ts`, `lib/supabase/{client,server,proxy-session,database.types}.ts`, `lib/i18n/{config,get-dictionary,locale-provider}.tsx`, `lib/actions/set-locale.ts`, `locales/{vi,en}/common.json`, `.env.local.example`, `docs/runbook-su-kien.md`, `supabase/config.toml`.
- Sửa 5: `app/layout.tsx`, `next.config.ts`, `package.json`, `.gitignore`.

**Xác thực hành vi:**
- `npx supabase status`: API 54321, DB 54322, Studio 54323 lên bình thường.
- Có `proxy.ts`, không tồn tại `middleware.ts`.
- Kiểm tra async cookies: `grep "cookies()" | grep -v await` → rỗng.
- Gate quá khứ (`NEXT_PUBLIC_LAUNCH_GATE_AT=2000-01-01T00:00:00+07:00`) → `/` 200 OK, `/prelaunch` 307 redirect về `/`. Gate tương lai → `/`, `/kudos`, `/login` 307 về `/prelaunch`; `/prelaunch` không redirect vòng.
- Locale: no cookie → `lang="vi"`; `NEXT_LOCALE=en` → `lang="en"`; giá trị rác `xx` → fallback `vi`. Parity key giữa `locales/vi/common.json` và `locales/en/common.json` OK.
- **Inline env xác minh đúng:** sửa `NEXT_PUBLIC_LAUNCH_GATE_AT` trong `.env.local` rồi `npm start` → `/` vẫn 200 (giá trị cũ trong bundle). Build lại → 307. Đúng như runbook cảnh báo.

**Lỗi Critical (đã sửa + verify lại):**
- `proxy.ts` ban đầu: hai nhánh redirect trả `NextResponse.redirect()` mới, làm mất cookie session. Supabase single-use refresh token → bị đốt, browser không nhận token mới → đăng xuất ngẫu nhiên. Khi gate khoá (prelaunch), MỌI request redirect → tất cả người dùng đều đăng xuất. **Sửa**: helper `redirectKeepingSession()` sao chép `set-cookie` sang response redirect. **End-to-end verify:** tạo user test, ép refresh token (date cũ), gọi `/prelaunch` → response 307 có `set-cookie`. Xoá user test sau.

**Cổng check:**
- `npx tsc --noEmit` exit 0.
- `npm run build` exit 0.
- `npx eslint proxy.ts lib app next.config.ts` (không bao gồm `.claude/**`, `plans/**`) exit 0.

Report chi tiết: `reports/tester-260805-1650-phase-01-nen-tang.md`, `reports/reviewer-260805-1650-phase-01-nen-tang.md`.

## Phát hiện quan trọng cho phase tiếp theo

1. **Tên biến env khác plan**: Plan ghi `NEXT_PUBLIC_SUPABASE_ANON_KEY`, nhưng CLI Supabase in ra cả `PUBLISHABLE_KEY` (`sb_publishable_…`, tên mới) lẫn `ANON_KEY` (JWT legacy, `eyJhbGc…`). Đã dùng key mới với tên biến **`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`**. Phase-02/03/04 phải dùng tên này, không phải tên plan gốc.

2. **npm script phải dùng `npx supabase`**: CLI không có trong `node_modules/.bin` → script không được gọi `supabase` trần, phải dùng `npx supabase` hay `./node_modules/.bin/supabase`.

3. **`npm run lint` toàn repo ĐỎ (exit 1, 866 lỗi)**: Nguyên nhân là `.claude/hooks/*.cjs` của bộ kit Takumi (có từ HEAD `2a1edf1` trước phase-01). Code phase-01 lint sạch. Điều này **chặn cổng `npm run validate` của phase-17**. Giải pháp: thêm `.claude/**` và `plans/**` vào `globalIgnores` trong `eslint.config.mjs` (file này hiện KHÔNG thuộc ownership của phase nào).

4. **`app/prelaunch/` chưa tồn tại**: Khi gate đóng, redirect tới `/prelaunch` trả 404. Đúng thiết kế: trang đó thuộc phase-14. Chú ý khi kiểm tra: phải tắt gate (set `NEXT_PUBLIC_LAUNCH_GATE_AT` ở quá khứ) để test route khác.

## Next Steps

- phase-02 dùng `npm run supabase:types` sau mỗi migration.
- phase-03 thêm `lib/auth/route-guard.ts` và chèn đúng **một dòng** import vào `proxy.ts`.
- Track A có thể khởi động độc lập ngay, không chờ phase này.

## Rollback

`git revert` phase commit + `npx supabase stop --no-backup`. Không có dữ liệu người dùng nào tồn tại ở bước này → hoàn tác không để lại hệ quả.
