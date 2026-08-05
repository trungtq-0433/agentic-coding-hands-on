# Phase 09 — UI Sun* Kudos Live board

## MoMorph refs:
- Sun* Kudos - Live board: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/MaZUn5xHXZ
- Clarifications: plans/260805-1032-sun-kudos-website/clarifications.md

**Track:** A · **P1** · pending · **4h** · phụ thuộc: phase-06 (nội bộ Track A). Không phụ thuộc Track B.
**File ownership:** `app/kudos/page.tsx`, `components/board/**`, `locales/*/board.json`

## Mục tiêu
Dựng UI `/kudos` (màn trọng tâm, 64 spec item) qua skill `momorph-implement-design`; mock data lấy từ chính Figma.

## Ngoài phạm vi
- Query, keyset pagination, realtime, thả tim thật → Track B, nối ở phase-16.
- Số tim **không** tự tăng lạc quan — hiển thị đúng giá trị prop trả về (TC_WEB_PROFILE_FUN_014).
- Modal Viết Kudo (phase-10), Thể lệ (phase-13), Open Secret Box (phase-15) — chỉ gọi callback mở. Sidebar: `unopenedCount = 0` → nút "Mở quà" **disabled**.

## Integration contract
- `<BoardPage highlights allKudos filters sidebar onFilterChange onLoadMore onToggleHeart onCopyLink onOpenProfile onCompose onOpenBox newKudosQueue onFlushQueue />`
- `onToggleHeart(kudosId) => Promise<{ok, hearted?, heartCount?, code?}>` — UI lấy con số từ kết quả; `ok:false` thì giữ nguyên trạng thái cũ và hiện toast lỗi
- `kudo-card` có prop **`pending`** → disable icon tim khi đang gọi, chặn double-click sinh race ở server
- `onLoadMore(cursor) => Promise<{items, nextCursor}>` — infinite scroll · `newKudosQueue: number` → dải "Có N kudo mới", bấm gọi `onFlushQueue`
- Card kudos export riêng `components/board/kudo-card.tsx` để phase-11 dùng lại nguyên vẹn (TC_WEB_PROFILE_GUI_006)
- Kudo ẩn danh: hiển thị **nhãn cố định**, không có tên tự nhập (clarifications gap #4)

## Acceptance
- Render đủ: banner + ô mở form, Highlight carousel 5 card + 2 nút + chỉ số trang, filter Hashtag/Phòng ban, Spotlight (tổng kudos, pan/zoom, ô tìm ≤100 ký tự), All Kudos infinite scroll, sidebar 5 chỉ số + nút Mở quà + 2 leaderboard, footer.
- Carousel ở card 1 disable nút lùi, ở card 5 disable nút tiến. Copy Link hiện toast "Link copied — ready to share!".
- Bấm tim liên tiếp 5 lần thật nhanh → chỉ **một** lời gọi rời đi (nhờ `pending`), UI không nháy qua lại.
- `grep -rn "lib/supabase\|lib/data\|lib/actions" components/board/` trả rỗng.
