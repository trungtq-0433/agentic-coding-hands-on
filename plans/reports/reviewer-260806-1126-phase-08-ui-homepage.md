# Review — Phase 08 UI Homepage SAA

**Phạm vi:** `app/page.tsx`, `components/home/**` (10 file), `locales/{vi,en}/home.json`, `public/home/**`,
`public/brand/root-further-logo.png`, và 5 file bàn giao kiểm soát (`components/ui/countdown-timer.tsx`,
`components/ui/fonts.ts`, `components/layout/site-footer.tsx`, `components/layout/site-header.tsx`,
`components/login/login-screen.tsx`). Đọc-only, không sửa file.

## Đã kiểm độc lập (không chỉ tin self-check)
- `npx tsc --noEmit` → sạch.
- `npx eslint components/home app/page.tsx components/ui/countdown-timer.tsx components/ui/fonts.ts components/layout/site-footer.tsx components/layout/site-header.tsx components/login/login-screen.tsx` → 0 lỗi.
- Grep `lib/(data|actions|supabase|realtime)` trong toàn bộ Track A của phase-08 → **không có** import nào (đạt ràng buộc #1).
- Không có `middleware.ts` mới.
- So khớp key `locales/vi/home.json` vs `locales/en/home.json` bằng script — **42 key khớp tuyệt đối tên và số lượng** (đạt ràng buộc #5). `lib/i18n/get-dictionary.ts` không nằm trong diff.
- 14 asset ảnh/svg tham chiếu trong code (`public/home/*`, `public/brand/*`) đều tồn tại trên đĩa.
- Đối chiếu docs thật `node_modules/next/dist/docs/01-app/02-guides/environment-variables.md` — xác nhận đúng: `NEXT_PUBLIC_*` bị inline lúc build, và code viết `process.env.NEXT_PUBLIC_EVENT_START_AT` nguyên dạng (`app/page.tsx:20`) — đạt ràng buộc #4.
- Đọc `git log -p` của `components/ui/countdown-timer.tsx`: logic tính toán + effect trong `useCountdownRemaining` **giống hệt 1:1** bản gốc phase-06 (chỉ tách state/effect ra khỏi component, không đổi một dòng logic) — hành vi `CountdownTimer` không đổi, không hồi quy.

## Critical
Không có.

## Warning

1. **`components/home/home-page.tsx` dài 213 dòng — vượt giới hạn 200 dòng** của quy ước dự án
   (`development-rules.md` → File Size Management, cũng là ràng buộc #2 trong yêu cầu review này).
   Phần lớn do comment toạ độ Figma dài (hợp lý, không nên cắt bỏ nội dung kỹ thuật) — nhưng phần
   compose header (nav array + slot AccountMenu/guest-login, dòng 74–155) tách được thành
   `home-page-header.tsx` riêng để đưa cả hai file về dưới 200 dòng mà không mất comment.
   **Vị trí:** `components/home/home-page.tsx:1-213`.

2. **Public directory chứa rác của tool-run, phải dọn trước khi commit:**
   - `public/home/.claude/agent-memory/implementer/` — thư mục memory agent bị tạo lạc vào `public/home`
     (rỗng, chưa có file, nhưng **`public/` được Next.js serve tĩnh nguyên trạng** — bất cứ thứ gì rơi
     vào đây trở thành công khai được tại `/home/.claude/...`). Đây đúng là loại rủi ro rò rỉ dữ liệu (mục
     #8 trong 8 check bắt buộc) nếu một lần chạy agent sau này ghi nội dung thật vào đó rồi bị `git add -A`
     cuốn theo. Cần xoá thư mục này và thêm `.claude/` vào việc kiểm tra trước khi stage `public/**`.
   - `public/home/kv-preview.png` (236KB) — không được import/tham chiếu ở bất kỳ đâu trong code
     (đã grep xác nhận). Là ảnh crop xem trước lúc dựng UI, cần xoá khỏi asset production.
   **Vị trí:** `public/home/.claude/`, `public/home/kv-preview.png`.

3. **`useMemo` ở `home-page-client.tsx:38` không có tác dụng bảo vệ thực** — nghi ngờ ban đầu đúng
   một phần: `useNamespaceTranslation()` (`lib/i18n/use-namespace-translation.ts:25`) trả về một
   closure MỚI mỗi lần gọi, nên `t` đổi identity ở mọi lần `HomePageClient` render lại. Vì
   `HomePageClient` chỉ subscribe context qua `useHomeT()` (không có state/prop nào khác biến thiên),
   lần re-render DUY NHẤT xảy ra chính là khi `locale` context đổi — tức là lần mà việc tính lại
   `awards` là **cần thiết thật**, không phải overhead thừa. Kết quả: không sai dữ liệu, nhưng
   `useMemo` không chặn được bất kỳ lần tính toán thừa nào trong thực tế — nó là optimization ảo, và
   comment dòng 36-37 ("đổi VI/EN là dựng lại đúng một lần, không phải mỗi lần render") suy diễn sai
   nguyên nhân (ngụ ý có nhiều lần render không cần tính lại, nhưng thực ra không có lần nào như vậy
   xảy ra được với component này). Đề xuất: bỏ `useMemo`, gọi thẳng
   `buildFigmaAwardMock(t)` trong thân hàm — code ngắn hơn, không mất tính đúng, và không còn comment
   gây hiểu lầm. Nếu muốn giữ memo hoá thật, đổi dependency array sang giá trị `locale` (ổn định hơn
   `t`) và để `buildFigmaAwardMock` tự đọc dictionary theo locale.
   **Vị trí:** `components/home/home-page-client.tsx:34-38`.

## Suggestion

1. **`aria-live="polite"` trên `CountdownDigits` (`countdown-digits.tsx:99-104`)** phát lại toàn bộ
   chuỗi `srText` mỗi phút suốt nhiều ngày đếm ngược — không phải bug (không đọc lặp 2 lần cùng lúc vì
   lưới số đã `aria-hidden`), nhưng tần suất polite mỗi 60s trong nhiều ngày có thể gây phiền cho
   người dùng screen reader. Có thể chấp nhận vì đây đã là tần suất thấp nhất trong 2 biến thể
   countdown (Prelaunch đếm giây). Nếu muốn êm hơn: chỉ update `aria-live` region khi đơn vị hiển thị
   (giờ/ngày) đổi, giữ nguyên phút không kèm live announce.

2. **`mix-blend-screen` ở `award-card.tsx:68`** cho kết quả đúng CHỈ khi nền cha luôn gần đen
   (`#00101A`, theo đúng comment tác giả đã ghi). Đây là coupling ngầm giữa `AwardCard` và nền trang
   — nếu một phase sau tái dùng component này trong khối có nền sáng hơn, màu sẽ bị rửa trôi mà
   không có gì báo lỗi ở build/lint. Đã được ghi chú tốt trong code; chỉ cần các phase sau đọc đúng
   comment trước khi tái dùng.

3. **`public/home/keyvisual-bg.png` nặng 4.4MB, tải với `priority`** — `next/image` sẽ tối ưu định
   dạng/kích thước lúc serve nên không ảnh hưởng bytes gửi cho client, nhưng file nguồn lớn làm tăng
   thời gian build/cache đầu và dung lượng repo. Có thể nén trước khi commit (không chặn).

## Đối chiếu các điểm tự nghi ngờ trong yêu cầu

- **`figma-award-mock.ts` + `useMemo`:** đúng — xem Warning #3. `t` đổi identity mỗi render, nhưng
  không gây sai dữ liệu vì render chỉ xảy ra đúng lúc cần tính lại.
- **z-âm + `isolate` + `overflow`:** đã rà toàn bộ 3 chỗ dùng z-âm (`home-page.tsx` 2 lớp,
  `sun-kudos-section.tsx` 1 lớp). Cả ba đều tránh đúng bẫy đã mô tả: `home-page.tsx` KHÔNG có
  `overflow-x-hidden` một trục; `sun-kudos-section.tsx` dùng `overflow-hidden` CẢ HAI trục (không
  sinh `auto`) + `isolate` — an toàn, đúng khuôn với `login-screen.tsx`. Không tìm thấy hồi quy.
- **`countdown-digits.tsx` accessibility:** `srText` được tính lại mỗi render từ `remaining` hiện tại
  nên luôn cập nhật đúng theo thời gian thật (không static). Không đọc lặp trong CÙNG một lần thông
  báo (lưới số `aria-hidden`), tần suất polite mỗi phút là tradeoff chấp nhận được — xem Suggestion #1.
- **`award-card.tsx` mix-blend-screen:** xem Suggestion #2 — đúng như nghi ngờ, có phụ thuộc ngầm vào
  nền cha, nhưng đã tài liệu hoá đầy đủ trong code, rủi ro thấp ở phạm vi hiện tại.
- **`notification-bell.tsx` onClick optional:** đây là điểm hoãn có chủ đích, đúng với "Ngoài phạm vi"
  của `phase-08-ui-homepage-saa.md` ("chỉ dựng icon + badge, không làm dữ liệu — gap #14 còn treo").
  Không phải stub che giấu — comment giải thích rõ lý do và trạng thái.
- **`home-page-client.tsx` 3 callback rỗng:** cũng là điểm hoãn có chủ đích khớp plan (phase-16 nối
  dây). Tên hàm rõ ràng, comment nêu đích danh phase sẽ lấp — đúng cách trình bày, không phải cheat
  để qua mắt review.
- **`site-footer.tsx` đảo thứ tự DOM + màn `/login`:** đã đọc diff — bản TRƯỚC phase-08 dùng
  `justify-between` với đúng MỘT con (`copyright`) nên chữ bị dạt trái (bug đã tồn tại từ phase-06/07).
  Bản phase-08 thêm `hasSides` (dòng 38-39): `/login` chỉ truyền `copyright` → `hasSides=false` →
  `justify-center` → chữ về đúng giữa. Đây là **fix một bug cũ**, không phải hồi quy mới.

## Done Well

- Toàn bộ file có docblock trích toạ độ Figma cụ thể (node id, số đo, phép tính khớp/lệch) — review
  xác minh được ngay từng quyết định bố cục thay vì phải đoán.
- Bàn giao kiểm soát 5 file dùng chung (`fonts.ts`, `site-header.tsx`, `site-footer.tsx`,
  `countdown-timer.tsx`, `login-screen.tsx`) đều ghi rõ "Bàn giao kiểm soát phase-06 → phase-08" kèm lý
  do, và diff xác nhận đúng tinh thần "sửa tối thiểu, không phá hành vi cũ".
  `useCountdownRemaining` tách 1:1 từ logic gốc — xác minh bằng `git log -p`, không có sai lệch.
  `login-screen.tsx` đổi từ private `justify-between` sang `hasSides` một cách an toàn (self-tested).
- Không có import cấm nào lọt vào Track A (grep xác nhận), i18n VI/EN khớp tuyệt đối, không phá
  `get-dictionary.ts`, không tạo `middleware.ts`, không hardcode width Figma làm cứng.
- 3 điểm hoãn có chủ đích (notification bell, 3 callback rỗng, mock award data) đều đặt tên rõ ràng để
  `grep` ra ngay ở phase-16, đúng tinh thần "không stub che giấu".

## Actions In Order

1. Xoá `public/home/.claude/` và `public/home/kv-preview.png` trước khi commit/stage `public/home/**`
   (Warning #2 — rủi ro rò rỉ + rác asset).
2. Tách `components/home/home-page.tsx` xuống dưới 200 dòng, ví dụ đưa phần compose header
   (dòng 74-155) ra `home-page-header.tsx` (Warning #1).
3. Bỏ `useMemo` thừa ở `home-page-client.tsx:38` hoặc sửa lại comment cho khớp thực tế (Warning #3).
4. (Không chặn) Cân nhắc Suggestion #1-3 khi có thời gian.

## Numbers
- Type coverage: `tsc --noEmit` sạch (0 lỗi) trên toàn repo.
- Lint: 0 lỗi trên phạm vi phase-08 (eslint scoped run).
- File > 200 dòng: 1/19 (`home-page.tsx`, 213 dòng).
- i18n key parity: 42/42 khớp VI/EN.

## Still Unresolved
- Không có câu hỏi mở nào cần người khác trả lời — 2 action dọn dẹp (public rác) + 1 action tách file
  + 1 sửa comment/useMemo là đủ để đóng phase này ở mức sạch.

**Status:** DONE_WITH_CONCERNS
**Summary:** Không có Critical. 3 Warning: rác agent-memory + ảnh preview lạc vào `public/home` (cần dọn trước commit vì `public/` được serve công khai), `home-page.tsx` vượt 200 dòng, và `useMemo` ở `home-page-client.tsx` không có tác dụng thực (không sai dữ liệu, chỉ optimization ảo + comment sai). Mọi ràng buộc bắt buộc (không import lib/data|actions|supabase, không middleware, i18n khớp, không hardcode width, hành vi CountdownTimer không đổi) đều đạt, đã tự kiểm độc lập chứ không chỉ tin self-check.
**Concerns/Blockers:** Nên dọn `public/home/.claude/` + `kv-preview.png` trước khi commit (rủi ro rò rỉ dữ liệu nếu tái diễn ở lần chạy agent sau). Không blocking để merge nếu dọn kịp trước commit.
