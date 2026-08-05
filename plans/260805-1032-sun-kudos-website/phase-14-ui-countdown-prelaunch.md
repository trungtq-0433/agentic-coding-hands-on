# Phase 14 — UI Countdown Prelaunch

## MoMorph refs:
- Countdown - Prelaunch page: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/8PJQswPZmU
- Clarifications: plans/260805-1032-sun-kudos-website/clarifications.md

**Track:** A · **P2** · pending · **1h** · phụ thuộc: phase-06 (nội bộ Track A). Không phụ thuộc Track B.
**File ownership:** `app/prelaunch/page.tsx`, `components/prelaunch/**`, `locales/*/prelaunch.json`

## Mục tiêu & ghi chú
Dựng trang chặn toàn màn hình `/prelaunch` qua skill `momorph-implement-design`.
- Đếm **mỗi giây** (`tickMs={1000}`), khác Homepage (mỗi phút). TZ `Asia/Ho_Chi_Minh`.
- Nguồn mốc thời gian: `NEXT_PUBLIC_LAUNCH_GATE_AT` — Server Component đọc env rồi truyền xuống prop, **không** gọi API (clarifications gap #1).
- ⚠ Biến `NEXT_PUBLIC_*` bị **inline lúc `next build`**: đổi mốc = sửa `.env` **rồi build lại**, restart KHÔNG đủ. Runbook ở phase-01.
- **Không ai bypass được** (gap #11), kể cả admin. Chặn do `proxy.ts` (phase-01), không làm ở UI.

## Ngoài phạm vi
- Logic gate và redirect — Track B phase-01. Trang này không có link, không có header nav.

## Integration contract
- `<PrelaunchScreen targetIso onReachZero />`
- `onReachZero` → phase-16 nối `router.refresh()` để server quyết định lại (client clock không được là nguồn sự thật)

## Acceptance
- Hiện 3 nhóm Days/Hours/Minutes, nhích **mỗi giây**.
- Không có link/nút điều hướng nào trên trang.
- Về 0 → gọi đúng một lần `onReachZero`, không đếm âm.
- Đổi VN/EN đổi nhãn ("Sự kiện sẽ bắt đầu sau" ↔ "Event starts in", DAYS/HOURS/MINUTES).
- `grep -rn "lib/supabase\|lib/data\|lib/actions" components/prelaunch/` trả rỗng.
