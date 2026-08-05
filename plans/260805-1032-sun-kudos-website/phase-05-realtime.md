# Phase 05 — Realtime (Broadcast)

**Track:** B · **Priority:** P2 · **Status:** pending · **Effort:** 3h
**Phụ thuộc:** phase-04 · **Mở khoá:** phase-16
**KHÔNG có quan hệ blocks/blockedBy với bất kỳ phase Track A nào.**

## Context Links

- Postgres Changes vs Broadcast, ngưỡng scale, cleanup React 19: [`reports/researcher-260805-1032-nextjs16-supabase-local.md`](./reports/researcher-260805-1032-nextjs16-supabase-local.md) §6
- Yêu cầu realtime theo màn: [`reports/researcher-260805-1032-momorph-requirements-synthesis.md`](./reports/researcher-260805-1032-momorph-requirements-synthesis.md) §5
- Quyết định: `clarifications.md` gap #6 (realtime cho Live board), gap #13 (word-cloud **không** realtime)
- Trigger phát Broadcast: [`phase-02`](./phase-02-schema-migrations-rls.md) migration `0006b`, Key Insight #10

## Overview

Cung cấp hook realtime dưới dạng module độc lập, **không** gắn vào component nào. Track A vẫn đang dựng UI song song; cắm hook vào Live board là việc của phase-16.

> **Đổi hướng so với bản kế hoạch đầu:** bản đầu dùng **Postgres Changes** trên bảng `kudos`/`hearts`. Cách đó **không chạy được** với mô hình bảo mật đã chốt — xem Key Insight #1. Toàn phase này đã viết lại theo **Broadcast phát từ trigger**.

## Key Insights

1. **Postgres Changes chết vì `revoke select on kudos`.** Postgres Changes uỷ quyền từng subscriber bằng chính RLS/grant của bảng. Phase-02 thu quyền SELECT trên `kudos` với cả `anon` lẫn `authenticated` (để chặn rò `sender_id` của kudo ẩn danh), nên **không sự kiện nào tới được client**. Hai thứ loại trừ nhau, không có đường thoả hiệp.
   Hai lựa chọn: (a) bỏ `revoke` để realtime chạy — mở lại lỗ rò ẩn danh; (b) giữ `revoke`, đổi cơ chế realtime. **Đã chốt (b): an toàn thắng tiện lợi.**
2. **Broadcast không đi qua RLS của bảng** — vừa là lý do nó chạy được, vừa là lý do payload phải nghèo. Bất cứ thứ gì nhét vào payload là công khai với người nghe kênh. → payload chỉ `{kudos_id, event}`, không `sender_id`, không `body`.
3. **Vẫn là refetch-on-signal, không đổi.** Nhận tín hiệu → gọi `fetchKudoCardById` qua `public_kudos_feed`. Quyền do DB quyết. Kiến trúc này vốn đã đúng ở bản đầu; chỉ đường truyền tín hiệu là đổi.
4. **Trigger phát tín hiệu, không phải client.** `realtime.send()` gọi trong trigger DB (phase-02 `0006b`) → tín hiệu phát ra kể cả khi thay đổi đến từ SQL Editor hay seed, không chỉ từ app.
5. **Hai topic, hai phạm vi**: `kudos-board` (công khai, ai cũng nghe được — chỉ mang id) và `user-hearts:<user_id>` (riêng, đồng bộ trạng thái đã-tim giữa nhiều tab của **cùng một** user).
6. **StrictMode double-invoke không rò kênh** miễn cleanup gọi `supabase.removeChannel(channel)`.
7. Word-cloud và bộ đếm "388 KUDOS" đứng ngoài realtime (gap #13). Notification bell chưa làm (gap #14).

## Requirements

### Chức năng
- `useKudosStream()`: nhận tín hiệu `insert` trên topic `kudos-board` → refetch → `onInsert(card)`; nhận `update` → refetch → `onHeartCountChange(kudosId, heartCount)`.
- `useMyHeartsStream(userId)`: nghe topic `user-hearts:<userId>` → `onMyHeartChange(kudosId, hearted)`.
- Cờ `enabled` để tắt (tab ẩn, hoặc lúc test).
- **Guest (chưa đăng nhập) vẫn nhận được tín hiệu board** — board là public, `anon` phải nghe được `kudos-board`.

### Phi chức năng
- Không component nào trong `lib/realtime/**`; chỉ hook + hàm thuần.
- Mỗi file < 200 dòng.
- Không phụ thuộc publication `supabase_realtime` — Broadcast không cần bảng nằm trong publication.

## Architecture

```
create_kudos() / toggle_heart()   (RPC, phase-04)
        │ ghi bảng
        ▼
  trigger trg_kudos_broadcast / trg_hearts_broadcast   (phase-02, migration 0006b)
        │ realtime.send(payload CHỈ id)
        ▼
  Realtime Broadcast
   ├─ topic 'kudos-board'          → mọi client kể cả anon
   └─ topic 'user-hearts:<uuid>'   → riêng từng user
        │  WebSocket
        ▼
  lib/realtime/kudos-channel.ts        ← tạo/huỷ channel, không giữ state
  lib/realtime/use-kudos-stream.ts     ← 'use client', refetch-on-signal
  lib/realtime/use-my-hearts-stream.ts
        │ callback
        ▼
  (phase-16) components/board/*
```

**Refetch-on-signal — payload không bao giờ là nguồn dữ liệu:**

```
onSignal({kudos_id}) → fetchKudoCardById(kudos_id)    ← qua public_kudos_feed
                     → null (bị lọc/không đủ quyền) thì BỎ QUA, không hiện
```

Nhánh "null thì bỏ qua" là chỗ luật che ẩn danh được thực thi: view trả về hàng đã che, nên kudo ẩn danh đến qua realtime cũng hiện đúng nhãn cố định.

### Chèn kudo mới vào feed đang cuộn

Không chèn thẳng vào giữa danh sách keyset. Đẩy vào hàng đợi, hiện dải "Có N kudo mới — bấm để xem"; bấm mới prepend. Chèn tự động làm nhảy vị trí cuộn và phá giả định của keyset cursor.

## Related Code Files

**Tạo mới**
- `lib/realtime/kudos-channel.ts`
- `lib/realtime/use-kudos-stream.ts`
- `lib/realtime/use-my-hearts-stream.ts`
- `lib/realtime/types.ts` — kiểu callback dùng chung với phase-16

**Sửa:** `lib/data/kudos-queries.ts` (thêm `fetchKudoCardById` — phase-04 sở hữu, hai phase chain tuần tự nên bàn giao hợp lệ)

**Xoá:** không

**Không còn cần:** migration bật publication `supabase_realtime` (bản đầu dự kiến `0010_enable_realtime.sql`) — Broadcast không dùng logical replication. Trigger phát tín hiệu đã nằm trong `0006b` của phase-02.

**File ownership (glob):** `lib/realtime/**`; bàn giao có kiểm soát: thêm đúng một hàm vào `lib/data/kudos-queries.ts`.

## Implementation Steps

1. Xác nhận trigger `0006b` của phase-02 đã phát tín hiệu: mở Studio, `insert` một kudo bằng SQL, quan sát Realtime Inspector thấy message trên `kudos-board`.
2. `lib/realtime/kudos-channel.ts`: `createBoardChannel(supabase, handlers)` → `supabase.channel('kudos-board').on('broadcast', {event:'kudos'}, handler).subscribe()`. Không giữ biến module-level.
3. `use-kudos-stream.ts`:
   ```
   'use client'
   useEffect(() => {
     if (!enabled) return
     const supabase = createClient()
     const channel = createBoardChannel(supabase, handlersRef)
     return () => { supabase.removeChannel(channel) }
   }, [enabled])
   ```
   Handler giữ trong `useRef` để không resubscribe mỗi lần callback đổi identity.
4. `use-my-hearts-stream.ts`: topic `user-hearts:${userId}`; không mở channel khi `userId` rỗng (guest không có trạng thái tim riêng).
5. Thêm `fetchKudoCardById(id)` vào `lib/data/kudos-queries.ts` — select từ `public_kudos_feed`, trả `null` khi không có hàng.
6. Kiểm quyền nghe: `anon` phải nghe được `kudos-board`. Nếu Realtime Authorization đang bật cho Broadcast, thêm policy trên `realtime.messages` cho phép `anon` SELECT topic này.
7. Kiểm tay 2 tab (đã login) + **1 tab ẩn danh** — xem Success Criteria.

## Todo List

- [ ] Xác nhận trigger `0006b` phát tín hiệu (Realtime Inspector)
- [ ] `kudos-channel.ts` không state module-level
- [ ] `use-kudos-stream.ts` + cleanup `removeChannel`
- [ ] `use-my-hearts-stream.ts`, bỏ qua khi guest
- [ ] `fetchKudoCardById` trong `kudos-queries.ts`
- [ ] Policy cho `anon` nghe `kudos-board` (nếu Realtime Authorization bật)
- [ ] Kiểm **guest chưa login** nhận được kudo mới
- [ ] Kiểm StrictMode không rò kênh

## Success Criteria

- **Guest chưa đăng nhập** mở `/kudos` ở cửa sổ ẩn danh → user khác gửi kudo → guest thấy dải "1 kudo mới" trong < 2s.
  *Đây là case bắt buộc, không phải case phụ.* Cách kiểm cũ (2 tab đều đã login) **không phát hiện được** lỗi mất realtime với `anon` — chính vì thế nó lọt qua vòng thiết kế đầu.
- Hai tab **đã login** khác nhau: tab A gửi kudo → tab B nhận < 2s.
- Kudo **ẩn danh** đến qua realtime hiện đúng nhãn cố định, **không** lộ tên người gửi.
- Mở DevTools → WS → đọc frame Broadcast: payload **chỉ** chứa `kudos_id` và loại event. Không `sender_id`, không `body`. Kiểm cả ở phiên anon.
- Thả tim ở tab A → `heart_count` ở tab B đổi đúng con số server, không phải +1 lạc quan.
- Cùng một user mở 2 tab, tim ở tab A → icon tim ở tab B chuyển sang đã-tim (topic `user-hearts:`).
- User X **không** nhận được message trên topic `user-hearts:<id-của-Y>`.
- Dev StrictMode: đúng 1 WebSocket sống; unmount trang → 0.
- Tắt `enabled` → không kết nối realtime nào được mở.
- `grep -rn "postgres_changes" lib/ app/` trả rỗng.

## Risk Assessment

| Rủi ro | K/năng × T/động | Giảm thiểu |
|---|---|---|
| Quay lại Postgres Changes vì "quen tay", rồi gỡ `revoke` cho nó chạy | TB × **Rất cao** | Key Insight #1 ghi rõ hai thứ loại trừ nhau; `grep postgres_changes` trong Success Criteria; pgTAP phase-17 đỏ nếu `revoke` bị gỡ |
| Nhét nội dung vào payload Broadcast cho đỡ phải refetch | **Cao** × **Rất cao** | Payload nghèo là điều kiện để Broadcast an toàn; case đọc frame WS ở phiên anon trong Success Criteria |
| Guest không nghe được `kudos-board` do Realtime Authorization | TB × Cao | Bước 6 + case guest đứng **đầu** Success Criteria |
| Rò channel do cleanup thiếu | TB × TB | `removeChannel` trong cleanup + kiểm DevTools WS |
| Resubscribe liên tục vì callback đổi identity | Cao × TB | Handler trong `useRef`, dependency chỉ `[enabled]` |
| Nghe nhầm topic `user-hearts:` của người khác | Thấp × Cao | Topic mang uuid; có case kiểm chéo trong Success Criteria |
| Feed nhảy vị trí cuộn khi có kudo mới | Cao × Thấp | Hàng đợi + dải "N kudo mới" |
| Mất tín hiệu lúc rớt mạng, không catch-up | TB × TB | **Chấp nhận có ý thức** — đã cân nhắc và loại khỏi MVP (Red Team #11, disposition Reject). Người dùng F5 là xong |

## Security Considerations

- Broadcast **không** đi qua RLS của bảng dữ liệu. Đây không phải khiếm khuyết mà là tính chất — và là lý do payload chỉ được mang id.
- Ranh giới che ẩn danh vẫn nằm ở `public_kudos_feed`, không ở đây. Realtime chỉ nói "có gì đó đổi".
- Topic riêng của user mang uuid trong tên; không dùng topic chung rồi lọc ở client.

## Next Steps

- phase-16 cắm hai hook vào Live board và card ở Profile.
- Notification bell để phase sau khi có spec trigger.

## Rollback

Revert commit. Gỡ realtime không ảnh hưởng luồng đọc/ghi — feed vẫn chạy bằng query thường, chỉ mất cập nhật tức thời. Trigger `0006b` để lại cũng vô hại (phát tín hiệu mà không ai nghe).
