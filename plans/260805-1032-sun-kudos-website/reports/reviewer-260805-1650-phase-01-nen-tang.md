# Review Phase-01 — Nền tảng Supabase + Next 16 (Sun* Kudos)

## Phạm vi

- **Files reviewed** (toàn bộ uncommitted, đối chiếu `git status`/`git diff`):
  - Mới: `proxy.ts`, `lib/launch-gate.ts`, `lib/supabase/{client,server,proxy-session}.ts`, `lib/i18n/{config,get-dictionary,locale-provider}.{ts,tsx}`, `lib/actions/set-locale.ts`, `locales/{vi,en}/common.json`, `.env.local.example`, `docs/runbook-su-kien.md`, `supabase/config.toml`, `lib/supabase/database.types.ts`
  - Sửa: `app/layout.tsx`, `next.config.ts`, `package.json`, `.gitignore`, `package-lock.json`
- **Lines**: ~372 dòng code phase-01 (mọi file < 200 dòng, xem bảng `wc -l` bên dưới)
- **Depth**: full — đọc từng file, chạy `tsc --noEmit`, `npm run build`, `eslint`, `git check-ignore`, và test runtime redirect thật (`PORT=3123 npm start`, đã kill process sau khi xong)

## Đánh giá chung

Code sạch, đúng tinh thần Next 16 (proxy thay middleware, `cookies()` async, không bật `cacheComponents`), bám sát plan và clarifications. `npx tsc --noEmit`, `npm run build`, `npx eslint proxy.ts lib app next.config.ts` đều exit 0. Không secret nào lọt vào file sẽ commit. **Một lỗi Critical** ở `proxy.ts` làm mất cookie session vừa refresh mỗi khi có redirect (launch-gate hoặc prelaunch-bounce) — đúng chỗ brief nghi ngờ nhất, và nghi ngờ đó đúng.

## Critical

| # | File:line | Vấn đề | Kịch bản hỏng |
|---|---|---|---|
| 1 | `proxy.ts:23-30` | `updateSession()` trả `{ response }` đã ghi cookie session mới (`lib/supabase/proxy-session.ts:29-32`), nhưng cả hai nhánh redirect (`NextResponse.redirect(new URL(PRELAUNCH_PATH, ...))` và `NextResponse.redirect(new URL("/", ...))`) tạo **response mới hoàn toàn**, không copy cookie từ `response` refreshed sang. Chỉ nhánh "đi thẳng" (`return response` ở dòng 32) mới mang cookie mới. | Refresh token của Supabase là **single-use** (README `node_modules/@supabase/ssr/README.md:41-48` nói rõ). Kịch bản cụ thể: site đang ở trạng thái prelaunch (Gap #11 đã chốt "không ai bypass" → **mọi** request về `/prelaunch`). Mỗi request tới proxy đều gọi `getUser()` → nếu access token hết hạn, Supabase refresh và trả cookie mới trong `response`; nhưng vì request luôn rơi vào nhánh redirect (dòng 24), cookie mới đó **bị vứt**. Browser vẫn giữ refresh token cũ (đã bị Supabase đánh dấu dùng rồi) → request kế tiếp refresh lại bằng token đã tiêu, thất bại → `getUser()` trả `null` → **user bị đăng xuất ngẫu nhiên trong suốt giai đoạn prelaunch**, đúng như lo ngại "chen code giữa createServerClient và getUser sinh lỗi đăng xuất ngẫu nhiên" mà code đã phòng đúng chỗ đó nhưng lại hở ở bước redirect. Vấn đề còn tồn tại cả sau khi mở màn, ở nhánh đá `/prelaunch` → `/`. |

**Cách sửa cụ thể**: viết một helper copy cookie từ response refreshed sang response cuối cùng trước khi trả, áp dụng cho MỌI đường ra của `proxy()`:

```ts
// proxy.ts
function withRefreshedCookies(target: NextResponse, refreshed: NextResponse): NextResponse {
  refreshed.cookies.getAll().forEach((cookie) => target.cookies.set(cookie));
  return target;
}

export async function proxy(request: NextRequest) {
  const { response } = await updateSession(request);
  const { pathname } = request.nextUrl;
  const onPrelaunch = pathname === PRELAUNCH_PATH;
  const beforeLaunch = isBeforeLaunchGate();

  if (beforeLaunch && !onPrelaunch) {
    return withRefreshedCookies(
      NextResponse.redirect(new URL(PRELAUNCH_PATH, request.url)),
      response,
    );
  }
  if (!beforeLaunch && onPrelaunch) {
    return withRefreshedCookies(
      NextResponse.redirect(new URL("/", request.url)),
      response,
    );
  }
  return response;
}
```

Đây là gotcha kinh điển của pattern `@supabase/ssr` + redirect (chính README của package cũng cảnh báo về vòng đời refresh token single-use ở dòng 41-48) — không phải suy đoán, mà suy trực tiếp từ code + tài liệu đã đọc.

## Warning

| # | File:line | Vấn đề | Đề xuất |
|---|---|---|---|
| 1 | `phase-01-nen-tang-supabase-va-next.md:99` (File ownership glob) | Glob liệt kê không bao gồm `docs/runbook-su-kien.md` và `lib/supabase/database.types.ts`, dù cả hai đều được tạo bởi phase-01 (Todo List dòng 124, Implementation Step 12). `database.types.ts` đặc biệt quan trọng vì phase-02 sẽ ghi đè nó sau mỗi migration (Next Steps dòng 173) — nếu glob không khai rõ, dễ sinh tranh chấp ownership khi chạy song song nhiều phase sau này. | Bổ sung 2 đường dẫn này vào glob của phase-01 (và ghi chú `database.types.ts` là "sở hữu chung, phase-02 được phép ghi đè"). Không phải lỗi code, chỉ là gap tài liệu — nhưng đúng loại vấn đề brief yêu cầu soi (#8). |
| 2 | `proxy.ts:23-30` | Redirect dùng mặc định `NextResponse.redirect()` → status `307`, giữ nguyên method. Nếu một Server Action (POST) được gọi trên trang đang bị gate (vd ai đó có form còn cache trong tab từ trước khi site chuyển sang prelaunch), request sẽ bị 307 POST sang `/prelaunch` — route này không có handler cho POST → lỗi khó hiểu thay vì rơi về GET nhẹ nhàng. | Không chặn merge (kịch bản hiếm, cần UI thật mới trigger được, và chưa có UI ở phase này) nhưng đáng cân nhắc dùng `status: 303` cho nhánh redirect launch-gate khi phase-03+ thêm action vào các trang bị gate. |

## Suggestion

| # | File:line | Ghi chú |
|---|---|---|
| 1 | `proxy.ts:40` (`config.matcher`) | Regex loại `.svg\|png\|jpg\|jpeg\|gif\|webp\|ico$` chỉ khớp chữ thường — `curl` test cho thấy `/logo.PNG` (hoa) vẫn lọt qua proxy (test bằng Node regex, xem log). Rủi ro thấp (Next.js serve asset tĩnh không phân biệt hoa/thường theo OS, và guồng máy build thường đặt tên file thường), không phải lỗi chặn nhầm nghiêm trọng, nhưng thêm flag `i` hoặc `[Pp][Nn][Gg]`-style nếu muốn chặt hơn. |
| 2 | `lib/supabase/server.ts:32-35` | `catch {}` rỗng nuốt **mọi** lỗi từ `cookieStore.set`, không riêng lỗi "gọi từ Server Component" (đây đúng là pattern chính thức Supabase khuyến nghị, không phải lỗi tự chế). Nếu muốn debug dễ hơn, có thể `console.debug` lỗi khi `process.env.NODE_ENV !== "production"` — không bắt buộc, vì hành vi hiện tại đúng theo tài liệu upstream. |
| 3 | `lib/actions/set-locale.ts:22-26` | Cookie `NEXT_LOCALE` không set `secure: true`. Không phải secret (chỉ chứa `"vi"`/`"en"`) nên rủi ro thực tế bằng 0, nêu ra cho đủ, không cần sửa. |
| 4 | `.claude/.skignore`, `.claude/.tkm.json`, `.claude/hooks/.logs/hook-log.jsonl`, `.claude/settings.json` | Nằm ngoài glob ownership phase-01 nhưng là artifact của chính quy trình làm việc (tkm config ghi quyết định "SDD off" đã chốt ở `clarifications.md`, hook log là log phiên). Không phải code app, không cần đưa vào phase file. Nêu để không bị hiểu lầm là "file lạ chạm nhầm". |

## Đối chiếu Acceptance (Success Criteria)

| Tiêu chí | Kết quả |
|---|---|
| `npx supabase status` liệt kê đủ API/DB/Studio | ✅ (đã chạy, JSON đầy đủ URL/key) |
| Có `proxy.ts`, không có `middleware.ts` | ✅ `ls middleware.ts` → not found |
| `grep -rn "middleware" proxy.ts` rỗng, `grep cookies() | grep -v await` rỗng | ✅ đã chạy, đúng |
| Gate tương lai → mọi URL về `/prelaunch`; gate quá khứ → bình thường, `/prelaunch` đá về `/` | ✅ test runtime: gate hiện đang ở quá khứ (2025-11-20 < hôm nay 2026-08-05) → `/prelaunch` trả 307 về `/`, đúng thiết kế. **Nhưng xem Critical #1 — cookie session bị mất trong đúng lối redirect này.** |
| Đổi `NEXT_LOCALE` → dictionary + `<html lang>` đổi theo | ✅ đọc code xác nhận logic đúng (`get-dictionary.ts` + `layout.tsx`), chưa test tay qua trình duyệt vì chưa có UI đổi ngôn ngữ (thuộc Track A phase-06) |
| Countdown inline-at-build, restart không đủ | ✅ đã ghi đúng vào runbook + `.env.local.example`, đúng trích dẫn doc |
| `images.remotePatterns` khai đủ 2 host | ✅ đúng 2 host theo plan, không dùng `images.domains` |
| `npm run build` exit 0 | ✅ đã chạy, thành công (Turbopack, `ƒ Proxy (Middleware)` xuất hiện đúng) |

## Edge Cases từ vòng scout

- Race hai tab cùng refresh token hết hạn cùng lúc: giới hạn đã biết của `@supabase/ssr` (chính README package cảnh báo), không phải lỗi phase-01, nhưng **Critical #1 làm nó tệ hơn** vì ngay cả trường hợp 1-tab bình thường cũng mất cookie mỗi khi rơi vào nhánh redirect.
- `lib/supabase/database.types.ts` hiện tại rỗng-hợp-lệ (`Tables: [_ in never]: never`), đúng "chưa có bảng nào" — xác nhận bằng đọc file. Nó **không** bị gitignore và **nên tiếp tục committed**: nếu gitignore nó, `tsc --noEmit`/`build` sẽ đỏ trên máy fresh-clone chưa chạy Supabase local (vì `client.ts`/`server.ts`/`proxy-session.ts` đều `import type { Database } from "./database.types"`). Trả lời câu hỏi #10 trong brief: **commit, không gitignore** — phase-02 ghi đè sau mỗi migration là hành vi đã được Next Steps ghi nhận.
- `.env.local` xác nhận **không** track (`git check-ignore -v` → khớp rule `.env*`), `.env.local.example` xác nhận unignored đúng ý đồ (`!.env.local.example`). Không secret thật nào trong file sẽ commit — đã grep toàn bộ `supabase/config.toml`, `.env.local.example`, `docs/runbook-su-kien.md`.
- `package-lock.json`: mọi `resolved` đều trỏ `registry.npmjs.org`, không có nguồn lạ.
- React 19.2.8 xác nhận **có hỗ trợ** cú pháp `<LocaleContext value={...}>` (không phải đoán): `node_modules/react-dom/cjs/react-dom-server.node.development.js` xử lý `case REACT_CONTEXT_TYPE` tại các dòng 3685/6275/6713/10161, và `ctx.$$typeof === Symbol.for("react.context")` khớp type mà JSX truyền vào khi dùng Context trực tiếp làm provider (tính năng mới React 19).

## Làm tốt

- Tách `proxy.ts` mỏng (42 dòng), logic launch-gate và session nằm riêng module thuần — đúng kiến trúc plan yêu cầu, dễ mở rộng ở phase-03 mà không phình file.
- Comment giải thích rất kỹ "vì sao" ở đúng những chỗ dễ sai (giữa `createServerClient` và `getUser()`, tại sao `setAll` bọc try/catch, vì sao fail-open) — đúng tinh thần "code tự tài liệu hoá".
- Không một dòng nào truy vấn DB trong `proxy.ts`, đúng Security Considerations.
- `.env.local.example` với comment cảnh báo rebuild ngay trong file, không chỉ trong docs — giảm khả năng người vận hành bỏ sót.
- Runbook (`docs/runbook-su-kien.md`) trích dẫn đúng đường dẫn doc gốc kèm số dòng, không diễn giải sai.

## Thứ tự hành động

1. **Bắt buộc trước khi merge**: sửa Critical #1 — copy cookie refreshed sang mọi response redirect trong `proxy.ts`.
2. Bổ sung `docs/runbook-su-kien.md` và `lib/supabase/database.types.ts` vào glob ownership của phase-01 (sửa file plan, không phải code).
3. (Tuỳ chọn, không chặn) cân nhắc `status: 303` cho redirect launch-gate một khi phase sau có Server Action trên trang bị gate.

## Số liệu

- Type coverage: `npx tsc --noEmit` — 0 lỗi
- Lint: `npx eslint proxy.ts lib app next.config.ts` — 0 lỗi (lint toàn repo đỏ 866 lỗi từ trước, không thuộc phase-01, đã xác minh qua `git blame`/mô tả brief)
- Build: `npm run build` — exit 0
- File lớn nhất phase-01: `lib/supabase/proxy-session.ts` (45 dòng) — mọi file đều dưới 200 dòng

## Còn treo

- Không thể test tay bằng trình duyệt thật luồng "đổi NEXT_LOCALE → UI đổi theo" vì UI chọn ngôn ngữ thuộc Track A phase-06 (chưa build) — đã xác nhận đúng bằng đọc code, không phải bằng test end-to-end.
- Chưa thể tái hiện runtime chính xác kịch bản mất cookie ở Critical #1 bằng một session Supabase thật (cần luồng login OAuth, thuộc phase-03+) — kết luận dựa trên đọc code + tài liệu `@supabase/ssr`, độ tin cậy cao nhưng chưa phải bằng chứng runtime 100%.

**Status:** DONE_WITH_CONCERNS
**Summary:** Code phase-01 sạch lint/type/build, bám sát plan Next 16 + Supabase SSR, nhưng có 1 lỗi Critical ở `proxy.ts` (redirect vứt cookie session vừa refresh, đúng chỗ brief nghi ngờ) cần sửa trước khi commit; còn lại là gap tài liệu nhỏ (ownership glob thiếu 2 file) và vài suggestion không chặn.
**Concerns/Blockers:** Critical #1 (`proxy.ts:23-30`) nên sửa trước khi commit — nguy cơ đăng xuất ngẫu nhiên trong toàn bộ giai đoạn prelaunch, đúng loại lỗi "qua CI vẫn vỡ khi chạy thật".
