# Phase 08 — UI Homepage SAA

## MoMorph refs:
- Homepage SAA: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/i87tDx10uM
- Clarifications: plans/260805-1032-sun-kudos-website/clarifications.md

**Track:** A · **P1** · pending · **3h** · phụ thuộc: phase-06 (nội bộ Track A). Không phụ thuộc Track B.
**File ownership:** `app/page.tsx` (ghi đè bản create-next-app), `components/home/**`, `locales/*/home.json`

## Mục tiêu
Dựng UI trang chủ `/` qua skill `momorph-implement-design`; mock data lấy từ chính Figma.

## Ghi chú bắt buộc đọc
- Design màn này còn `in_progress` — **đã chốt code theo bản hiện tại** (clarifications). Cô lập mọi thứ trong `components/home/**` để bản design mới không lan ra ngoài.
- Countdown Homepage đếm **theo phút** (`tickMs={60000}`), khác Prelaunch (theo giây). Về 0 → ẩn "Coming soon", giữ nguyên `00`.

## Ngoài phạm vi
- Nguồn `NEXT_PUBLIC_EVENT_START_AT` → prop `targetIso`. Nội dung 6 hạng mục giải → prop, dữ liệu tĩnh do phase-12 sở hữu.
- Notification bell: chỉ dựng icon + badge, **không** làm dữ liệu (gap #14 còn treo).

## Integration contract
- `<HomePage targetIso awards profile isAdmin onCompose onRules onSignOut />`
- Thẻ giải: click → `/awards#${slug}` với `slug = kebab-case(title)` (clarifications gap #16)
- Dùng lại `SiteHeader`/`SiteFooter`/`CountdownTimer`/`KudosFab` từ phase-06

## Acceptance
- `/` render đủ: header, keyvisual + countdown 3 ô Days/Hours/Minutes, thông tin sự kiện, 2 CTA, block Root Further, lưới 6 thẻ giải, block Sun* Kudos, FAB, footer.
- Guest xem được toàn bộ nội dung (không chặn gì ở UI).
- Countdown nhích đúng 1 lần/phút; qua mốc → hiện `00 00 00`, không âm.
- Đổi VN/EN đổi hết chuỗi; không import gì từ `lib/data`, `lib/actions`, `lib/supabase`.
