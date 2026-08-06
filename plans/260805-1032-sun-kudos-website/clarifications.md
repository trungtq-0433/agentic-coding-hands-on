# Clarifications — Sun* Kudos website

Nguồn gap: `reports/researcher-260805-1032-momorph-requirements-synthesis.md` §7.
Định dạng: một dòng một quyết định. Đây là nguồn chân lý — không hỏi lại những mục đã chốt ở đây.

## Session 2026-08-05

### Gate quyết định phạm vi
- Q: Bật SDD mode (spec layer `docs/features/F###`)? → A: **Off** — đã có spec thật từ MoMorph, thêm tầng spec nữa là trùng việc. Lưu `.claude/.tkm.json`.
- Q: Ngôn ngữ plan + tài liệu sinh ra? → A: **Tiếng Việt** — spec/domain gốc tiếng Việt, tránh sai lệch thuật ngữ khi dịch.

### Từ report inventory (đã trả lời trước đó)
- Q: Filter `pages=2324` trên UI có khớp 18 màn non-`[iOS]`? → A: **Khớp**.
- Q: `_hphd32jN2` (FAB 1) có bị `Sv7DFwBw1h` (FAB 2) thay thế? → A: **Dùng cả 2**.
- Q: Homepage SAA design còn `in_progress` — chờ chốt hay code theo bản hiện tại? → A: **Code theo bản hiện tại**.
- Q: Supabase local-only hay tính luôn hosted? → A: **Local dev thôi** — không migration/CI lên hosted.

### Gap BLOCKING
- Q: Gap #1 — nguồn target datetime cho countdown (Homepage nói env var, Prelaunch ghi TODO API)? → A: **Chỉ env var cho cả hai** — không dựng bảng `event_config`. Suy ra: 2 biến độc lập `NEXT_PUBLIC_LAUNCH_GATE_AT` (Prelaunch gate) + `NEXT_PUBLIC_EVENT_START_AT` (Homepage). **Đổi ngày = sửa `.env` RỒI CHẠY LẠI `next build`** — biến `NEXT_PUBLIC_*` bị inline vào bundle lúc build, restart process là KHÔNG đủ (`node_modules/next/dist/docs/01-app/02-guides/environment-variables.md:166`). *Sửa 2026-08-05 sau Red Team #5: dòng này trước ghi "sửa `.env` + restart" — sai.* Runbook ở `phase-01` và `docs/runbook-su-kien.md`.
- Q: Gap #2 — login thành công redirect đi đâu (spec ghi `/todo` placeholder)? → A: **Về Homepage `/`** — khớp "main application page" trong TC.
- Q: Gap #4 — "tên ẩn danh" là field tự nhập hay nhãn cố định? → A: **Nhãn cố định, bỏ field tự nhập** — khớp "masked-alias placeholder" trong TC Profile, chặn rủi ro giả danh. Kéo theo: bỏ text field ở spec Viết Kudo item G; cột `kudos.anonymous_alias` không cần.
- Q: Gap #5 — hashtag/phòng ban là danh sách cứng hay DB? → A: **Bảng DB, seed từ danh sách cứng trong spec, chưa có admin CRUD ở MVP**.
- Q: Gap #3 — mục "Admin Dashboard" trong menu admin (spec tự ghi TODO, route chưa có)? → A: **Làm trang placeholder "Coming soon"** — giữ mục menu để TC ID-5/ID-37 pass, route `/admin` có role guard.

### Gap IMPORTANT
- Q: Gap #6 — Live board cần realtime hay polling? → A: **Supabase Realtime (Postgres Changes) trên `kudos` + `hearts`**.
- Q: Gap #7 — "Hero tier" badge (chỉ có trong 1 ghi chú TC, thiếu tên tier + ngưỡng)? → A: **Bỏ khỏi MVP** — giữ hoa-thị (ngưỡng đã rõ 10/20/50 tổng kudos). Ghi thành follow-up.
- Q: Gap #9 — quy tắc CẤP secret box (không có trong spec/TC nào)? → A: **Seed dữ liệu demo, defer rule thật** — build đủ luồng MỞ hộp + bảng `secret_box_grants`, không bịa cơ chế earn.

### Quyết định mặc định (agent chốt theo khuyến nghị report, không hỏi)
Các mục dưới đây report đã có khuyến nghị rõ và không đổi kiến trúc — chốt theo mặc định, nói ra để mày phản đối được nếu sai:
- Gap #8 — ngày đặc biệt (heart bonus): bảng `special_days` + cờ `hearts.is_special_day_bonus` quyết định lúc INSERT, dùng lại lúc thu hồi. Không có UI admin ở MVP → seed tay.
- Gap #10 — 6 hạng mục giải (Hệ thống giải): **nội dung tĩnh** (constant/JSON trong repo), không bảng DB — không có màn admin nào quản lý nó.
- Gap #11 — ai bypass được Countdown Prelaunch: **không ai** — chặn tất cả, đúng mục đích prelaunch gate.
- Gap #12 — i18n cho nội dung user tạo (body kudo): **giữ nguyên như user gõ**, không dịch máy.
- Gap #13 — bộ đếm "388 KUDOS" + word-cloud: query lúc tải trang, không realtime.
- Gap #16 — slug cho award anchor: `kebab-case(title)`.

### Đã được spec chốt sẵn — không cần hỏi
- Auth: **Google OAuth, một nút duy nhất, MỌI tài khoản Google đều được phép** (spec Login item 2.2.1, tường minh). Không có email/password, không giới hạn domain.
- i18n: đúng **2 ngôn ngữ VN + EN**, lưu ở cookie `NEXT_LOCALE` (spec Login 1.2).
- Timezone countdown: `Asia/Ho_Chi_Minh` (UTC+7).
- Ràng buộc `kudos.sender_id != recipient_id` — TC_WEB_PROFILE_FUN_008 xác nhận.

## Session 2026-08-05 (bổ sung sau Red Team Review)

Nguồn: 15 finding từ 4 reviewer thù địch, user duyệt từng cái. Bảng đầy đủ ở `plan.md` mục `## Red Team Review`.

- Q: `revoke select on kudos` (chặn rò ẩn danh) và Realtime Postgres Changes loại trừ nhau — bỏ cái nào? → A: **Giữ `revoke`, đổi realtime sang Broadcast phát từ trigger**, payload chỉ mang `kudos_id`. An toàn thắng tiện lợi. (Red Team #3, 2 reviewer độc lập cùng bắt)
- Q: Có nên dựa vào policy `with check` thay cho `revoke` quyền ghi trực tiếp? → A: **Không** — `revoke insert/update/delete` trên `kudos`, `kudos_hashtags`, `kudos_images`, `hearts`. Policy chỉ xác thực *ai ghi*, không xác thực *ghi cái gì*; mọi luật nghiệp vụ sống trong RPC. (#1, #2)
- Q: `is_special_day_bonus` lấy từ đâu? → A: **RPC `toggle_heart` tự tra `special_days`**, không có tham số nào cho client truyền vào. (#2)
- Q: Bảng `kudos_mentions` có giữ không? → A: **Bỏ khỏi MVP** — ghi mà không màn nào đọc. `@mention` sống trong `body` dạng text. (#15)
- Q: Test suite 1 phase hay chẻ nhỏ? → A: **Giữ 1 phase, effort 5h → 14h** (ước lượng đầu bỏ sót việc dựng hạ tầng test từ số không). (#14)

### Bổ sung sau thực thi phase-01 (2026-08-05)
- **Tên biến env lệch**: plan ghi `NEXT_PUBLIC_SUPABASE_ANON_KEY`, CLI Supabase local in ra cả `PUBLISHABLE_KEY` (tên mới, `sb_publishable_…`) và `ANON_KEY` (JWT legacy). Thực tế dùng **`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`**. Phase-02/03/04 phải dùng tên này.
- **npm script**: CLI Supabase không ở `node_modules/.bin`, phải dùng `npx supabase`, không gọi `supabase` trần.
- **`npm run lint` ĐỎ toàn repo (exit 1, 866 lỗi)**: do `.claude/hooks/*.cjs` của kit Takumi (từ trước phase-01). Code phase-01 lint sạch. Giải pháp: thêm `.claude/**`, `plans/**` vào `globalIgnores` trong `eslint.config.mjs`. File này chưa thuộc ownership phase nào — cần quyết định sở hữu. **Chặn phase-17 (npm run validate tester dùng)**.
- **`app/prelaunch/` 404**: Đúng design, thuộc phase-14. Kiểm tra route khác phải ở gate ở quá khứ.

## Còn treo (không chặn MVP)
- **✅ Đăng nhập Google end-to-end ĐÃ VERIFY THẬT** (2026-08-06, trình duyệt thật, tài khoản thật).
  Hai tài khoản đăng nhập thành công: `tran.quang.trung@sun-asterisk.com` và **`tqtrung09@gmail.com`
  — Gmail NGOÀI domain**, chứng minh spec "mọi tài khoản Google đều được phép" chạy đúng ngoài đời,
  không chỉ với user giả tạo qua admin API. Trigger `handle_new_user` tạo đúng 1 hàng `profiles` +
  1 hàng `user_roles` (role `user`) cho mỗi người, chép được `full_name` + `avatar_url` từ metadata
  Google. `/profile` trả 404 sau khi login (route guard cho qua) và 307 khi chưa login — session thật.
  `avatar_url` về từ `lh3.googleusercontent.com`, khớp đúng `images.remotePatterns` mà phase-01 khai.
  **Còn lại chưa kiểm:** avatar chưa được RENDER ở đâu (chưa màn nào hiển thị), nên `next/image` chưa
  thực sự chạy với host đó — chỉ mới chứng minh cấu hình khớp dữ liệu thật.
- **Lỗi đã sửa khi demo (2026-08-06):** `supabase/config.toml` mặc định của CLI có
  `site_url = "http://127.0.0.1:3000"` và `additional_redirect_urls = ["https://127.0.0.1:3000"]`
  (https, không chứa app). GoTrue thấy `redirect_to` ngoài allow-list thì **rơi về `site_url` và vứt
  luôn path** → sau khi login về `http://127.0.0.1:3000/?code=...` thay vì `/auth/callback?code=...`,
  nên `exchangeCodeForSession` không bao giờ chạy và không có session nào được tạo. Đã đổi thành
  `site_url = "http://localhost:3000"` + allow-list `http://localhost:3000/**` và
  `http://127.0.0.1:3000/**`. **Lưu ý:** GoTrue KHÔNG coi `localhost` và `127.0.0.1` là một, và `/**`
  là bắt buộc vì app redirect về `/auth/callback` chứ không về gốc. Dev phải chạy ở **cổng 3000**.
- **StrictMode double-mount + `enabled=false` của hook realtime**: thật chưa kiểm (cần React runtime + component thật, phase-16).
- **5 chỗ UI phải suy đoán** vì Figma không có frame: trigger đóng FilterDropdown, hover/disabled mọi dropdown, trạng thái lỗi AddLinkDialog, icon cờ VN/EN, 3 component không screenId.
- Hero tier: cần designer cấp tên tier + ngưỡng + icon.
- Rule cấp phát Secret Box: cần PO chốt. **Đường tạm:** RPC `admin_grant_secret_box()` + runbook cấp tay (phase-02) — đủ để sự kiện không chết giữa chừng khi hết hộp. (#7)
- Nội dung/trigger cụ thể của notification bell (gap #14) — định nghĩa lúc implement, ưu tiên "nhận kudos mới".
- Màn Admin Dashboard thật: cần batch spec riêng.
- **`PAO - PAO` trong danh sách phòng ban nguồn** — mục thứ 50, một phòng ban con trùng tên cha (`PAO` là mục 33). Gần như chắc chắn lỗi nhập liệu bên soạn spec. Vẫn seed đủ 50 kèm `FIXME`, chờ người soạn spec xác nhận gộp hay sửa tên. (capped finding)
- **8/18 file test case rỗng hoàn toàn 0 byte** (mọi dropdown + cả 2 FAB) — nhóm component dùng chung của phase-06 không có TC gốc để bám, test phải suy từ spec. Nếu QA bổ sung TC sau, rà lại phase-17. (capped finding)

## Session 2026-08-05 (Sau thực thi phase-03)

Các ràng buộc kiến trúc phát sinh từ implementation, phục vụ phase-04/16 và track A:

- **Hai file env, tuyệt đối không nhầm:**
  - `.env` — dùng bởi **CLI Supabase** (`supabase/config.toml` đọc qua `env()`). Chứa `SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID`, `SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET`. **Giá trị thật ở đây.**
  - `.env.local` — dùng bởi **Next.js**. Chứa `NEXT_PUBLIC_SUPABASE_*`, `NEXT_PUBLIC_*_AT` — **KHÔNG** chứa credential Google. **Để trống template, copy từ `.env` lúc setup.**

- **`redirect_uri` trong `config.toml` phải khai tường minh** `http://localhost:54321/auth/v1/callback` — để trống là GoTrue suy `127.0.0.1` khác với `localhost` đã đăng ký trên Google Console → OAuth mismatch reject.

- **Mọi redirect mới trong `proxy.ts`** phải dùng helper `redirectKeepingSession()` chứ không `NextResponse.redirect()` trần — lỗi Critical đã xảy ở phase-01, đừng lặp lại.

- **`seed.sql` phải giữ `ON CONFLICT`** trên `profiles` + `user_roles` miễn là trigger `handle_new_user` còn tồn tại — seed tự INSERT profile/roles, trigger cũng tạo, không conflict = npx db reset lỗi rollback, DB rỗng.

- **Phase sau (04/11/16 khi gọi `requireUser()`/`requireAdmin()`):** gọi trong **page.tsx / Server Action**, KHÔNG gọi trong layout — Next 16 Partial Rendering sẽ bỏ lọt kiểm soát từ layout, chỉ page được re-render. Quy ước: Guard logic ở tầng application (page/action), không middleware/layout.

## Ràng buộc phát sinh từ phase-02 (đọc trước khi code Track A / phase-11 / phase-16)

- **`select('*')` trên bảng `profiles` sẽ LỖI 42501.** `sent_kudos_count` bị loại khỏi grant
  bằng column-level grant vì nó cộng cả kudos ẩn danh — để công khai là suy ra được
  `số_ẩn_danh(X) = sent_kudos_count(X) − count(feed where sender_id = X)`, đo trên seed khớp
  100%. Mọi query `profiles` phải **liệt kê cột tường minh**:
  `id, full_name, avatar_url, department_id, received_kudos_count, received_hearts_count, created_at`.
  Chính chủ muốn biết số đã gửi thì đếm từ `my_sent_kudos`. (Red Team phase-02, Critical #1)
- **Không query thẳng bảng `kudos`** — đã revoke toàn bộ quyền với anon/authenticated.
  Đọc feed qua view `public_kudos_feed`, đọc sent-list qua `my_sent_kudos`.
- **Không ghi thẳng `kudos` / `kudos_hashtags` / `kudos_images` / `hearts`** — chỉ SELECT.
  Mọi ghi đi qua RPC của phase-04.
- **Realtime dùng Broadcast, KHÔNG dùng Postgres Changes.** Topic `kudos-board` và
  `user-hearts:<user_id>`; payload chỉ mang id. Đã kiểm `realtime.send()` tồn tại và trigger
  phát thật trên bản Supabase CLI hiện tại — gỡ được 2 mục unresolved của plan.

### Credential Google OAuth — chỗ đặt, và cái bẫy .env vs .env.local

Secret cũ từng bị dán vào `plan.md` và lọt vào git; GitHub secret scanning chặn push, đã xoay
key và scrub lịch sử bằng `git filter-repo --replace-text`. **Không bao giờ dán giá trị
credential vào file trong `plans/` hay `docs/`.**

Có HAI file env, hai người tiêu thụ khác nhau — đây là chỗ dễ mất buổi chiều:

| File | Ai đọc | Biến |
|---|---|---|
| `.env.local` | **Next.js** | `NEXT_PUBLIC_SUPABASE_*`, `NEXT_PUBLIC_*_AT` — **KHÔNG** chứa credential Google |
| `.env` | **CLI Supabase** (thay thế `env()` trong `supabase/config.toml`) | `SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID`, `SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET` |

Đã kiểm chứng bằng thực nghiệm (đặt biến dò vào `.env`, `supabase stop && start`, đọc env của
container): CLI **có** đọc `.env`, và **không** đọc `.env.local`. Cả hai file đều đã gitignore;
template tương ứng là `.env.example` và `.env.local.example`.

**phase-03 phải làm:** bật `[auth.external.google]` trong `supabase/config.toml` với
`client_id = "env(SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID)"` và
`secret = "env(SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET)"` — đúng khuôn mẫu mà chính config.toml
đã dùng cho các provider khác. **Tuyệt đối không ghi giá trị literal vào config.toml**, file đó
được commit. Redirect URI đã đăng ký sẵn trên Cloud Console:
`http://localhost:54321/auth/v1/callback` (cổng **Supabase**, không phải cổng Next).

## Session 2026-08-05 (Sau phase-04/05/06 thực thi)

### Ràng buộc bảo mật từ phase-04/05/06

- **Cursor keyset PHẢI validate định dạng ISO-8601** trước khi ghép vào filter PostgREST. Input từ URL là thù địch. Regex strict: `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`.
- **`fetchKudoCardById` ở `lib/realtime/`**, KHÔNG `lib/data/`** — vì nó cần chạy ở client (hook), `kudos-queries.ts` dùng server client (`next/headers`). Phase-16 import từ `lib/realtime/fetch-kudo-card.ts`.
- **Bộ lọc phòng ban lọc theo phòng ban NGƯỜI NHẬN**, không người gửi. Phải xử lý `department_id IS NULL` thành nhóm "Chưa phân loại" (mọi user đăng nhập thật đều NULL). Không sửa view phase-02, xử lý ở `listDepartments()` + `listKudos(departmentId='unassigned')`.
- **Đọc feed CHỈ qua `public_kudos_feed` + `my_sent_kudos`**; ghi CHỈ qua 3 RPC. Đọc thẳng `kudos` = lỗi bảo mật (revoke ở phase-02).
- **`ModalShell` là chrome dùng chung** — `components/layout/modal-shell.tsx` chỉ backdrop/Esc/focus trap/scroll-lock. Phase-10/13/15 song song compose nội dung, KHÔNG tự dựng chrome (3 phase tự dựng = 3 Esc-listener đá nhau).

### Deviations (cấu trúc, không phải lỗi)

- **`computeStarCount` trùng ở 2 chỗ**: `lib/kudos/star-count.ts` (phase-04) và bản private `lib/auth/dto.ts` (phase-03). Cố ý không gộp vì ownership khác. Nợ phase-18+.
- **`listRecentRankUps()` là xấp xỉ** — no history table, proxy `received_kudos_count >= 10` sort desc. Toàn là demo.
- **`ModalShell` bỏ `createPortal`** — `fixed inset-0` đủ, nhưng sẽ hỏng nếu parent có `transform`/`filter` CSS. Chấp nhận giới hạn đó.
- **`public_kudos_feed` KHÔNG có cột `recipient_department_id`** → lọc phòng ban: lấy `recipient_id` → join `profiles` để lấy `department_id` → filter. Không sửa view phase-02.
- **`SiteHeader`/`SiteFooter`/`CountdownTimer` không có Figma screenId** — style suy từ token 9 màn khác, cần designer duyệt. Chấp nhận là component chung.

## Session 2026-08-06 (Sau phase-07 UI Login)

### i18n Namespace — Ràng buộc mới

- **Thêm namespace locale mới:** tạo file `locales/{vi,en}/<namespace>.json` với 5+ key. Không sửa `lib/i18n/get-dictionary.ts` lần nữa — loader đã tổng quát.
- **Client component dùng hook:** `const t = useNamespaceTranslation('<namespace>')` → `t('key')`. Hook nằm ở `lib/i18n/use-namespace-translation.ts` (phase-07 phát hành).
- **Server Component dùng dictionary:** `const dict = await getDictionary(locale, '<namespace>')` → `dict.key`. Hàm ở `lib/i18n/get-dictionary.ts` tham số `namespace` tùy chọn, fallback `'common'`.
- **Generality forward-looking:** tham số `namespace` ở `getDictionary` chưa có caller nào dùng (chỉ phase-07 nên nó được sinh). Giữ lại vì phase-14/15 (trang tĩnh) nhiều khả năng cần server-side dictionary, nhưng ghi rõ: chưa dùng, không phải nợ.
- **Path bundler bảo vệ:** `import.meta.resolve` / `@bundler:locales` template literal chỉ gói `locales/*/*.json`, đường dẫn lạ thất bại lúc chạy. Không khai thác được (kiểm qua curl `../../` + `<script>`).
- **Phase-01 sở hữu nhưng chỉnh sửa tuần tự:** nếu phase sau muốn sửa `lib/i18n/**` phải qua cùng khuôn "bàn giao kiểm soát" (1-2 dòng import/interface mới, không phình file hơn 5 dòng), ghi vào phase file và cập nhật ghi chú amendment này.

## Session 2026-08-06 (Sau phase-08 UI Homepage)

### Bản thiết kế Homepage tự mâu thuẫn — 4 chỗ, đã chốt cách xử lý

Màn `i87tDx10uM` còn `in_progress`, quyết định cũ là "code theo bản hiện tại". Bốn chỗ dưới đây
**không thể chép nguyên văn** vì chép là tạo lỗi, nên đã lệch có chủ đích và cần người soạn thiết kế xác nhận:

- **3/6 mô tả thẻ giải TRÙNG NHAU.** Best Manager, Signature 2025 - Creator và MVP dùng chung câu
  "Vinh danh người quản lý có năng lực quản lý tốt, dẫn dắt đội nhóm". Mô tả của Top Project Leader
  thì kết thúc bằng dấu phẩy cụt. → **Chép nguyên văn** (đúng "code theo bản hiện tại") kèm `FIXME`
  trong `components/home/figma-award-mock.ts`. Cần 3 mô tả thật.
- **Chữ "Comming soon" sai chính tả** trong Figma (node `2167:9036`). → Viết đúng thành
  "Coming soon". Lệch 1 ký tự so với bản vẽ, nhưng đưa lỗi chính tả lên production tệ hơn.
- **Footer đánh dấu "Award Information" là mục ĐANG CHỌN** trong khi header đánh dấu "About SAA 2025"
  — hai chỗ mâu thuẫn trên CÙNG một trang. → Không chép trạng thái chọn ở footer;
  `aria-current="page"` đặt lên link trỏ đi trang khác là sai ngữ nghĩa.
- **Ngày sự kiện hiển thị `26/12/2025`** (chuỗi tĩnh trong Figma) trong khi
  `NEXT_PUBLIC_EVENT_START_AT` = `2025-12-20T18:00:00+07:00`. **Lệch 6 ngày, hai nguồn độc lập.**
  Countdown đếm theo env, chữ hiển thị theo Figma → có thể về `00` trong khi vẫn ghi "26/12". Cần
  chốt một nguồn duy nhất trước khi chạy thật.

### Font chữ số countdown — chưa có, đang dùng bản thay thế

Figma khai font `"Digital Numbers"` (LCD 7 đoạn) cho ô số. Font này **không có trên Google Fonts và
không có trong hệ thống** (đã `fc-list`: chỉ có `KacstDigital`, font Ả Rập, không dùng được).
→ Tạm dùng `Share_Tech_Mono`, chọn vì monospace nên chữ số không nhảy ngang khi đếm — tiêu chí quan
trọng hơn hình dáng glyph. Khai cục bộ trong `components/home/countdown-digits.tsx`, đổi font chỉ
cần sửa đúng chỗ đó. **Cần designer cấp file font + license.**

### Ba cái bẫy kỹ thuật đã trả giá để tìm ra (đừng lặp lại)

- **`overflow-x-hidden` + con `z` âm = nền biến mất.** CSS quy định khi một trục `overflow` là
  `hidden` còn trục kia `visible` thì trục `visible` bị tính lại thành `auto` — phần tử thành vùng
  cuộn, và Chromium sơn nền vùng cuộn ĐÈ LÊN các con z âm. Ảnh vẫn load, `opacity:1`, đúng kích
  thước, chỉ là không bao giờ thấy. Mất khá lâu vì mọi thuộc tính đọc ra đều đúng. `/login` dùng
  cùng khuôn z âm mà không dính vì nó `overflow-hidden` CẢ HAI trục. → Đừng đặt `overflow-x-hidden`
  lên thẻ vừa có nền vừa chứa con z âm.
- **`shadow-[0_4px_4px_0_rgba(0,0,0,0.25),0_0_6px_0_#FAE287]` của Tailwind v4 không dựng ra gì.**
  Giá trị nhiều lớp có dấu phẩy bên trong `rgba()` bị lớp arbitrary bỏ qua; `getComputedStyle` trả
  `rgba(0,0,0,0) 0px 0px 0px 0px`, tức bóng mất sạch mà **không có lỗi build nào**. → Bóng nhiều lớp
  viết `style={{ boxShadow: ... }}` inline.
- **`useMemo` với dep là hàm từ hook i18n luôn trượt.** `useNamespaceTranslation` trả arrow function
  mới mỗi render → `[t]` luôn khác → memo không bao giờ trúng. Đã gỡ.

### Đọc số đo Figma: hai chỗ thuộc tính khai KHÁC bố cục thật

- **`gap` + `justify-content: space-between` → khoảng cách thật KHÔNG phải `gap`.** Lưới thẻ giải
  khai `gap: 80px` nhưng toạ độ cho thấy 108px (thẻ 1 đóng x=480, thẻ 2 mở x=588); và
  3×336 + 2×108 = 1224 khớp đúng bề ngang khối. `gap` chỉ là mức tối thiểu. **Luôn kiểm bằng toạ độ.**
- **`padding` khai nhưng không bó nội dung.** `Frame 486` (Root Further) khai `padding: 120px 104px`,
  nhưng con của nó đặt TUYỆT ĐỐI và phớt lờ: node chữ trải đủ 1152px (không thụt 104px), `Group 434`
  nằm ở y=881 — CAO HƠN mép trên frame (899). Frame khai height 1219 trong khi nội dung cao 1256,
  tức nội dung tràn khỏi khung. Áp padding ngang → khối cao dư ~470px; áp thêm padding dọc → dư ~280px.
  Bỏ cả hai → tổng trang **4479px so với bản vẽ 4480px**.

### Bàn giao kiểm soát sang file của phase khác (4 file)

- `components/ui/fonts.ts` (phase-06): Montserrat `["700"]` → `["400","500","700"]`. Homepage dùng 400
  (tiêu đề + mô tả thẻ giải) và 500 (nút "Chi tiết"). `next/font/google` CHỈ sinh `@font-face` cho
  weight được liệt kê — thiếu thì CSS vẫn đúng nhưng trình duyệt phải suy ra từ 700, chữ dày sai mà
  không báo lỗi.
- `components/ui/countdown-timer.tsx` (phase-06): tách `useCountdownRemaining(targetIso, tickMs)` +
  export `RemainingParts`. `CountdownTimer` giữ nguyên props/markup. Homepage dùng lại logic đếm với
  giao diện ô số hoàn toàn khác — chia hook thay vì nhồi variant vào component cũ.
- `components/layout/site-footer.tsx` (phase-06): thêm prop `logo`, nhóm trái (logo → nav → slot)
  đứng trước dòng bản quyền. Footer Homepage có logo 69×64 + 4 mục nav; footer Login chỉ có bản quyền
  căn giữa — cùng component Figma, hai cách dùng. `hasSides` sai → giữ nguyên hành vi màn Login.
- `components/layout/site-header.tsx` (phase-06): `h-20` → `min-h-20`. Chiều cao cố định làm nav xuống
  dòng ở 375px tràn ra ngoài hộp và **đè lên chữ hero**.

### Quyết định không có trong Figma (màn này không có khung mobile)

- **Header chỉ PHỦ từ `lg` trở lên**, dưới `lg` nằm trong luồng và đẩy nội dung xuống. Bản vẽ chỉ tồn
  tại ở khung 1512px nơi header vừa đúng một hàng 80px.
- **Trạng thái khách**: Figma chỉ vẽ trạng thái đã đăng nhập (avatar + menu). Acceptance phase-08 yêu
  cầu guest xem được toàn bộ nội dung → chỗ `AccountMenu` đổi thành lối vào `/login`.
- **"Tiêu chuẩn chung"** (mục nav thứ 4 ở footer) không có route trên bản vẽ → nối vào `onRules`
  (modal Thể lệ, phase-13), cùng đích với nút "Thể lệ" trên FAB. Render thành `<a href>` là link chết.

### Điểm nối dây của phase-16 (grep `phase-16` trong `components/home/home-page-client.tsx`)

Còn lại: `onCompose` / `onRules` — modal Viết Kudo (phase-10) và Thể lệ (phase-13) chưa tồn tại,
nút bấm được, FAB thu gọn lại, chưa có gì mở ra. **Không dựng modal giả**: phase-06 đã chốt
`ModalShell` là chrome dùng chung.

**Phần auth đã KÉO SỚM, không còn chờ phase-16 nữa (2026-08-06).** Ban đầu `profile = null` /
`isAdmin = false` được truyền cứng đúng theo ranh giới Track A/B. Nhưng `proxy.ts` của Track B đã
chạy từ phase-03 và nó đọc **cookie thật** — nên trang có HAI nguồn sự thật ngược nhau về "đã đăng
nhập chưa": người đã đăng nhập bị `/login` đá về `/`, mà `/` vẫn vẽ nút "Đăng nhập", bấm vào thì
quay lại chỗ cũ — kẹt vòng, và không có đường đăng xuất vì menu tài khoản không bao giờ render.

→ `app/page.tsx` giờ đọc phiên thật qua `getCurrentProfile()` + `isCurrentUserAdmin()` và truyền
`signOutAction` (Server Action — đây là lý do nó xuống được Client Component, function thường thì
Next chặn). **Hệ quả về plan:** `app/page.tsx` đã chạm cả hai track, sớm hơn quy tắc "phase-16 là
phase duy nhất được sửa file của cả hai track". Cố ý, xem
`../reports/debugger-260806-1347-header-mau-thuan-trang-thai-dang-nhap.md`.

**Bài học cho phase-09..12:** nối phiên NGAY khi dựng màn, đừng truyền cứng `profile={null}` rồi
hoãn — `/kudos`, `/awards`, `/profile` sẽ dính đúng cái bẫy này.

### Asset

- Logo Root Further gộp về `public/brand/root-further-logo.png`. Bản tải cho Homepage trùng **md5**
  với bản `public/login/Root_Further_Logo.png` của phase-07 — hai bản sao của cùng một asset thương
  hiệu nghĩa là lần đổi logo sau sẽ sót một chỗ. `login-screen.tsx` đã trỏ lại.
- `public/home/keyvisual-bg.png` nặng **4,3MB** → bắt buộc qua `next/image` (`fill` + `priority`),
  KHÔNG dùng `background-image` CSS (CSS tải nguyên bản, không qua tối ưu định dạng).
- Khác phase-07: màn này **cả 35 node media đều có URL**, kể cả keyvisual — không phải dùng ảnh tạm.

## Session 2026-08-06 (Sau phase-09 UI Live board)

### Acceptance của phase-09 SAI so với bản vẽ — cần người soạn spec chốt

Phase file ghi "sidebar 5 chỉ số + nút Mở quà + **2 leaderboard**". Query `2940:13488` cho thấy sidebar
chỉ có **2 con**: khối thống kê `D.1_` và **MỘT** leaderboard `D.3_`. Đánh số nhảy `D.1 → D.3` cho thấy
`D.2_` từng tồn tại rồi bị xoá khỏi thiết kế. → Bỏ prop `topReceivers` thay vì để nó vĩnh viễn rỗng.

Hai chỗ khác lệch giữa mô tả và bản vẽ:
- Nhãn nút thật là **"Mở Secret Box"**, không phải "Mở quà".
- Dòng phụ mỗi hàng leaderboard là **chuỗi mô tả quà** (`"Nhận được 1 áo phông SAA"`), không phải con
  số — không dựng lại được từ `number` + mẫu câu. Track B phải trả câu đã dựng sẵn.

### Hero tier: đã có TÊN, vẫn thiếu NGƯỠNG

Gap #7 chốt bỏ Hero tier vì "thiếu tên tier + ngưỡng". Màn Live board cho biết **4 tên**: `New Hero`,
`Rising Hero`, `Super Hero`, `Legend Hero` — và huy hiệu xuất hiện trên MỌI thẻ kudo. Nhưng **ngưỡng
vẫn không có ở đâu**. → `KudoCard` nhận `heroTier` như prop tuỳ chọn: UI dựng đủ chỗ khớp bản vẽ, luật
suy ra hạng để trống cho phase-16/PO. Không bịa ngưỡng.

**Ảnh badge `New Hero` không lấy được** — node `MM_MEDIA_New Hero` không có URL trong `get_media_files`
và `get_figma_image` trả 500. Gặp `new` thì không render huy hiệu. 3 hạng còn lại có đủ ảnh.

### Node không mang tiền tố `MM_MEDIA_` thì nằm NGOÀI pipeline asset

Ba lớp nền hoạ tiết của panel Spotlight (`image 24`, `image 25`, `Root further mo rong 1`) không lấy
được vì tên không có tiền tố — **đúng cái bẫy đã gặp với ảnh hero ở phase-07**. Panel hiện dùng nền đặc
cùng tông + đúng viền/bo góc thật (`1px #998C5F`, `radius 47.14px`, tỉ lệ 1157×548). Muốn đủ hoạ tiết
thì đổi tên 3 node đó trong Figma rồi sync lại — không phải sửa code.

### Bài học quy trình: agent không có MCP thì SUY ĐOÁN, và nó không tự biết

Giữa phiên tôi làm hỏng MCP momorph bằng một lần `claude mcp add` sai endpoint (`momorph.ai/api/mcp` ở
scope user, trong khi bản đúng là `mcp.momorph.ai/mcp` ở scope local). Hai agent chạy sau đó **không có
công cụ tra thiết kế** và dựng bằng cách suy từ tên node. Cả hai đều khai báo thẳng, nhưng kết quả lệch
thật và chỉ lộ ra khi đối chiếu ảnh:

| Chỗ | Agent đoán | Figma thật |
|---|---|---|
| Banner | 2 nút "Viết Kudo" / "Tìm kiếm sunner" | 2 ô bo tròn `radius 68px`, chữ "Hôm nay, bạn muốn gửi lời cảm ơn và ghi nhận đến ai?" / "Tìm kiếm profile Sunner" |
| Headline | không có | "Hệ thống ghi nhận và cảm ơn" 36px/44px `#FFEA9E` |
| Carousel | thẻ rút gọn avatar + tên | **thẻ kudo đầy đủ** 528px, viền 4px `#FFEA9E`, radius 16 |
| Header section | chỉ mỗi chữ tiêu đề | eyebrow + kẻ `#2E3940` + tiêu đề 57px, lặp 3 lần |

→ **Kiểm công cụ của agent TRƯỚC khi giao việc phụ thuộc công cụ đó.** Và sửa cấu hình MCP giữa phiên
thì không có tác dụng: client nạp cấu hình lúc khởi động, phải restart mới ăn.

### Bốn lỗi im lặng tìm được bằng cách CHẠY, không phải đọc code

1. **Chốt chặn double-click không hoạt động.** `useHeartToggle` kiểm `pending` từ state — 5 cú bấm cùng
   một tick đều đọc closure cũ với set rỗng, cả 5 đều lọt. Con số hiển thị vẫn ĐÚNG (cả 5 tính ra cùng
   giá trị) nên nhìn qua tưởng đạt; đo bằng cách đếm lời gọi mới lộ ra. → chuyển sang `useRef` cập nhật
   đồng bộ. Sau khi sửa: 5 cú bấm → đúng **1** lời gọi.
2. **Huy hiệu Hero render 20×4px** thay vì 109×19 — carousel khai nhầm `width=20 height=20` cho ảnh chữ
   nhật, cộng flex bóp. Tỉ lệ vẫn đúng nên không "méo", chỉ là bé đến mức không đọc được.
3. **React key trùng** — thẻ dùng `key={image.url}` mà một kudo hoàn toàn có thể đính cùng một ảnh 2 lần.
4. **`##Dedicated`** — mock lưu hashtag kèm `#` trong khi thẻ tự thêm dấu. Tầng dữ liệu thật lưu tên trần.

### Trùng lặp phát sinh khi 4 agent dựng song song — đã gộp

- Bảng huy hiệu Hero chép ở 2 file → `hero-badge.tsx`
- Icon SVG nội tuyến rải 5 file, kính lúp trùng 2 nơi, `kudo-card` còn dùng path bút chì **tự đơn giản
  hoá** thay vì asset thật → `board-icons.tsx`
- Mảng nav 3 mục chép ở 3 nơi, bản trong `board-page.tsx` dùng sai key và hardcode tiếng Anh (không dịch
  được) → `components/layout/site-nav.ts`
- Mẫu header section lặp 3 lần trong màn (và cũng là mẫu ở trang chủ) → `section-header.tsx`

### Điểm nối dây phase-16 của màn này (grep `phase-16` trong `board-page-client.tsx`)

`onLoadMore` cắt trang từ mảng mock thay vì keyset cursor thật · `onToggleHeart` giả lập độ trễ rồi lật
trạng thái (tồn tại để kiểm được luật chống double-click; chữ ký `Promise<ToggleHeartResult>` giữ nguyên
cho RPC thật) · `newKudosQueue` luôn 0 vì chưa nối Broadcast — **không giả lập số đếm nhảy loạn cho có
vẻ sống động** · `onCompose`/`onRules`/`onOpenBox` mở modal phase-10/13/15 chưa tồn tại.

`app/kudos/page.tsx` **đã nối phiên đăng nhập thật ngay từ đầu** (không lặp lại sai lầm phase-08).

## MoMorph refs
- fileKey: `9ypp4enmFmdK3YAFJLIu6C` (file "SAA 2025 - Internal Live Coding")
- URL pattern: `https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/{screenId}`
- Inventory 18 màn: `../reports/momorph-260805-1011-website-spec-done-screens.md`
- Spec + test case CSV đã tải: `research/momorph/csv/`
