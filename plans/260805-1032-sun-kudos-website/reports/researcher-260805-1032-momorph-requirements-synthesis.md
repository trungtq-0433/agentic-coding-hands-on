# Sun* Kudos (SAA 2025) — Tổng hợp yêu cầu từ spec + test case MoMorph

Nguồn: 18 file `spec-*.csv` (252 item thực tế, không phải 245 như brief — chênh do vài dòng draft/placeholder trùng No, xem ghi chú) + 14 file `tc-*.csv` có nội dung (292 TC, 9 màn dropdown/FAB có `tc-*.csv` rỗng — đúng như brief).
Không có skill tkm nào khớp việc "đọc CSV spec/tc có sẵn và tổng hợp yêu cầu" (đã kiểm qua `tkm:help`) → dùng Bash/Read trực tiếp, đọc hết 100% file được liệt kê.

Quy ước: **[INFERRED]** = suy luận của researcher, không phải spec/tc nói thẳng. Không đánh dấu = trích trực tiếp có thể truy nguồn itemId/TC_ID.

---

## 1. Tóm tắt từng màn

| Màn | screenId | Spec/TC | Tóm tắt |
|---|---|---|---|
| **Login** | GzbNeVGJHz | 8 / 17 | Trang đăng nhập Google OAuth duy nhất (nút B.3). Header logo + language selector, hero + nút "LOGIN With Google", footer copyright. Mọi tài khoản Google được phép (item 2.2.1). Redirect sau login: spec ghi `/todo` (placeholder chưa hoàn thiện — xem gap #2), TC nói "main application page". Guest thấy trang; user đã login bị redirect khỏi trang này (TC 45278c06, f62b0c97). |
| **Homepage SAA** | i87tDx10uM | 46 / 62 | Trang chủ public: Header (logo, nav, bell, ngôn ngữ, account menu — admin thấy thêm "Admin Dashboard"), Keyvisual + Countdown (widget, cập nhật theo phút, nguồn env var — item B1), Award grid 6 thẻ (click → Awards Information kèm hashtag-slug scroll), block Sun* Kudos promo, Widget/FAB button, Footer. Guest xem được nội dung public (TC ID-0); actions cần login. |
| **Profile bản thân** | 3FoIx6ALVb | 28 / 30 | `/profile` (self) và `/profile?id=` (người khác) — 2 mặt của cùng route. Spec phần lớn ở trạng thái `draft` (thiếu mô tả), TC lại rất chi tiết (xem gap #7, #4). Hero: avatar/tên/phòng ban/Hero-tier badge/hoa-thị sao. Badge collection 6 slot (khoá xám — Secret Box chưa live). Card thống kê 5 chỉ số CHỈ hiện ở self; profile người khác thay bằng thanh "viết Kudo" pre-fill người nhận. Dropdown hướng Kudos: self có "Đã nhận/Đã gửi", người khác chỉ có "Đã nhận" (ẩn để không lộ số kudo ẩn danh đã gửi). |
| **Sun\* Kudos Live board** | MaZUn5xHXZ | 64 / 41 | Trang trọng tâm: Banner → ô nhập mở form Viết Kudo → Highlight Kudos (carousel top-5 theo tim, filter Hashtag/Phòng ban) → Spotlight word-cloud (388 KUDOS, pan/zoom, search) → All Kudos (infinite scroll) + Sidebar (thống kê cá nhân, nút Mở quà, 2 leaderboard: thăng hạng mới nhất/nhận quà mới nhất). Tương tác: heart toggle, copy link, click avatar/tên → profile, click hashtag → filter. Guest xem được UI, click profile/detail bắt login (TC 71b3ef43). |
| **Viết Kudo** (modal) | ihQ26W78P2 | 26 / 57 | Modal gửi kudos: Người nhận (autocomplete bắt buộc), textarea rich-text (bold/italic/stroke/số/link/quote, @mention), Hashtag (1–5, bắt buộc), Image (0–5, jpg/png only), checkbox "Gửi ẩn danh" (bật → hiện thêm field nhập tên ẩn danh — xem gap #4), Hủy/Gửi. Test case rất đầy đủ (57 TC) phủ hết validation. |
| **Hệ thống giải** (Awards Info) | zFYDgyj_pD | 23 / 15 | Trang tĩnh giới thiệu 6 hạng mục giải (Top Talent, Top Project, Top Project Leader, Best Manager, Signature 2025 - Creator, MVP) kèm số lượng + giá trị giải; menu điều hướng trái (scrollspy, active state); block CTA Sun* Kudos ở cuối. Không có form nhập liệu — chủ yếu display + navigation. |
| **Thể lệ** (panel/modal) | b1Filzi9i6 | 4 / 9 | Panel hiển thị nội dung thể lệ, danh sách thưởng, 6 huy hiệu; footer "Đóng"/"Viết KUDOS" (mở modal Viết Kudo). Scroll khi nội dung dài. |
| **Countdown Prelaunch** | 8PJQswPZmU | 5 / 17 | Trang chặn toàn màn hình TRƯỚC khi site mở, đếm ngược Days/Hours/Minutes cập nhật MỖI GIÂY (khác Homepage — theo phút). Khi về 0: mở khoá điều hướng toàn site; trước đó mọi điều hướng bị khoá (item "1" transitionNote). Nguồn target datetime: spec ghi rõ "TODO: thiết kế API endpoint" — chưa có (xem gap #1). TC tự ghi "Access control unspecified" — spec/tc đều không xác định ai được xem trang này. |
| **Open Secret Box** (modal) | J3-4YFIpMM | 4 / 19 | Modal thành công sau khi mở hộp: hiển thị huy hiệu ngẫu nhiên nhận được (6 loại theo tỉ lệ cố định), click box lại để mở tiếp (nếu còn hộp chưa mở), số hộp chưa mở ở đáy modal. TC khẳng định rõ: số hộp chưa mở PHẢI lấy từ backend, không được thao túng client-side (security TC). |
| **Dropdown Hashtag filter** | JWpsISMAaM | 4 / 0 | Component dùng chung: danh sách hashtag để filter Live board. Mô tả liệt kê cứng 13 hashtag mẫu — mâu thuẫn với "queried from DB" ở nơi khác (gap #5). |
| **Dropdown Phòng ban** | WXK5AYB_rG | 4 / 0 | Component filter theo phòng ban — mô tả liệt kê cứng danh sách phòng ban Sun* (CTO, SPD, FCOV, CEVC1...) nhưng function note nói "được truy vấn từ CSDL" (gap #5). |
| **Dropdown list hashtag** | p9zO-c4a4x | 10 / 0 | Component chọn hashtag TRONG form Viết Kudo (khác dropdown filter ở trên) — multi-select tối đa 5, disable phần còn lại khi đủ 5, hashtag "load dynamic từ DB". |
| **Dropdown ngôn ngữ** | hUyaaugye2 | 3 / 0 | VN/EN, cờ + mã ngôn ngữ, dùng chung Header mọi trang. |
| **Dropdown profile** | z4sCl3_Qtk | 3 / 0 | Menu account cho user thường: Profile, Logout. |
| **Dropdown profile Admin** | 54rekaCHG1 | 4 / 0 | Menu account cho admin: Profile, Dashboard (route TODO chưa xác định — gap #3), Logout (gọi API logout, không có confirm dialog, về Homepage). |
| **Addlink Box** (modal) | OyDLDuSGEa | 10 / 25 | Dialog chèn link vào rich-text editor (dùng trong Viết Kudo — nút C.5): Text (1–100 ký tự, bắt buộc, không chỉ khoảng trắng), Link (URL hợp lệ, 5–2048 ký tự, bắt buộc), Hủy/Lưu. |
| **FAB 1** | _hphd32jN2 | 3 / 0 | Nút nổi thu gọn (Homepage) mở 2 lựa chọn nhanh. 3 item spec đều mô tả giống hệt nhau — dấu hiệu lỗi copy-paste khi viết spec (gap nice-to-have #15). |
| **FAB 2** | Sv7DFwBw1h | 3 / 0 | Trạng thái mở rộng của FAB: nút "Thể lệ", "Viết KUDOS", "Hủy" (tròn đỏ, icon ×). |

---

## 2. Data model đề xuất (Postgres/Supabase)

`databaseTable`/`databaseColumn` gần trống toàn bộ 252 spec item (chỉ 2 chỗ ghi "kudos" mơ hồ — spec-live-board hàng B, B.2.3). **Toàn bộ bảng dưới đây là [INFERRED]** từ ngữ nghĩa spec+tc, trừ khi ghi chú khác.

| Bảng | Cột chính | Ghi chú |
|---|---|---|
| `profiles` | `id uuid PK FK auth.users`, `full_name text`, `avatar_url text`, `department_id FK`, `role enum('user','admin')`, `created_at` | Không có cột email/auth id được public hiển thị (TC_WEB_PROFILE_SEC_004 khẳng định không lộ). role suy ra từ dropdown-profile-admin tồn tại riêng. |
| `departments` | `id`, `code text unique`, `name text`, `parent_department_id FK self` (nullable) | Cấu trúc phân cấp **[INFERRED]** từ tên lồng nhau trong spec-dropdown-phong-ban ("CEVC2 - CySS", "OPDC - HRF - TA"). |
| `hashtags` | `id`, `name text unique` | Master table, DB-driven theo spec-live-board B.1.1/B.1.2 + spec-dropdown-list-hashtag A.1 ("dữ liệu... load dynamic từ DB"). |
| `kudos` | `id`, `sender_id FK profiles`, `recipient_id FK profiles`, `body text` (rich text, cần sanitize XSS), `is_anonymous bool`, `anonymous_alias text NULL`, `created_at`, `status enum` (default 'active', dự phòng "Spam" chip — TC_WEB_PROFILE_GUI_007 xác nhận field kiểu tồn tại nhưng chip không dùng) | Constraint `kudos_no_self` (sender != recipient) — **được TC_WEB_PROFILE_FUN_008 xác nhận đã tồn tại**, không phải suy luận thuần. |
| `kudos_hashtags` | `kudos_id`, `hashtag_id` | Join table, ràng buộc ứng dụng tối đa 5/kudos (spec E.2, ID-16/17 tc-viet-kudo). |
| `kudos_images` | `id`, `kudos_id`, `url`, `position smallint` | Tối đa 5 ảnh (spec F, TC ID-18–20 tc-viet-kudo); chỉ nhận jpg/png (TC ID-21–24). |
| `kudos_mentions` | `kudos_id`, `mentioned_profile_id` | **[INFERRED]** — cần bảng riêng để tra cứu/notify người được @mention; spec chỉ nói "gợi ý autocomplete", không nói lưu trữ ra sao. |
| `hearts` | `id`, `kudos_id FK`, `user_id FK profiles`, `is_special_day_bonus bool`, `created_at`, UNIQUE(`kudos_id`,`user_id`) | 1 tim/user/kudos (spec C.4.1); sender không tự tim được kudos mình (TC 63645b03); cờ bonus để thu hồi đúng số khi unlike (spec C.4.1 note "Cần phân biệt lượt thả tim bình thường và đặc biệt"). |
| `special_days` | `id`, `date`, `note`, `created_by_admin_id` | **[INFERRED]** — bắt buộc phải persist vì rule +2 tim ngày đặc biệt "do admin cấu hình" (spec C.4.1), nhưng KHÔNG có màn admin nào trong 18 màn để xác nhận cấu trúc. |
| `badges` | `id`, `name` (Stay Gold/Flow to Horizon/Beyond the Boundary/Root Further/Touch of Light/Revival), `image_url`, `probability_weight` (30/25/10/5/20/10) | Trực tiếp từ spec-open-secret-box item C. |
| `profile_badges` | `profile_id FK`, `badge_id FK`, `awarded_at` | Bộ sưu tập icon cá nhân (spec-profile item A: "Bộ sưu tập icon của tôi tuân theo icon mở được trong Secret box"). |
| `secret_box_grants` | `id`, `profile_id FK`, `status enum('unopened','opened')`, `badge_id FK NULL`, `opened_at NULL` | Ledger để tính "chưa mở/đã mở" + phục vụ leaderboard "10 sunner nhận quà mới nhất". **Cách cấp phát hộp hoàn toàn không có trong spec/tc** (gap #9). |
| `awards` | `id`, `slug`, `title`, `description`, `quantity_label`, `prize_value_label`, `image_url`, `sort_order` | 6 hạng mục cố định trong spec-he-thong-giai — **có thể là static content, không nhất thiết cần bảng DB** (gap #10). |
| `event_config` | `key text PK`, `value text` (vd `event_start_at`, `launch_gate_at`) | **[INFERRED]** — cần 1 nguồn cấu hình datetime chung để giải quyết mâu thuẫn env-var-vs-API (gap #1). |
| `notifications` | `id`, `profile_id FK`, `type`, `payload jsonb`, `is_read bool`, `created_at` | Hoàn toàn suy luận — spec chỉ xác nhận có bell + badge đỏ, không nói nội dung/trigger (gap nice-to-have #14). |

**Index đề xuất [INFERRED]:** `kudos(recipient_id, created_at desc)`, `kudos(sender_id, created_at desc)` (phục vụ feed nhận/gửi + infinite scroll keyset — TC_WEB_PROFILE_FUN_013 xác nhận dùng "keyset cursor"), `hearts(kudos_id)`, `kudos_hashtags(hashtag_id)`, `profiles(department_id)`.

---

## 3. Ma trận quyền (input cho RLS)

| Hành động / Màn | Guest (chưa login) | Sunner (user thường) | Admin |
|---|---|---|---|
| Xem Homepage (nội dung public) | ✅ (TC ID-0) | ✅ | ✅ |
| Xem Login screen | ✅ (nếu chưa login) | ❌ redirect về app chính (TC f62b0c97) | ❌ |
| Xem Live board (Kudos feed, đọc) | ✅ (TC 71b3ef43 precondition) | ✅ | ✅ |
| Click avatar/tên/Xem chi tiết trên Live board | ❌ → redirect login (TC 71b3ef43) | ✅ | ✅ |
| Xem `/profile` (bất kỳ ai) | ❌ → redirect `/login` (TC_WEB_PROFILE_ACC_001) | ✅ | ✅ |
| Xem Sent-list của NGƯỜI KHÁC (kể cả kudos ẩn danh của họ) | ❌ | ❌ — route chỉ cho self (TC_WEB_PROFILE_SEC_001/002/003, "definer view" giới hạn theo caller) | ❌ (không có bằng chứng admin được đặc quyền xem) |
| Gửi Kudos (Viết Kudo modal) | ❌ (ACCESSING ID-1) | ✅ | ✅ |
| Thả tim (Heart) | ❌ (ngụ ý cần login) | ✅, trừ kudos tự gửi (TC 63645b03) | ✅, cùng luật |
| Mở Secret Box | ❌ | ✅ nếu còn hộp chưa mở (TC 7c3c912f/2a8a63de) | ✅ (không có phân biệt) |
| Account menu → "Admin Dashboard" | — | ❌ không thấy mục này (TC ID-6, ID-38) | ✅ thấy mục này (TC ID-5, ID-37) — **route đích chưa xác định** (gap #3) |
| Sửa thông tin profile (tên/avatar/phòng ban) | — | ❌ — route chỉ đọc, không có edit affordance (TC_WEB_PROFILE_SEC_004) | Không có bằng chứng khác |

**Kết luận cho RLS:** `profiles` và `kudos` cần SELECT công khai (kể cả ẩn danh, cột nào cũng phải, do board hiển thị public); phần "ẩn" Sent-list của người khác không nên chặn bằng RLS thô trên bảng `kudos` (sẽ chặn luôn board công khai) mà nên qua **view/RPC riêng theo `auth.uid()`** như TC gợi ý ("definer view"). `/profile` route-level auth gate tách biệt với RLS bảng dữ liệu — đây là **kiểm soát ở tầng ứng dụng (middleware/proxy.ts)**, không phải RLS.

---

## 4. Quy tắc nghiệp vụ & validation (gom từ validationNote/qa/Expected_Result)

| Vùng | Quy tắc | Nguồn |
|---|---|---|
| Viết Kudo — Người nhận | Bắt buộc, chọn từ autocomplete Sunner có thật, min 1 ký tự tìm kiếm | spec B.2; TC ID-7/8 |
| Viết Kudo — Nội dung | Bắt buộc, hỗ trợ rich text + `@mention` | spec D; TC ID-11/12/13 |
| Viết Kudo — Hashtag | Bắt buộc, **1–5** tag | spec E/E.2; TC ID-14–17 |
| Viết Kudo — Image | Không bắt buộc, tối đa **5**, chỉ jpg/png (pdf/mp4/txt bị từ chối) | spec F; TC ID-18–24, ID-55 |
| Viết Kudo — Gửi ẩn danh | Checkbox off mặc định; bật → hiện field nhập tên ẩn danh (ngữ nghĩa field này còn mơ hồ — gap #4) | spec G; TC ID-6, ID-41–44 |
| Add Link — Text | Bắt buộc, 1–100 ký tự, không chỉ khoảng trắng | spec B/B.2; TC 7d85997d/adb699ca |
| Add Link — Link | Bắt buộc, URL hợp lệ (http/https), 5–2048 ký tự | spec C; TC db2ca333/aad5791a |
| Thanh tìm Sunner (Spotlight) | Không bắt buộc, tối đa 100 ký tự | spec B.7.3; TC 9e689933 |
| Heart | Mỗi user chỉ 1 lượt tim/1 kudos; sender không tự tim được kudos mình gửi; ngày đặc biệt (admin cấu hình) → +2 tim thay vì +1; hủy tim → thu hồi đúng số đã cộng (1 hoặc 2) | spec C.4.1; TC 63645b03/91e102ba/31936b72 |
| Secret Box | Mỗi lần mở chỉ nhận **đúng 1** huy hiệu ngẫu nhiên theo tỉ lệ cố định: Stay Gold 30%, Flow to Horizon 25%, Beyond the Boundary 10%, Root Further 5%, Touch of Light 20%, Revival 10%; số hộp chưa mở là nguồn từ server, không thể sửa client-side | spec C (open-secret-box); TC d566fbeb/5cc072ad |
| Countdown Prelaunch | Cập nhật MỖI GIÂY, khoá điều hướng đến khi = 0, timezone `Asia/Ho_Chi_Minh` (UTC+7) | spec item 1/2/3 |
| Countdown Homepage | Cập nhật THEO PHÚT (không phải giây), nguồn env var ISO-8601, ẩn "Coming soon" khi = 0, giữ nguyên `00` sau khi qua mốc | spec B1/B1.2; TC ID-39–43, ID-56/57 |
| Hoa-thị (sao) trên profile | 1 sao = 10 Kudos nhận được; 2 sao = 20; 3 sao = 50 (tính trên TỔNG kudos nhận) | spec B.3.2 (live-board) |
| "Hero tier" badge | Tính trên số NGƯỜI GỬI KHÁC NHAU (distinct senders), khác hẳn hoa-thị — **ngưỡng cụ thể không có trong spec nào** (gap #7) | TC_WEB_PROFILE_GUI_001 note |

---

## 5. Yêu cầu realtime

Không có spec/tc item nào dùng từ "realtime"/"websocket"/"subscribe" tường minh. Suy luận **[INFERRED]** hoàn toàn từ tên màn "Live board" + stack đích (Supabase Realtime có sẵn):

| Nơi cần | Event | Ai subscribe |
|---|---|---|
| Live board — All Kudos feed | INSERT kudos mới | Mọi client đang mở board (kể cả guest, do board public) |
| Live board — Highlight Kudos (top 5 theo tim) | UPDATE heart_count | Mọi client đang mở board |
| Kudos card (mọi nơi hiển thị: board, profile) | Heart count thay đổi | Client đang xem card đó — nhưng TC (TC_WEB_PROFILE_FUN_014) nói rõ số hiển thị phải lấy "giá trị SERVER báo về", không tự tăng lạc quan phía client → ưu tiên refetch/realtime hơn optimistic update thuần |
| Spotlight word-cloud "388 KUDOS" | Tổng số kudos | Có thể polling khi mở board là đủ (không bắt buộc realtime — nice-to-have #13) |
| Notification bell + badge đỏ | Kudos/heart/rank-up mới liên quan đến user | User đã login, mọi trang có header |

Không có gì trong spec/tc gợi ý phải làm realtime cho Awards Info, Thể lệ, Countdown (countdown tự tính client-side từ target datetime, không cần push).

---

## 6. Đa ngôn ngữ (i18n)

- Hỗ trợ đúng **2 ngôn ngữ: VN, EN** — xác nhận tường minh (spec Login 1.2 "Hỗ trợ 2 ngôn ngữ: VN và EN"; TC Homepage ID-58 "Only VN and EN options displayed").
- Lưu lựa chọn: cookie `NEXT_LOCALE` (spec-login item 1.2, tường minh — không phải suy luận).
- Phần cần dịch: **toàn bộ UI chrome** (label, nút, tiêu đề, thông báo, placeholder) — xác nhận qua TC_WEB_PROFILE_GUI_008 ("mọi string trên trang đều dịch 2 ngôn ngữ") + có file `locales/{vi,en}/profile.json` (tc nêu tên file cụ thể).
- Nội dung do người dùng tạo (nội dung Kudos, tên ẩn danh tự nhập) — **không có cơ chế dịch nào được nói tới**, giữ nguyên như người dùng gõ **[INFERRED — theo YAGNI, không tự thêm dịch máy]**.
- Countdown label ("DAYS"/"HOURS"/"MINUTES", "Sự kiện sẽ bắt đầu sau"/"Event starts in") cũng theo bộ dịch UI chrome (spec countdown-prelaunch item 0.2).

---

## 7. Danh sách GAP

### BLOCKING

| # | Gap | Ảnh hưởng màn | Phương án |
|---|---|---|---|
| 1 | Nguồn target datetime cho countdown mâu thuẫn: Homepage nói ENV VAR (spec-homepage B1: "có thể được cấu hình thông qua biến môi trường"), Countdown Prelaunch nói API chưa thiết kế (spec-countdown item 1 databaseNote: "TODO: thiết kế API endpoint"). Không rõ đây là 1 hay 2 mốc thời gian khác nhau (site-launch gate vs event-day). | Homepage, Countdown Prelaunch | (a) 1 bảng `event_config` với 2 key riêng, seed từ env var lúc migrate, có thể update qua Supabase sau **[Khuyến nghị]** — khớp stack Supabase, không cần redeploy khi đổi ngày; (b) chỉ dùng API cho cả 2; (c) chỉ dùng env var cho cả 2 (khớp TODO note kém nhất vì countdown-prelaunch đã ghi rõ cần API). |
| 2 | Login redirect đích `/todo` là placeholder rõ ràng trong spec (item 2.2.1), không phải route thật. | Login | (a) Redirect về Homepage `/` **[Khuyến nghị]** — khớp TC "main application page"; (b) redirect thẳng `/kudos` (board); (c) redirect theo role (admin→dashboard, user→home) — nhưng dashboard route cũng chưa có (xem gap #3). |
| 3 | Route/màn "Admin Dashboard" hoàn toàn chưa xác định — chính spec ghi TODO tường minh (spec-dropdown-profile-admin A.2: "TODO: Route/màn hình Admin Dashboard chưa được xác định"), và không nằm trong 18 màn được giao. | Dropdown profile Admin, Homepage (menu item) | (a) Ẩn/disable mục "Admin Dashboard" cho đến khi có batch spec riêng, chỉ để route middleware bảo vệ sẵn **[Khuyến nghị]**; (b) build trang tạm/placeholder ngay; (c) yêu cầu batch spec admin riêng trước khi code phần này. |
| 4 | Ngữ nghĩa "tên ẩn danh" khi bật checkbox gửi ẩn danh không nhất quán: spec Viết Kudo (item G) mô tả như 1 **field tự nhập** tên ẩn danh; nhưng TC Profile (TC_WEB_PROFILE_SEC_002) gọi đó là "masked-alias **placeholder**" — ngụ ý 1 nhãn CỐ ĐỊNH hệ thống gán, không phải do user gõ tự do. | Viết Kudo, Profile, Live board (hiển thị kudos ẩn danh) | (a) Bỏ field tự nhập, luôn hiện nhãn cố định kiểu "Người ẩn danh" **[Khuyến nghị]** — khớp cách TC Profile mô tả, tránh rủi ro giả danh người khác; (b) giữ field tự nhập làm bút danh tùy chỉnh cho riêng kudos đó; (c) hybrid: field tùy chọn, mặc định nhãn cố định nếu bỏ trống. |
| 5 | Nguồn danh sách Hashtag & Phòng ban mâu thuẫn: 2 spec dropdown liệt kê DANH SÁCH CỨNG cụ thể (13 hashtag, ~40+ phòng ban) trong phần mô tả, nhưng 3 spec khác (`live-board` B.1.1/B.1.2, `dropdown-list-hashtag` A.1) nói rõ "được truy vấn/load dynamic từ CSDL". Không có màn admin CRUD nào trong 18 màn để quản lý 2 danh sách này. | Dropdown Hashtag filter, Dropdown Phòng ban, Dropdown list hashtag, Live board, Viết Kudo | (a) Coi 2 bảng là DB-driven, danh sách cứng trong spec chỉ là DATA MẪU cần seed, không có admin CRUD ở MVP **[Khuyến nghị]** — khớp 3/5 nguồn nói "từ DB"; (b) admin CRUD đầy đủ (ngoài phạm vi 18 màn, để sau); (c) hardcode hằng số trong code (mâu thuẫn trực tiếp với 3 spec item). |

### IMPORTANT

| # | Gap | Ảnh hưởng màn | Phương án |
|---|---|---|---|
| 6 | Phạm vi realtime hoàn toàn không được spec/tc nói tới, chỉ suy luận từ tên "Live board". | Live board, Homepage (bell) | (a) Supabase Realtime channel trên bảng `kudos`/`hearts` phát tới board + notification **[Khuyến nghị]** — đúng stack đã chọn; (b) polling định kỳ; (c) không có, chỉ refresh thủ công. |
| 7 | "Hero tier" badge (tính theo số người gửi khác nhau) chỉ xuất hiện trong 1 TC note (TC_WEB_PROFILE_GUI_001), KHÔNG có trong bất kỳ spec item nào trong 252 dòng đã đọc — tên tier, ngưỡng cụ thể đều thiếu. | Profile, có thể cả Live board leaderboard | (a) Yêu cầu bổ sung spec/design cho Hero tier trước khi code phần này **[Khuyến nghị]**; (b) suy đoán ngưỡng đối xứng với hoa-thị (10/20/50 senders khác nhau) làm tạm; (c) bỏ khỏi MVP vì chưa có tài liệu. |
| 8 | Cơ chế "ngày đặc biệt" cho heart bonus: ai cấu hình, cấu hình ở đâu (không có màn admin trong batch), và cách phân biệt tim thường/tim bonus khi unlike qua ngày khác. | Live board (heart) | (a) Bảng `special_days` + cờ `hearts.is_special_day_bonus` quyết định lúc INSERT, dùng lại lúc thu hồi **[Khuyến nghị]**; (b) tính lại theo ngày hiện tại lúc unlike (sai nếu unlike khác ngày); (c) luôn thu hồi 1 (vi phạm rule đã nêu). |
| 9 | Quy tắc CẤP Secret Box (bao nhiêu kudos/mốc nào thì được +1 hộp chưa mở) không xuất hiện ở đâu trong 252 spec/292 tc — chỉ có bước MỞ hộp được đặc tả. | Open Secret Box, Profile, Live board sidebar | (a) Hỏi rõ rule cấp phát trước khi code counters **[Khuyến nghị]**; (b) chỉ admin cấp tay (cần màn admin, chưa có); (c) seed cứng demo, defer rule thật. |
| 10 | 6 hạng mục giải (Hệ thống giải) — nội dung tĩnh hay bảng DB có CRUD? Không màn admin nào quản lý nó trong batch. | Hệ thống giải | (a) Static content (constant/JSON), không cần bảng DB ở MVP **[Khuyến nghị]** — đúng YAGNI vì không có UI quản trị; (b) bảng DB + admin CRUD (để sau); (c) hardcode trong component (chấp nhận được ngắn hạn, khó update). |
| 11 | Countdown Prelaunch: chính TC tự ghi "Access control unspecified" (Category "Check access condition" nhưng Test_Objective để trống) — ai được xem/bypass màn chặn này (kể cả admin) chưa rõ. | Countdown Prelaunch | (a) Chặn tất cả, không ai bypass **[Khuyến nghị]** — đơn giản nhất, đúng mục đích prelaunch gate; (b) admin bypass theo role; (c) bypass qua query param/dev flag. |
| 12 | i18n cho nội dung do user tạo (kudos body, tên ẩn danh tự nhập) — không được đề cập, chỉ UI chrome được xác nhận dịch. | Viết Kudo, Live board, Profile | (a) Giữ nguyên như người dùng gõ, không dịch **[Khuyến nghị]** (YAGNI); (b) tích hợp dịch máy (over-engineering so với scope hiện có); (c) gắn cờ ngôn ngữ nội dung để lọc sau này. |

### NICE-TO-HAVE

| # | Gap | Ảnh hưởng màn | Phương án |
|---|---|---|---|
| 13 | Bộ đếm "388 KUDOS" + word-cloud Spotlight — cần realtime hay chỉ query mỗi lần tải trang? | Live board | Query lúc tải trang là đủ **[Khuyến nghị]**, nâng cấp lên realtime sau nếu cần. |
| 14 | Nội dung/trigger cụ thể của notification bell (nhận kudos? nhận tim? thăng hạng? secret box?) hoàn toàn không được đặc tả — chỉ biết có bell + badge đỏ. | Homepage | Định nghĩa danh sách loại notification lúc implement, ưu tiên "nhận kudos mới" + "thăng hạng" trước. |
| 15 | FAB1 có 3 spec item mô tả giống hệt nhau (copy-paste rõ ràng trong nguồn) — không phân biệt được hành vi click icon trái/phải/nút chính. | FAB 1 | Không chặn code vì FAB2 (trạng thái mở rộng) đã đủ rõ 3 nút; xử lý lúc build UI qua `momorph-implement-design`. |
| 16 | Thuật toán tạo `slug` cho hashtag-anchor của award category (kebab-case tiêu đề?) không nói rõ. | Homepage, Hệ thống giải | Dùng kebab-case(title) làm slug **[Khuyến nghị]**, đơn giản, đủ dùng. |

---

## 8. Ghi chú độ tin cậy — mâu thuẫn spec ↔ test case

| Mâu thuẫn | Vị trí A | Vị trí B |
|---|---|---|
| Nguồn datetime countdown: env var vs API | `spec-homepage-saa-i87tDx10uM.csv` dòng "B1" (item B1, mô tả "có thể được cấu hình thông qua biến môi trường") | `spec-countdown-prelaunch-8PJQswPZmU.csv` dòng item "1" (databaseNote: "TODO: thiết kế API endpoint để lấy target datetime") |
| Redirect sau login | `spec-login-GzbNeVGJHz.csv` item "2.2.1" (transitionNote: "...redirect về `/todo`") | `tc-login-GzbNeVGJHz.csv` TC `e76aa170-85dd-469f-b73e-eac6f574cf57` ("redirected to the main application page") |
| Nguồn hashtag: liệt kê cứng vs DB | `spec-dropdown-hashtag-filter-JWpsISMAaM.csv` item "A" (liệt kê cứng 13 hashtag) | `spec-live-board-MaZUn5xHXZ.csv` item "B.1.1" ("Danh sách hashtag được truy vấn từ cơ sở dữ liệu") + `tc-live-board-MaZUn5xHXZ.csv` TC `0e56cacb...` (Test_Data: "sourced live from the database") |
| Nguồn phòng ban: liệt kê cứng vs DB | `spec-dropdown-phong-ban-WXK5AYB_rG.csv` item "A" (liệt kê cứng ~40+ tên phòng ban) | `spec-live-board-MaZUn5xHXZ.csv` item "B.1.2" ("Danh sách phòng ban sẽ được truy vấn từ cơ sở dữ liệu") |
| Ngữ nghĩa "tên ẩn danh" | `spec-viet-kudo-ihQ26W78P2.csv` item "G" ("Bật: Hiển thị text field điền tên ẩn danh") | `tc-profile-ban-than-3FoIx6ALVb.csv` TC `TC_WEB_PROFILE_SEC_002` (Note: "the masked-alias **placeholder** is NOT used for your own anonymous Kudo") — ngôn ngữ "placeholder" ngụ ý nhãn cố định, không phải field tự nhập tự do |
| "Hero tier" badge chỉ có ở TC, không có ở spec | Không tìm thấy trong bất kỳ spec item nào (đã đọc hết 252 dòng) | `tc-profile-ban-than-3FoIx6ALVb.csv` TC `TC_WEB_PROFILE_GUI_001` Note: "Hero tier is keyed on DISTINCT SENDERS...hoa-thi stars on TOTAL Kudos received...Two different denominators, deliberately." |
| Spec `profile-ban-than` phần lớn ở trạng thái `draft` (thiếu mô tả hoàn toàn — cột description/function trống với 18/28 dòng) trong khi TC cùng màn (30 TC) lại cực kỳ chi tiết, mô tả cả kiến trúc implementation (definer view, keyset cursor, RLS-adjacent logic) | `spec-profile-ban-than-3FoIx6ALVb.csv` — các dòng `A.1`,`A.2`,`A.3`,`B`,`B.1`,`B2`... đều có `spec_progress = "draft"` và cột description/function trống | `tc-profile-ban-than-3FoIx6ALVb.csv` — toàn bộ 30 TC | **Đáng chú ý nhất:** đây là màn duy nhất mà TC là nguồn thông tin chính, không phải spec — nên xử lý ưu tiên đọc TC trước khi code màn Profile. |

---

## Câu hỏi chưa giải quyết

1. Countdown Homepage và Countdown Prelaunch có dùng CHUNG 1 mốc thời gian hay là 2 mốc độc lập (site-launch gate vs event-day)? (gap #1)
2. Route redirect thật sau khi login thành công là gì? (gap #2)
3. Màn Admin Dashboard có nằm trong phạm vi dự án hiện tại không, hay để phase sau? (gap #3)
4. "Tên ẩn danh" trong Viết Kudo là field tự nhập hay nhãn cố định hệ thống? (gap #4)
5. Hashtag/Phòng ban là bảng tĩnh seed 1 lần hay cần admin CRUD? Nếu cần CRUD, màn nào phụ trách? (gap #5)
6. Có bắt buộc dùng Supabase Realtime cho Live board/notification hay polling là đủ cho MVP? (gap #6)
7. "Hero tier" badge: tên tier, ngưỡng cụ thể, ai/khi nào hiển thị? Cần bổ sung spec/design riêng. (gap #7)
8. Cơ chế cấp Secret Box (rule earn hộp chưa mở) là gì? Không có trong bất kỳ spec/tc nào đã đọc. (gap #9)
9. "Ngày đặc biệt" cho heart bonus: cấu hình 1 ngày, nhiều ngày, hay khung giờ? Ai (admin) cấu hình ở đâu? (gap #8)
10. 6 hạng mục giải trong "Hệ thống giải" có cần chỉnh sửa qua admin không, hay là nội dung tĩnh cố định cho mùa giải 2025? (gap #10)
