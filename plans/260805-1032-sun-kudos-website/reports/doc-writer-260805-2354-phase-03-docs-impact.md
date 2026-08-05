# Tác động tài liệu — phase-03 (Google OAuth + tầng auth)

## Verdict

| # | Điểm | Verdict | File đã sửa |
|---|---|---|---|
| 1 | Hai file env (`.env` vs `.env.local`), credential Google chỉ ở `.env` | **Cập nhật** | `README.md` |
| — | (phát hiện thêm) Banner tiến độ README ghi sai phase | **Cập nhật** | `README.md` |
| 2 | `redirect_uri` tường minh trong `config.toml` | **Không cần** | — |
| 3 | Tự tạo OAuth client cho dev khác | **Không cần — tiền đề sai** | — |

## Đã sửa: README.md

1. Banner tiến độ (dòng 5) nói "phase-01/17 … schema, auth … còn ở phase sau" — sai, vì `plan.md`
   ghi rõ phase-01, 02, 03 đều `completed` (3/17, 12h/63h). Sửa thành phase-03/17, auth đã xong.
2. Thêm bước 2-3 vào "Cài đặt lần đầu": `cp .env.example .env` + điền credential Google OAuth vào
   biến `SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID`/`_SECRET`, có ghi chú `.env` khác `.env.local`.
   Không dán giá trị credential thật. Đánh số lại bước 3→7.

**Lý do cần:** README hiện tại (trước sửa) không nhắc gì đến `.env` — người mới clone chỉ biết
`.env.local`. Auth Google là **luồng đăng nhập duy nhất** (spec Login 2.2.1, không email/password),
nên đây không phải chi tiết phụ. `.env.example` và comment trong `config.toml` đã giải thích kỹ,
nhưng README là nơi người mới đọc đầu tiên và hiện bỏ sót hoàn toàn bước này.

**Chưa xác nhận (nêu rõ để không đoán):** không re-test bằng cách dừng/khởi động lại stack Supabase
xem thiếu `.env` có làm `supabase:start` gãy cứng hay chỉ làm nút Google không hoạt động — vì stack
local đang chạy dở (một số service đã stopped: `imgproxy`, `pooler`) và không muốn phá trạng thái
đang dùng. Dựa vào hồ sơ Red Team Review trong `plan.md` (finding #20, severity Warning, đã fix bằng
comment trong `.env.example`) để suy ra đây không phải lỗi chặn cứng toàn bộ stack — nhưng README vẫn
cần nhắc vì Google là đường đăng nhập duy nhất.

## Không cần sửa: điểm #2 (redirect_uri)

`supabase/config.toml:342-353` đã có giá trị đúng (`http://localhost:54321/auth/v1/callback`,
committed) kèm comment giải thích đầy đủ cơ chế lỗi + cách đã kiểm chứng (`curl
/auth/v1/authorize?provider=google`). Giá trị này **cố định trong file được commit** — dev bình
thường không bao giờ phải sờ vào, tự động có đúng khi clone. Không có lý do đưa vào README (không
phải bước setup) hay runbook (không phải việc vận hành lặp lại — đây là hằng số kiến trúc, không phải
biến người vận hành đổi). Giữ nguyên ở code comment là đủ, thêm ở docs sẽ là tài liệu trùng lặp không
ai đọc (vi phạm YAGNI).

## Không cần sửa: điểm #3 (tự tạo OAuth client riêng)

Tiền đề trong yêu cầu ("ai clone repo muốn chạy auth trên máy họ cần OAuth client riêng") **không
đúng với kiến trúc hiện tại**, đã kiểm bằng đọc code:

- `supabase/config.toml:10` — port API cố định `54321` cho mọi máy local (không random).
- `plan.md:58` — PRE-REQ-01 là **một** OAuth client dùng chung, redirect URI
  `http://localhost:54321/auth/v1/callback` — do port cố định, URI này giống nhau trên mọi máy dev,
  nên **một client dùng chung được cho tất cả**, không cần mỗi người tự tạo client riêng.

Việc dev cần là **giá trị credential** (client_id/secret) của client đã có, không phải hướng dẫn tạo
client mới. Nhưng kênh phân phối giá trị đó (Slack? 1Password? ai giữ?) **không xuất hiện ở đâu trong
code/plan** — `plan.md:58` chỉ ghi "ĐÃ GIAO và HOÀN THÀNH" cho người tạo client, không nói cách người
tiếp theo xin lại giá trị. Đây là khoảng trống thật, nhưng viết hướng dẫn "tự tạo OAuth client" vào
README sẽ là **thông tin sai** (khuyến khích tạo thêm client không cần thiết, có thể gây nhầm redirect
URI). Đã sửa README bước 3 để nói đúng: xin giá trị từ người giữ client, không tự tạo. Không thêm gì
khác vì kênh phân phối cụ thể không có trong bất kỳ nguồn nào tôi được phép trích dẫn — bịa ra sẽ vi
phạm nguyên tắc "không đoán".

## docs/runbook-su-kien.md

Không sửa. File này là vận hành sự kiện (countdown, Secret Box) — không có mục troubleshooting auth,
và không cần thêm vì cả 3 điểm trên hoặc đã có chỗ đúng (code comment / README) hoặc không cần tài
liệu (điểm 2), hoặc tiền đề sai (điểm 3).

## Câu hỏi còn treo

- Kênh phân phối credential Google OAuth thật cho dev mới (Slack channel? 1Password vault?) chưa có
  ở đâu trong repo. Nếu có, nên bổ sung một dòng vào README bước 3 trỏ tới đúng kênh đó — hiện để
  placeholder "xin người giữ OAuth client" vì không có tên kênh cụ thể để trích dẫn.
- `plan.md:58` (PRE-REQ-01) vẫn ghi credential đặt vào `.env.local`/biến `GOOGLE_CLIENT_ID` —
  đã lỗi thời so với code thật (`.env`, biến `SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID`, xác nhận qua
  Red Team finding #20 trong cùng file). Không sửa vì `plans/` là việc của project-manager, chỉ nêu
  ở đây để người phụ trách plan biết.

**Status:** DONE
**Summary:** Sửa `README.md` — cập nhật banner tiến độ (phase-03/17) và thêm bước tạo `.env` +
điền credential Google OAuth (khác `.env.local`), không dán giá trị thật. Điểm redirect_uri (#2) và
tự-tạo-OAuth-client (#3) không cần tài liệu hoá: #2 đã đúng và có comment đầy đủ trong
`supabase/config.toml` (committed, dev không cần sờ); #3 dựa trên tiền đề sai — port 54321 cố định
nên một OAuth client dùng chung đủ cho mọi máy, không cần tự tạo riêng.
**Concerns:** (1) Không re-test thực nghiệm việc thiếu `.env` có chặn cứng `supabase:start` hay
không — dựa vào hồ sơ Red Team trong `plan.md` (finding #20, Warning) thay vì tự thử, để tránh phá
trạng thái stack đang chạy dở. (2) `plan.md:58` có thông tin lỗi thời về vị trí credential — ngoài
phạm vi sửa của agent này, đã nêu ở mục "Câu hỏi còn treo".
