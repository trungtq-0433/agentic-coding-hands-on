# Sun* Kudos (SAA 2025)

Website ghi nhận và lan toả Kudos nội bộ Sun\*, xây trên Next.js 16 (App Router) và Supabase (chạy local qua Docker). Chi tiết yêu cầu và kiến trúc: [`plans/260805-1032-sun-kudos-website/plan.md`](./plans/260805-1032-sun-kudos-website/plan.md).

> Dự án đang ở **phase-03/17** (nền tảng Supabase + Next, schema/RLS, và auth Google OAuth đã xong; UI 18 màn còn ở phase sau). Xem tiến độ đầy đủ trong `plan.md`.

## Yêu cầu môi trường

- Node.js (bản LTS gần nhất) và npm.
- **Docker đang chạy** — Supabase local dựng trên container, không có Docker thì `supabase start` fail ngay. Kiểm bằng `docker info`.

## Cài đặt lần đầu

```bash
# 1. Cài dependency
npm install

# 2. Tạo file env từ template
cp .env.local.example .env.local
cp .env.example .env

# 3. Điền credential Google OAuth (bắt buộc — auth chỉ có một nút "Đăng nhập
#    Google", không có email/password) vào .env, biến
#    SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID / _SECRET. Xin giá trị thật từ
#    người giữ OAuth client của dự án (PRE-REQ-01 trong plan.md) — KHÔNG tự
#    tạo OAuth client riêng, redirect URI đã đăng ký cố định là
#    http://localhost:54321/auth/v1/callback và dùng chung cho mọi máy local
#    (port 54321 cố định trong supabase/config.toml).
#    Lưu ý: đây là file .env (CLI Supabase đọc), KHÁC với .env.local (Next.js
#    đọc) ở bước trên — xem chú thích trong .env.example.

# 4. Dựng Supabase local (Docker phải chạy trước; lần đầu kéo vài GB image, mất vài phút)
npm run supabase:start

# 5. Copy URL + key mà lệnh trên IN RA vào .env.local
#    Tên biến/key thay đổi theo version CLI — lấy NGUYÊN VĂN từ output,
#    đừng chép từ tài liệu. Xem chú thích trong .env.local.example.

# 6. Sinh type Supabase (chạy lại sau mỗi lần đổi migration)
npm run supabase:types

# 7. Chạy dev server
npm run dev
```

Mở [http://localhost:3000](http://localhost:3000).

## Script

| Lệnh | Việc gì |
|---|---|
| `npm run dev` | Next dev server |
| `npm run build` | Build production (Turbopack) |
| `npm run start` | Chạy bản đã build |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run lint` | ESLint (`eslint`) |
| `npm run supabase:start` | Dựng stack Supabase local |
| `npm run supabase:stop` | Hạ stack |
| `npm run supabase:reset` | Reset DB về migrations + seed — **xoá sạch dữ liệu** |
| `npm run supabase:types` | Sinh lại `lib/supabase/database.types.ts` |

Supabase CLI không cài global trong repo này — mọi script gọi qua `npx supabase`.

> **Lưu ý về `npm run lint`:** lệnh này hiện đang đỏ khi chạy trên toàn repo, do lỗi có từ trước ở `.claude/hooks/*.cjs` (phần harness Claude Code, không phải code app). Code Sun\* Kudos (`app/`, `lib/`, `proxy.ts`) tự lint sạch — chạy riêng `npx eslint app lib proxy.ts` nếu cần kiểm code app.

## Vận hành sự kiện (countdown, Secret Box, key Supabase)

Xem [`docs/runbook-su-kien.md`](./docs/runbook-su-kien.md) — đặc biệt phần đổi mốc countdown, vì biến `NEXT_PUBLIC_*` bị nhúng vào bundle lúc build và **bắt buộc `npm run build` lại**, restart process không đủ.
