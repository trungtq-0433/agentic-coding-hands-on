# Phase 13 — UI Thể lệ (panel/modal)

## MoMorph refs:
- Thể lệ UPDATE: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/b1Filzi9i6
- Clarifications: plans/260805-1032-sun-kudos-website/clarifications.md

**Track:** A · **P3** · pending · **1h** · phụ thuộc: phase-06 (nội bộ Track A). Không phụ thuộc Track B.
**File ownership:** `components/rules/**`, `lib/content/rules.ts`, `locales/*/rules.json`

## Mục tiêu
Dựng panel Thể lệ qua skill `momorph-implement-design`. Là modal, **không có route riêng** — mở từ FAB và từ footer.

## Ghi chú
- Nội dung thể lệ + danh sách thưởng + 6 huy hiệu là **nội dung tĩnh** trong `lib/content/rules.ts`, cùng lý do với awards (không có màn admin quản lý).
- Tên 6 huy hiệu khớp `badges.code` phase-02: Stay Gold · Flow to Horizon · Beyond the Boundary · Root Further · Touch of Light · Revival.

## Ngoài phạm vi
- Mở modal Viết Kudo từ nút "Viết KUDOS" — chỉ gọi callback, phase-16 nối.

## Integration contract
- `<RulesPanel open onClose onCompose content />` — bọc trong `ModalShell` của phase-06, **không** tự dựng backdrop/Esc/scroll-lock
- `content` mặc định lấy từ `lib/content/rules.ts`, cho phép override để test

## Acceptance
- Mở/đóng bằng nút "Đóng" và bằng phím Esc; nội dung dài thì cuộn được trong panel, không cuộn nền.
- Nút "Viết KUDOS" gọi `onCompose` và đóng panel.
- Hiện đủ 6 huy hiệu đúng tên; đổi VN/EN đổi hết chuỗi.
- `grep -rn "lib/supabase\|lib/data\|lib/actions" components/rules/` trả rỗng.
