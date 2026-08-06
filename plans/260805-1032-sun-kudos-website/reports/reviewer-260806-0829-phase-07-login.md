# Review — Phase-07 (`/login`) + bàn giao hạ tầng i18n (phase-01 → phase-07)

## Phạm vi
- **Hạ tầng (diff trong file phase-01 sở hữu):** `lib/i18n/get-dictionary.ts` (sửa), `lib/i18n/use-namespace-translation.ts` (mới), `components/ui/use-common-ui-text.ts` (sửa)
- **Phase-07:** `app/login/page.tsx`, `components/login/{login-screen,login-page-client,use-login-text}`, `locales/{vi,en}/login.json`, `public/login/Root_Further_Logo.png`
- Dòng thay đổi: ~76 dòng diff (hạ tầng) + ~312 dòng file mới (phase-07). Mọi file < 200 dòng.
- Độ sâu: đọc toàn bộ diff, build thật (`npm run build`), soi `.next/server` để kiểm chứng hành vi bundler, `tsc`/`eslint` chạy lại, `npm start` + `curl` để kiểm exploit thực tế.

## Đánh giá chung
Chất lượng cao, đúng tinh thần "bàn giao có kiểm soát". Quyết định đổi `fs.readFile(process.cwd()+…)` → `import()` template literal là **đúng và có bằng chứng thực nghiệm ủng hộ** (xem mục 1 bên dưới) — không phải chỉ lý thuyết suông. Race/cache/validate đều đúng. Phase-07 sạch: không đụng ngoài ownership, không import `lib/supabase|data|actions`, acceptance criteria đạt (đo bằng curl thật, có cả case tấn công). Không tìm thấy **Critical**. Một vài **Warning** đáng sửa sớm (a11y alert timing, thiếu ràng buộc kiểu cho `namespace`), phần còn lại là **Suggestion**.

---

## Critical
Không có.

## Warning

| # | File:dòng | Vấn đề | Kịch bản hỏng |
|---|---|---|---|
| W1 | `components/login/login-screen.tsx:74-81` | Alert `role="alert"` được render **ngay trong SSR/hydration ban đầu** khi `?error=oauth`, không phải chèn vào DOM sau khi trang đã "sống". Theo cách hoạt động thật của `aria-live`/`role="alert"`, trình đọc màn hình (NVDA/JAWS/VoiceOver) chỉ phát hiện **thay đổi** trong vùng live — nội dung đã có mặt từ lần render đầu tiên thường **không được công bố tự động**. | User dùng SR bị redirect `/login?error=oauth` sau OAuth thất bại (luồng thật phase-16) sẽ **không nghe thấy** thông báo lỗi, dù `role="alert"` đúng cú pháp. Có thể verify bằng NVDA + Chrome thật (không kiểm được bằng curl vì đây là hành vi runtime của AT). |
| W2 | `lib/i18n/get-dictionary.ts:41-43` | `namespace: string` — không ràng buộc kiểu (không phải union `"common" \| "login" \| "common-ui" \| …`). Hiện **0 call site** gọi `getDictionary` với namespace khác `"common"` (`grep getDictionary` toàn repo chỉ có `app/layout.tsx` gọi 1-tham-số) — tham số `namespace` là đường mở, chưa ai đi qua, chưa có input xấu nào tới được nó. Nhưng vì kiểu là `string` trần, tương lai chỉ cần một dòng `getDictionary(locale, userInput)` là đủ để namespace nhận input người dùng mà `tsc` không cản. | Xem phân tích khai thác thực nghiệm ở mục 2 — **không dẫn tới đọc file ngoài `locales/`** nhờ cơ chế bundler (không phải nhờ code tự vệ), nên đây là rủi ro **thiết kế/maintainability**, không phải lỗ hổng khai thác được ngay bây giờ. Khuyến nghị: `type DictionaryNamespace = "common" \| "common-ui" \| "login"` (mở rộng dần theo phase) để `tsc` tự chặn namespace lạ tại compile-time, thay vì dựa vào "may mắn chưa ai gọi sai".

---

## Suggestion

| # | File:dòng | Ghi chú |
|---|---|---|
| S1 | `lib/i18n/get-dictionary.ts` (namespace param) | Tham số `namespace` tổng quát hoá xong nhưng **hiện không phase nào thực sự dùng qua `getDictionary`** — client components (`use-login-text.ts`, `use-common-ui-text.ts`) dùng cơ chế song song hoàn toàn khác (`useNamespaceTranslation` + import tĩnh JSON), **không đi qua `getDictionary`**. `login.json`/`common-ui.json` xuất hiện trong bundle server (xem mục 1) chỉ vì Turbopack liệt kê tĩnh mọi file khớp glob, không vì có Server Component nào gọi `getDictionary(locale, "login")` thật. Không phải lỗi — infra chuẩn bị sẵn cho tương lai (đúng mục đích bàn giao: "không phải sửa file mỗi khi thêm namespace") — nhưng nên ghi 1 dòng TODO/comment nói rõ "namespace hiện chưa có Server Component nào dùng ngoài `common`" để phase sau không tưởng nhầm đây là cơ chế đang chạy thật. |
| S2 | `plans/.../phase-07-ui-login.md:26` (acceptance) | Dòng "không import gì từ `lib/`" mâu thuẫn câu chữ với chính code đúng đắn: `login-screen.tsx` import `@/lib/i18n/locale-provider` và `@/lib/i18n/config` — là `lib/` thật. Việc code làm là **đúng** (i18n hạ tầng dùng chung là ý đồ phase-01), nhưng câu chữ acceptance quá rộng so với ý định thật (chỉ cấm `lib/supabase\|lib/data\|lib/actions`, đúng như lệnh `grep` verify đã dùng). Sửa câu chữ trong `phase-07-ui-login.md` để phase sau đọc không hiểu lầm. |
| S3 | `plans/.../phase-01-nen-tang-supabase-va-next.md` | File đã "Status: completed" với "Kết quả thực thi" mô tả `get-dictionary.ts` bản cũ (chỉ nạp `common`). Sau bàn giao này, mô tả đã lỗi thời so với code thật. Theo `documentation-management.md` (roadmap/changelog phải phản ánh đúng tiến độ thật) — nên thêm 1 dòng "Amendment" ngắn trong phase-01 trỏ sang phase-07 thay vì để độc giả sau đọc nhầm hành vi cũ. |
| S4 | `components/login/login-screen.tsx:16` | `onGoogleLogin: () => void` nhưng docblock nói phase-16 sẽ truyền hàm async (`signInWithGoogle` ném lỗi qua `throw`). TS cho phép gán `() => Promise<void>` vào `() => void` (quy tắc permissive có chủ đích của TS) nên không đỏ — nhưng `onClick={onGoogleLogin}` gọi trực tiếp nghĩa là promise trả về **không ai `.catch`**. Không phải lỗi của phase-07 (ngoài phạm vi, ghi rõ trong task), chỉ là điểm cần nhớ khi phase-16 nối dây thật: bọc `handleGoogleLogin` bằng try/catch hoặc `.catch()` ở nơi gọi, đừng để `signInWithGoogle`'s `throw` rơi thành unhandled rejection trong browser. |
| S5 | `public/login/Root_Further_Logo.png` | 13KB, 451×200, dùng đúng `next/image` với `width`/`height` khớp file thật (không méo, không CLS). Ổn, không cần nén thêm ở quy mô này. |

---

## Trả lời trực tiếp các câu hỏi "Soi kỹ"

### Hạ tầng i18n

**1) `import()` template literal — có phình bundle / rò namespace khác vào bundle không?**
Đã build thật và soi `.next/server/chunks/ssr/`. Turbopack tạo đúng như dự đoán của comment: **1 module "context" nhỏ** (`locales_0oh4yje._.js`, 876 byte) là bảng tra `(locale,namespace) → đường dẫn chunk`, KHÔNG nhúng nội dung JSON vào bảng đó. Mỗi file JSON (`locales_vi_login_json_..._cjs...js`, 334-915 byte/file) là **chunk riêng, nạp lười** — chỉ tải khi `import()` thực sự chạy với tham số đó lúc runtime. Đã grep `app/page.js` (route `/`) và **không thấy** tham chiếu chunk `login` — xác nhận nội dung `login.json` không rò vào route không liên quan. Đây là bundle **server-only** (file có `import "next/headers"` nên không thể lọt vào client bundle — Next sẽ build lỗi nếu ai cố import). Kết luận: comment của tác giả đúng, có bằng chứng thực nghiệm, không đánh đổi gì đáng kể ở quy mô hiện tại (36KB tổng `locales/`). Rủi ro thật duy nhất: bảng tra cứu này liệt kê **mọi** file khớp glob tại thời điểm build dù namespace đó có ai gọi hay không (xem S1) — không phải vấn đề bundle-size, mà là "infra generalize trước khi có người dùng".

**2) Path traversal qua `namespace`?**
Hiện tại **không có đường nào** từ input người dùng tới `namespace` — mọi call site đều truyền hằng chuỗi (chỉ 1 call site, mặc định `"common"`). Về mặt cơ chế: bảng tra cứu context-module là **cố định lúc build** (6 entry: {vi,en}×{common,common-ui,login}) — một namespace không nằm trong 6 entry đó (kể cả chuỗi có `../`) sẽ **không resolve được** ở runtime (không giống `fs.readFile` đọc trực tiếp đĩa theo path người dùng đưa). Vì vậy dù `namespace` không có ràng buộc kiểu (W2), việc "path traversal đọc file ngoài `locales/`" **không khả thi** với cơ chế `import()` hiện tại — khác hẳn rủi ro của bản `fs.readFile(process.cwd()+…)` cũ mà orchestrator đã chủ động tránh. Vẫn giữ W2 vì lý do khác: thiếu ràng buộc kiểu là nợ kỹ thuật, không phải lỗ hổng khai thác được ngay.

**3) Cache `Map` giữ `Promise` — rò bộ nhớ / race?**
Không rò: key gian là `locale:namespace`, bị chặn trên bởi số locale (2) × số namespace (tăng chậm theo phase, tối đa ~15-20) → tập hợp key hữu hạn nhỏ, sống suốt vòng đời process — đúng ý đồ cache. Nhánh `.catch` xoá cache khi lỗi **đúng** (cho phép thử lại nếu file JSON vừa được tạo/sửa). Race hai request đồng thời cùng key: `getDictionary` là hàm `async` nhưng **không có `await` nào** trong thân hàm trước dòng `dictionaryCache.set` — nghĩa là đoạn "đọc cache → tạo promise → ghi cache" chạy **đồng bộ trọn vẹn trong một lượt của event loop**, hai lời gọi không thể chen ngang nhau ở mức JS (Node đơn luồng). Không có race.

**4) `validateDictionary` chạy mỗi lần hay chỉ lần đầu?**
Chỉ lần đầu mỗi `(locale,namespace)`: cache lưu **Promise** (không phải giá trị), lần gọi sau trả thẳng promise đã settle, không re-import, không re-validate. Có cần thiết không: **có** — vì `import()` với path động khiến TypeScript không suy luận được shape JSON tĩnh (khác với `import` tĩnh có `resolveJsonModule`), nên đây là boundary check hợp lý cho nội dung JSON do phase khác thêm (một phase lỡ để giá trị nested object/number sẽ bị chặn ở lần nạp đầu thay vì lỗi runtime mơ hồ ở nơi dùng `t(key)`).

**5) Migrate `use-common-ui-text.ts` — hành vi đổi không? 8 component dùng `useCommonUiT()` có ảnh hưởng?**
Không đổi. Đối chiếu code cũ/mới: cùng logic `dictionary[key] ?? key`, cùng nguồn `locale` (qua `useLocale()`), chỉ chuyển từ code lặp lại sang gọi `useNamespaceTranslation()` dùng chung. Đã kiểm `SiteHeader` (dùng `useCommonUiT()` cho `nav aria-label`) — hoạt động đúng, không hồi quy (khớp với xác nhận `aria-label` LanguageSwitcher đã kiểm trong task).

**6) Cách gọn hơn cả hai phương án?**
Không. `import()` + cache Map + validate là gọn nhất cho bài toán ("nhiều namespace, không sửa file trung tâm mỗi phase, chạy được với `standalone`/serverless"). Phương án thay thế duy nhất đáng cân nhắc — bundler alias/glob tĩnh kiểu `import.meta.glob` — không tồn tại ở Next/Turbopack hiện tại (đó là API riêng của Vite). Giữ nguyên, chỉ nên bổ sung ràng buộc kiểu cho `namespace` (W2) chứ không cần đổi cơ chế.

### Phase-07

**7) `await searchParams` + validate `errorCode`?**
Đúng chuẩn Next 16 — đối chiếu `node_modules/next/dist/docs/.../page.md`: `PageProps<'/login'>` là helper toàn cục sinh kiểu từ route literal, `searchParams` là `Promise<{[key:string]: string | string[] | undefined}>`, phải `await`. Code khớp 100%. Validate: `params.error === "oauth" ? "oauth" : undefined` là **allow-list nghiêm ngặt** (so sánh bằng chuỗi chính xác, không dùng regex/includes) — đã tự chạy `curl` với payload `?error=<script>alert(1)</script>`: kết quả **0 match** `role="alert"`, không có chuỗi payload phản chiếu vào HTML trả về. `?error=oauth` hợp lệ: alert render đúng, đã `curl` xác nhận cả tiếng Việt. Trường hợp `?error=oauth&error=oauth` (mảng) tự động rơi về `undefined` an toàn (so sánh strict với string thất bại trên array) — không crash.

**8) Boundary Client Component có cần thiết? `onGoogleLogin` placeholder có ổn không?**
Cần thiết — lý do nêu trong docblock (`login-page-client.tsx:9-17`) đúng: React Server Components không cho truyền hàm thường (khác Server Action) từ Server xuống Client Component qua props, nên cần một boundary Client Component định nghĩa handler tại chỗ. Về việc để placeholder dù `lib/auth/sign-in-with-google.ts` đã tồn tại từ phase-03: đây là **lựa chọn đúng**, không phải thiếu sót — chính acceptance criteria của phase-07 (`plans/.../phase-07-ui-login.md:26`) ghi rõ "không import gì từ `lib/`" (ý đồ thật: không import `lib/supabase|data|actions` — xem S2). Nối dây thật ở đây sẽ vi phạm ranh giới track (`Track A` không phụ thuộc `Track B`) mà chính plan đã thiết kế để 2 track chạy song song không khoá nhau. Giữ nguyên.

**9) Accessibility: label nút, alert, alt ảnh, contrast?**
- Nút: text hiển thị "LOGIN With Google" + SVG `aria-hidden="true"` → accessible name rõ, không cần `aria-label` thêm. Có `focus-visible:outline`.
- Alert: có `role="alert"`, KHÔNG có thêm `aria-live` — đúng, vì `role="alert"` **ngầm định** `aria-live="assertive"` (thêm `aria-live` là dư thừa). Nhưng xem **W1**: vấn đề là *thời điểm* alert xuất hiện (SSR ban đầu), không phải thiếu thuộc tính ARIA.
- Ảnh: `alt={t("hero.title")}` = "ROOT FURTHER" — hợp lý (logo có nghĩa, không phải ảnh trang trí).
- Contrast: nút nền `#FFEA9E` chữ `#00101A` — tính theo công thức WCAG (luminance sRGB): tỉ lệ **~17.7:1** — vượt xa ngưỡng AA (4.5:1 text thường, 3:1 UI component/large text) và cả AAA (7:1). Đạt, dư sức.

**10) Nền hero thay thế — mức lệch thiết kế?**
Chấp nhận được. Docblock (`login-screen.tsx:20-28`) ghi rõ lý do (API Figma trả 500 hai lần), và bản thay thế dùng đúng 2 lớp gradient thật từ Figma (`662:14392`, `662:14390`) phủ trên nền đặc cùng tông `#00101A` — không lệch bố cục/layout, chỉ thiếu chi tiết hoạ tiết sóng trang trí. Đã ghi chú theo dõi bổ sung khi Figma export lại được — đúng quy trình, không phải bỏ sót âm thầm.

**11) Logo — kích thước & `next/image`?**
Dùng `next/image` (không phải `<img>` trần) — đúng chuẩn, được tối ưu (lazy/priority, srcset tự động). `width={451} height={200}` khớp chính xác kích thước file thật (đã `file` xác nhận `451x200`) → không méo ảnh, không lệch aspect ratio. 13KB — hợp lý cho một logo/hero graphic ở kích thước này.

### Chung

**12) File ownership**
Không chạm gì ngoài phạm vi khai báo. Diff/untracked khớp đúng: `app/login/**`, `components/login/**`, `locales/*/login.json`, `public/login/**` (ownership phase-07) + `lib/i18n/get-dictionary.ts`, `lib/i18n/use-namespace-translation.ts`, `components/ui/use-common-ui-text.ts` (bàn giao phase-01/06, có ghi chú rõ trong code). Không có file nào bị sửa ngoài danh sách này.

**13) YAGNI/KISS/DRY**
Tuân thủ tốt: hook `useNamespaceTranslation` dùng chung đúng tinh thần DRY (thay vì 9 hook gần giống nhau như lo ngại ban đầu). Riêng S1 là điểm generalize sớm hơn nhu cầu thật (namespace param chưa ai dùng qua `getDictionary`) — nhẹ, chấp nhận được vì chi phí thấp và đúng mục tiêu tránh sửa file trung tâm.

---

## Edge Cases đã soi thêm (ngoài diff)
- `searchParams.error` là mảng (`?error=oauth&error=oauth`) → an toàn, rơi về `undefined`.
- Payload XSS trong query `?error=<script>...` → đã `curl` thật, không render, không phản chiếu.
- Race 2 request đồng thời cùng namespace → không có (đã phân tích luồng đồng bộ trong `getDictionary`).
- Route `/` (không liên quan `/login`) có bị kéo theo chunk `login.json` không → đã grep `.next/server/app/page.js`, không có.
- Build thật (`npm run build`) exit 0, `tsc --noEmit` exit 0, `eslint` trên các file thay đổi exit 0 (chạy lại độc lập, không chỉ tin lời khai).

## Đã làm tốt
- Quyết định `import()` thay `fs.readFile(process.cwd()+…)` đúng, có lý do kỹ thuật vững (đã verify bằng build thật, không chỉ suy đoán).
- Cache Map + xoá cache khi lỗi + validate boundary — thiết kế chỉn chu cho một bài toán nhỏ, không thừa không thiếu.
- Comment code giải thích rành mạch *tại sao*, không chỉ *làm gì* — đúng tinh thần "comment ở chỗ không hiển nhiên".
- `login-screen.tsx` xử lý allow-list `errorCode` nghiêm ngặt, không có lỗ injection.
- Giữ đúng ranh giới Track A/Track B (không import `lib/auth` dù đã có sẵn) — kỷ luật tốt, tránh nợ kỹ thuật ngầm.

## Thứ tự hành động
1. (Warning) Sửa vấn đề công bố alert cho trình đọc màn hình (W1) — cân nhắc focus lập trình vào alert hoặc trễ một tick trước khi mount để kích hoạt live-region đúng cách. Nên làm trước khi nối OAuth thật ở phase-16.
2. (Warning) Ràng buộc kiểu cho `namespace` trong `getDictionary` (W2) — union type thay vì `string` trần, chặn từ compile-time.
3. (Suggestion) Sửa câu chữ acceptance phase-07 (S2) và ghi chú tại phase-01 (S3) để tránh hiểu lầm cho phase sau.
4. (Suggestion) Ghi chú TODO namespace chưa dùng thật (S1); nhắc phase-16 bọc try/catch quanh `onGoogleLogin` async thật (S4).

## Số liệu
- `tsc --noEmit`: exit 0
- `eslint` (file thay đổi): exit 0
- `npm run build`: exit 0 (Turbopack, 168ms compile)
- Test suite: không áp dụng (repo chưa có test runner — phase-17)
- Lint/type findings: 0

## Còn để ngỏ
- W1 cần kiểm bằng trình đọc màn hình thật (NVDA/VoiceOver) — không kiểm được bằng `curl`/`tsc`, chỉ suy luận từ hành vi ARIA chuẩn.
- Đăng nhập Google thật (E2E) chưa chạy — đúng như clarifications.md đã ghi, ngoài phạm vi phase-07.
