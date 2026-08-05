# Phase 10 — UI Viết Kudo (modal)

## MoMorph refs:
- Viết Kudo: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/ihQ26W78P2
- Addlink Box (đã dựng ở phase-06): https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/OyDLDuSGEa
- Clarifications: plans/260805-1032-sun-kudos-website/clarifications.md

**Track:** A · **P1** · pending · **3h** · phụ thuộc: phase-06 (nội bộ Track A). Không phụ thuộc Track B.
**File ownership:** `components/kudo-compose/**`, `locales/*/compose.json`

## Mục tiêu
Dựng modal Viết Kudo (26 spec item, 57 test case) qua skill `momorph-implement-design`; mock data lấy từ chính Figma. Không có route riêng — là modal.

## Ghi chú bắt buộc & ngoài phạm vi
- **Bỏ field nhập tên ẩn danh** (clarifications gap #4): checkbox "Gửi ẩn danh" bật/tắt, không hiện text field nào thêm.
- Validation ở đây chỉ phục vụ trải nghiệm; luật thật do server ép (phase-04).
- Autocomplete người nhận thật, upload ảnh thật, gửi thật → prop callback, phase-16 nối.

## Integration contract
- `<ComposeKudoModal open onClose onSubmit searchSunners hashtags presetRecipient? submitting errors />` — bọc trong `ModalShell` (phase-06), **không** tự dựng backdrop/Esc/scroll-lock. `draft` **không có** `mentionIds` (bảng `kudos_mentions` đã bỏ khỏi MVP; `@mention` sống trong `body` dạng text)
- `presetRecipient?: Profile | null` — mặc định `null`; profile người khác truyền vào để pre-fill (TC_WEB_PROFILE_FUN_007), homepage/board không đổi
- `onSubmit(draft) => Promise<{ok, fieldErrors?}>` — `draft = {recipientId, body, hashtagIds, images, isAnonymous}`
- `searchSunners(q) => Promise<Profile[]>` — autocomplete, tối thiểu 1 ký tự. Dùng lại `MultiHashtagPicker` + `AddLinkDialog` từ phase-06

## Acceptance
- Người nhận rỗng → chặn gửi; 0 hashtag → chặn; chọn hashtag thứ 6 → không chọn được.
- Chọn 6 ảnh → ảnh thứ 6 bị từ chối; chọn `.pdf`/`.mp4`/`.txt` → hiện lỗi loại tệp.
- Rich text đủ bold/italic/stroke/số/link/quote/@mention; nút link mở `AddLinkDialog`.
- Bật "Gửi ẩn danh" → **không** xuất hiện ô nhập tên nào.
- Nút Hủy đóng modal không gửi; đổi VN/EN đổi hết chuỗi kể cả thông báo lỗi.
