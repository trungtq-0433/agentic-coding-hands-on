# MoMorph screen inventory — Sun* Kudos

- **fileKey:** `9ypp4enmFmdK3YAFJLIu6C`
- **Source URL:** https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens?spec=done&pages=2324
- **Fetched:** 2026-08-05 10:11 (+07) via MCP `momorph` → `list_frames(fileKey)`
- **Totals:** 174 frames · spec_status done = 50 · in_progress = 23 · none = 101

## Filter caveat (đọc trước khi dùng)

MCP `list_frames` chỉ nhận `designStatus / specStatus / devStatus / reviewStatus`.
**Không** có filter `platform` hay `page` — hai cái đó chỉ tồn tại ở UI web MoMorph
(`?pages=2324`). `list_frame_sets` trả rỗng, `get_project_overview` không có data,
`get_frame` cũng không trả page/platform.

→ Web/mobile ở đây tách bằng **tiền tố tên**: `[iOS]` = mobile, còn lại = website.
Đây là **suy luận từ naming, không phải metadata**. Verify lại trên UI trước khi khoá scope.

## Website + spec done — 18 screens (scope chính)

URL pattern: `https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/{screenId}`

| # | screenId | Tên màn | design_status |
|---|----------|---------|---------------|
| 1 | `OyDLDuSGEa` | Addlink Box | done |
| 2 | `8PJQswPZmU` | Countdown - Prelaunch page | done |
| 3 | `JWpsISMAaM` | Dropdown Hashtag filter | done |
| 4 | `WXK5AYB_rG` | Dropdown Phòng ban | done |
| 5 | `p9zO-c4a4x` | Dropdown list hashtag | done |
| 6 | `hUyaaugye2` | Dropdown-ngôn ngữ | done |
| 7 | `z4sCl3_Qtk` | Dropdown-profile | done |
| 8 | `54rekaCHG1` | Dropdown-profile Admin | done |
| 9 | `_hphd32jN2` | Floating Action Button - phím nổi chức năng | **in_progress** |
| 10 | `Sv7DFwBw1h` | Floating Action Button - phím nổi chức năng 2 | done |
| 11 | `i87tDx10uM` | Homepage SAA | **in_progress** |
| 12 | `zFYDgyj_pD` | Hệ thống giải | done |
| 13 | `GzbNeVGJHz` | Login | done |
| 14 | `J3-4YFIpMM` | Open secret box - chưa mở | done |
| 15 | `3FoIx6ALVb` | Profile bản thân | done |
| 16 | `MaZUn5xHXZ` | Sun* Kudos - Live board | done |
| 17 | `b1Filzi9i6` | Thể lệ UPDATE | done |
| 18 | `ihQ26W78P2` | Viết Kudo | done |

## Phân nhóm cho Track A (khuyến nghị)

**Không spawn 18 subagent.** 8/18 là component dùng chung — spawn song song sẽ đẻ ra
nhiều phiên bản dropdown khác nhau cho cùng một thứ.

**Nhóm 1 — shared components (chạy TRƯỚC, 1 phase):**
`JWpsISMAaM`, `WXK5AYB_rG`, `p9zO-c4a4x`, `hUyaaugye2`, `z4sCl3_Qtk`, `54rekaCHG1`,
`OyDLDuSGEa`, `_hphd32jN2` + `Sv7DFwBw1h`
→ dropdown / overlay / FAB. `Dropdown-profile` và `Dropdown-profile Admin` là 2 biến thể
của cùng 1 component (khác quyền), không phải 2 component.

**Nhóm 2 — màn thật (Track A song song, 1 subagent/màn):**
`GzbNeVGJHz` Login · `i87tDx10uM` Homepage SAA · `3FoIx6ALVb` Profile bản thân ·
`MaZUn5xHXZ` Live board · `ihQ26W78P2` Viết Kudo · `zFYDgyj_pD` Hệ thống giải ·
`b1Filzi9i6` Thể lệ · `8PJQswPZmU` Countdown Prelaunch · `J3-4YFIpMM` Open secret box

## Rủi ro đã phát hiện

1. **`i87tDx10uM` Homepage SAA — design_status `in_progress`.** Spec done nhưng design
   chưa chốt. Đây là màn trung tâm; design đổi = code lại. Chốt với designer trước, hoặc
   xếp cuối Track A.
2. **`_hphd32jN2` FAB — design_status `in_progress`**, và có `Sv7DFwBw1h` "FAB 2" bản done.
   Nhiều khả năng #2 thay thế #1. Xác nhận trước khi code cả hai.
3. **8 màn `[iOS] Open secret box - trạng thái Standby`** trùng tên hoàn toàn (mobile) —
   dấu hiệu naming trong file chưa sạch. Áp cho website nghĩa là: đừng tin tên màn là
   duy nhất, luôn khoá bằng screenId.

## Mobile + spec done — 32 screens (ngoài scope website)

| screenId | Tên màn | design_status |
|----------|---------|---------------|
| `k-7zJk2B7s` | Access denied | in_progress |
| `7y195PPTxQ` | Award_Best Manager | in_progress |
| `b2BuS8HYIt` | Award_MVP | in_progress |
| `O98TwiHaJe` | Award_Signature 2025 - Creator | in_progress |
| `QQvsfK3yaK` | Award_Top project leader | in_progress |
| `c-QM3_zjkG` | Award_Top talent | in_progress |
| `OuH1BUTYT0` | Home | done |
| `uUvW6Qm1ve` | Language dropdown | done |
| `8HGlvYGJWq` | Login | done |
| `sn2mdavs1a` | Not Found | in_progress |
| `_b68CBWKl5` | Notifications | in_progress |
| `kQk65hSYF2` | Open secret box | done |
| `KUmv414uC9` | Open secret box - action bấm mở | done |
| `wsI6gaO_yc` | Open secret box - Standby | done |
| `xptNUunBS_` | Open secret box - Standby | done |
| `FvTOS7oCPU` | Open secret box - Standby | done |
| `scvV-OQCAJ` | Open secret box - Standby | done |
| `IXpGakYRm5` | Open secret box - Standby | done |
| `-LIblaeusT` | Open secret box - Standby | done |
| `_cWAEarZPi` | Open secret box - Standby | done |
| `fO0Kt19sZZ` | Sun*Kudos | in_progress |
| `j_a2GQWKDJ` | Sun*Kudos_All Kudos | done |
| `PV7jBVZU1N` | Sun*Kudos_Gửi lời chúc Kudos | done |
| `aKWA2klsnt` | Sun*Kudos_Gửi lời chúc_dropdown hashtag | done |
| `5MU728Tjck` | Sun*Kudos_Gửi lời chúc_dropdown tên người nhận | done |
| `3jgwke3E8O` | Sun*Kudos_Search Sunner | in_progress |
| `hldqjHoSRH` | Sun*Kudos_Searching | in_progress |
| `xms7csmDhD` | Sun*Kudos_Tiêu chuẩn cộng đồng | done |
| `7fFAb-K35a` | Sun*Kudos_Viết Kudo_default | in_progress |
| `V5GRjAdJyb` | Sun*Kudos_dropdown hashtag | done |
| `76k69LQPfj` | Sun*Kudos_dropdown phòng ban | done |
| `zIuFaHAid4` | Thể lệ | in_progress |

## Domain lộ ra từ tên màn (input cho Supabase schema)

kudos/lời chúc · hashtag · phòng ban · award (MVP, Best Manager, Top talent, Top project
leader, Signature Creator) · secret box · live board · admin review content · đa ngôn ngữ ·
notifications · search sunner.

→ Schema xoay quanh `users / departments / kudos / hashtags / awards / secret_boxes`,
realtime cho Live board, RLS phân tách user vs admin.

## Bối cảnh môi trường

- Repo: Next.js 16.3.0 + React 19.2.8 + Tailwind v4 + TS. Mới chỉ có `app/` (create-next-app).
- Supabase: **chưa có gì**. CLI chưa cài global; Docker 29.7.1 đã có → dùng `npx supabase init/start`.
- MCP `momorph`: header `x-github-token` từng chứa error text của `gh auth token` (gh bản cũ)
  → server không auth được. Đã vá 2026-08-05 bằng `claude mcp remove/add`.
  Backup config: `~/.claude.json.bak-260805-0948`.

## Câu chưa trả lời

1. Filter `pages=2324` trên UI có khớp đúng 18 màn non-`[iOS]` này không? MCP không verify được.
=> Answer: Khớp
2. `_hphd32jN2` (FAB) có bị `Sv7DFwBw1h` (FAB 2) thay thế không?
=> Answer: Dùng cả 2
3. Homepage SAA design chưa done — chờ chốt hay code theo bản hiện tại?
=> Answer: Dùng theo bản hiện tại
4. Supabase dừng ở local dev, hay cần tính luôn đường lên hosted (migration + CI)?
=> Answer: Dùng ở local dev thôi.