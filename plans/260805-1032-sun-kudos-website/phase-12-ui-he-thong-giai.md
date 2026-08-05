# Phase 12 — UI Hệ thống giải (Awards Information)

## MoMorph refs:
- Hệ thống giải: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/zFYDgyj_pD
- Clarifications: plans/260805-1032-sun-kudos-website/clarifications.md

**Track:** A · **P2** · pending · **2h** · phụ thuộc: phase-06 (nội bộ Track A). Không phụ thuộc Track B.
**File ownership:** `app/awards/page.tsx`, `components/awards/**`, `lib/content/awards.ts`, `locales/*/awards.json`

## Mục tiêu
Dựng UI `/awards` qua skill `momorph-implement-design`; nội dung 6 hạng mục giải là **hằng số tĩnh trong repo**, không bảng DB (clarifications gap #10).

## Ghi chú
- `lib/content/awards.ts` do phase này sở hữu: mảng 6 phần tử `{slug, title, description, quantityLabel, prizeValueLabel, imageUrl, sortOrder}`, `slug = kebab-case(title)` (gap #16).
- Nội dung gốc lấy từ `research/momorph/csv/spec-he-thong-giai-zFYDgyj_pD.csv` item D.1–D.6: Top Talent (10 đơn vị, 7.000.000đ) · Top Project (02 tập thể, 15.000.000đ) · Top Project Leader (03 cá nhân, 7.000.000đ) · Best Manager (01 cá nhân, 10.000.000đ) · Signature 2025 - Creator (01, 5.000.000đ cá nhân / 8.000.000đ tập thể) · MVP (01, 15.000.000đ).
- Homepage (phase-08) nhận mảng này qua prop — phase-16 nối, phase-08 **không** import trực tiếp.

## Ngoài phạm vi
- Admin CRUD giải thưởng — không có trong MVP.

## Integration contract
- `<AwardsPage awards activeSlug onNavigate />` — scrollspy tự quản lý trong component
- Anchor: `#${slug}`, cuộn tới khi vào trang kèm hash (từ thẻ giải ở Homepage)

## Acceptance
- Render đủ: keyvisual banner, tiêu đề section, menu trái 6 mục có active state + gạch chân, 6 thẻ giải đầy đủ số lượng + giá trị, block CTA Sun* Kudos ở cuối.
- Mở `/awards#top-talent` từ Homepage → cuộn đúng thẻ, mục menu tương ứng active.
- Cuộn tay qua các thẻ → mục menu active đổi theo.
- Đổi VN/EN đổi hết chuỗi chrome; tên hạng mục giữ nguyên như spec.
