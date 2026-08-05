# Phase 11 — UI Profile bản thân

## MoMorph refs:
- Profile bản thân: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/3FoIx6ALVb
- Clarifications: plans/260805-1032-sun-kudos-website/clarifications.md

**Track:** A · **P1** · pending · **3h** · phụ thuộc: phase-06 **và phase-09** (dùng lại `kudo-card`, chain nội bộ Track A). Không phụ thuộc Track B.
**File ownership:** `app/profile/page.tsx`, `components/profile/**`, `locales/*/profile.json`

## ⚠ ĐỌC TEST CASE TRƯỚC KHI CODE
Spec màn này phần lớn ở trạng thái `draft` — **18/28 dòng trống**; hành vi thật nằm trong 30 test case.
**BẮT BUỘC đọc `plans/260805-1032-sun-kudos-website/research/momorph/csv/tc-profile-ban-than-3FoIx6ALVb.csv` trước khi viết dòng code đầu tiên.** Đừng suy đoán từ Figma.

## Mục tiêu
Dựng UI `/profile` (self) và `/profile?id=` (người khác) — hai mặt của cùng một route — qua `momorph-implement-design`.

## Ngoài phạm vi
- Query, definer view Sent-list, keyset pagination, thả tim thật → Track B, nối ở phase-16.
- Không có affordance sửa profile (TC_SEC_004). **Hero tier bỏ khỏi MVP** (gap #7) — chỉ giữ hoa-thị 10/20/50. 6 slot huy hiệu luôn xám; 2 dòng Secret Box đọc 0.

## Integration contract
- `<ProfilePage profile stats direction items onDirectionChange onLoadMore onToggleHeart onCompose />`
- `stats: Stats | null` — **`null` là tín hiệu duy nhất** quyết định self/other: `null` → thay cả thẻ 5 chỉ số bằng thanh "viết Kudo" pre-fill người nhận (TC_FUN_006/007)
- `direction: 'received' | 'sent'` — dropdown có `sent` **chỉ khi** `stats != null` (TC_SEC_001). Dùng lại nguyên `components/board/kudo-card.tsx` của phase-09, không tạo bản sao (TC_GUI_006)

## Acceptance
- `?id` là chính mình → hiện đúng như self; `?id` sai định dạng UUID → chặn trước khi query; `?id` lặp → từ chối; `?id` rỗng → self.
- Profile người khác: **không** có tab "Đã gửi", **không** có thẻ 5 chỉ số, **có** thanh viết Kudo.
- Đổi hướng nhận/gửi → nạp lại trang 1, bỏ các trang đã cuộn; chọn lại hướng đang active → no-op. Hai hướng có empty message riêng; chip "Spam" **không bao giờ** render.
- Profile chưa từng đăng nhập (không avatar/phòng ban/kudos) vẫn render không vỡ.
