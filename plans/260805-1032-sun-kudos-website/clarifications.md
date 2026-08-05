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
- Hero tier: cần designer cấp tên tier + ngưỡng + icon.
- Rule cấp phát Secret Box: cần PO chốt. **Đường tạm:** RPC `admin_grant_secret_box()` + runbook cấp tay (phase-02) — đủ để sự kiện không chết giữa chừng khi hết hộp. (#7)
- Nội dung/trigger cụ thể của notification bell (gap #14) — định nghĩa lúc implement, ưu tiên "nhận kudos mới".
- Màn Admin Dashboard thật: cần batch spec riêng.
- **`department_id` của mọi user đăng nhập thật sẽ là NULL.** Google không trả phòng ban, trigger chỉ chép name/avatar, và **không có màn sửa profile trong 18 màn**. Đường tạm: filter gom NULL vào nhóm hiển thị **"Chưa phân loại"** thay vì trả rỗng im lặng. Cần PO chốt cách gán phòng ban thật (import HR? màn chọn lúc đăng nhập lần đầu? — cả hai đều cần design mới). (#6)
- **`PAO - PAO` trong danh sách phòng ban nguồn** — mục thứ 50, một phòng ban con trùng tên cha (`PAO` là mục 33). Gần như chắc chắn lỗi nhập liệu bên soạn spec. Vẫn seed đủ 50 kèm `FIXME`, chờ người soạn spec xác nhận gộp hay sửa tên. (capped finding)
- **8/18 file test case rỗng hoàn toàn 0 byte** (mọi dropdown + cả 2 FAB) — nhóm component dùng chung của phase-06 không có TC gốc để bám, test phải suy từ spec. Nếu QA bổ sung TC sau, rà lại phase-17. (capped finding)
- **PRE-REQ-01 — Google OAuth client** chưa giao cho ai. Cần quyền admin Google Workspace của tổ chức; chặn phase-03 → 04 → 05 → 16. Xem `plan.md` mục Pre-requisites. (capped finding)

## MoMorph refs
- fileKey: `9ypp4enmFmdK3YAFJLIu6C` (file "SAA 2025 - Internal Live Coding")
- URL pattern: `https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/{screenId}`
- Inventory 18 màn: `../reports/momorph-260805-1011-website-spec-done-screens.md`
- Spec + test case CSV đã tải: `research/momorph/csv/`
