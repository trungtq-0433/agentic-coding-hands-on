# Phase 07 — UI Login

## MoMorph refs:
- Login: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/GzbNeVGJHz
- Clarifications: plans/260805-1032-sun-kudos-website/clarifications.md

**Track:** A · **P2** · pending · **1h** · phụ thuộc: phase-06 (nội bộ Track A). Không phụ thuộc Track B.
**File ownership:** `app/login/page.tsx`, `components/login/**`, `locales/*/login.json`

## Mục tiêu
Dựng UI trang `/login` qua skill `momorph-implement-design`; mock data lấy từ chính Figma.

## Ngoài phạm vi
- OAuth thật, session, redirect về `/` — Track B phase-03, nối ở phase-16.
- Chặn user đã đăng nhập vào `/login` — do `proxy.ts` xử lý, không làm ở UI.
- **Đúng một nút Google**, không có form email/password, không có ô nhập domain (spec item 2.2.1).

## Integration contract
- `components/login/login-screen.tsx`: `<LoginScreen onGoogleLogin errorCode?/>`
- `onGoogleLogin: () => void` (async, phase-16 truyền `signInWithGoogle`)
- `errorCode?: 'oauth'` → hiện dải lỗi; đọc từ `searchParams` (**`await searchParams`** — Next 16 là Promise)
- Header dùng lại `SiteHeader` (logo + `LanguageSwitcher`), footer dùng `SiteFooter` (copyright)

## Acceptance
- `/login` render đủ header, hero, nút "LOGIN With Google", footer; đổi VN/EN chuyển hết chuỗi.
- Bấm nút gọi đúng `onGoogleLogin`; không import gì từ `lib/`.
- `?error=oauth` hiện thông báo lỗi ở cả hai ngôn ngữ.
