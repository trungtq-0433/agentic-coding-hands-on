# Phase 15 — UI Open Secret Box (modal)

## MoMorph refs:
- Open secret box - chưa mở: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/J3-4YFIpMM
- Clarifications: plans/260805-1032-sun-kudos-website/clarifications.md

**Track:** A · **P2** · pending · **1h** · phụ thuộc: phase-06 (nội bộ Track A). Không phụ thuộc Track B.
**File ownership:** `components/secret-box/**`, `locales/*/secret-box.json`

## Mục tiêu
Dựng modal "MỞ SECRET BOX THÀNH CÔNG" qua skill `momorph-implement-design`. Là modal, không có route riêng.

## Ghi chú & ngoài phạm vi
- Số hộp chưa mở và huy hiệu **luôn đến từ prop do server trả về** — TC bảo mật cấm tính/lưu ở client. Không bộ đếm cục bộ, không tự trừ.
- Random có trọng số là việc của RPC (phase-04); UI **không** biết tỉ lệ 30/25/10/5/20/10. Rule cấp phát hộp còn treo (gap #9). Gọi RPC thật → phase-16 nối.

## Integration contract
- `<SecretBoxModal open onClose onOpenBox remaining lastBadge opening errorCode? />` — bọc trong `ModalShell` của phase-06, **không** tự dựng backdrop/Esc/scroll-lock
- `onOpenBox() => Promise<{badge, remaining}>` — UI cập nhật cả hai giá trị từ kết quả trả về
- `errorCode?: 'NO_UNOPENED_BOX'` → hiện thông báo hết hộp
- `opening: boolean` → disable box khi đang gọi (chống double-click double-open)

## Acceptance
- Hiện tiêu đề, hình hộp mở kèm huy hiệu nhận được, dòng "Click vào box để tiếp tục mở", số hộp chưa mở ở đáy.
- `remaining = 0` → **ẩn** dòng hướng dẫn và không cho bấm tiếp.
- Đang gọi `onOpenBox` → box disabled, không phát sinh lời gọi thứ hai.
- Con số hiển thị luôn bằng `remaining` từ prop, không có state đếm nội bộ (kiểm bằng cách truyền prop nghịch lý và xác nhận UI theo prop).
- Đổi VN/EN đổi hết chuỗi.
