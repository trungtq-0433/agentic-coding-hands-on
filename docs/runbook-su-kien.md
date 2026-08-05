# Runbook vận hành — Sun* Kudos (SAA 2025)

## Đổi mốc thời gian countdown

Có hai mốc độc lập:

| Biến | Điều khiển |
|---|---|
| `NEXT_PUBLIC_LAUNCH_GATE_AT` | Cổng chặn toàn site. Trước mốc này mọi URL đá về `/prelaunch`. |
| `NEXT_PUBLIC_EVENT_START_AT` | Countdown hiển thị trên Homepage. |

Định dạng: ISO-8601 kèm offset `+07:00`, ví dụ `2025-11-20T09:00:00+07:00`.

### Quy trình

```
1. sửa giá trị trong .env.local
2. npm run build      ← BẮT BUỘC, không được bỏ
3. npm start
```

### Vì sao bước 2 không bỏ được

Biến `NEXT_PUBLIC_*` **bị nhúng thẳng vào bundle JavaScript lúc `next build`**, không đọc lại lúc chạy. Doc Next.js nói rõ:

> "After being built, your app will no longer respond to changes to these environment variables… all `NEXT_PUBLIC_` variables will be frozen with the value evaluated at build time"
> — `node_modules/next/dist/docs/01-app/02-guides/environment-variables.md:166`

Sửa `.env.local` rồi chỉ restart process thì **giá trị cũ vẫn nằm trong bundle đã gửi xuống trình duyệt**. Triệu chứng: countdown không nhúc nhích, hoặc cổng chặn mở/đóng sai giờ — và không có lỗi nào hiện ra để lần.

Đây là cái giá đã chấp nhận khi chọn env var thay vì bảng `event_config` (quyết định gap #1 trong `plans/260805-1032-sun-kudos-website/clarifications.md`). Không phải bug.

### Kiểm chứng

```bash
npm run build && npm start
# đổi NEXT_PUBLIC_LAUNCH_GATE_AT trong .env.local
# restart process  → countdown KHÔNG đổi   ← đúng như mô tả trên
npm run build && npm start
#                 → countdown ĐỔI
```

## Supabase local

```bash
npm run supabase:start    # dựng stack (Docker phải chạy trước)
npm run supabase:stop     # hạ stack
npm run supabase:reset    # reset DB về migrations + seed — XOÁ SẠCH dữ liệu
npm run supabase:types    # sinh lại lib/supabase/database.types.ts sau mỗi migration
```

Studio: http://127.0.0.1:54323 · API: http://127.0.0.1:54321 · DB: `postgresql://postgres:postgres@127.0.0.1:54322/postgres` · Mailpit: http://127.0.0.1:54324

Key lấy **nguyên văn** từ output `npx supabase start` — tên key đổi theo version CLI. Bản hiện tại in ra cả `PUBLISHABLE_KEY` (định dạng mới `sb_publishable_…`) lẫn `ANON_KEY` (JWT legacy); dự án dùng cái đầu, biến `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.

`SECRET_KEY` / `SERVICE_ROLE_KEY` **không bao giờ** mang tiền tố `NEXT_PUBLIC_` và chưa dùng tới ở giai đoạn này.

## Chuẩn bị máy trước khi chạy lần đầu

1. Docker đang chạy — kiểm bằng `docker info`. Không có Docker thì `supabase start` fail ngay.
2. Lần đầu `supabase start` phải kéo vài GB image, mất nhiều phút.
3. `cp .env.local.example .env.local` rồi điền key thật từ output.
