# Phase 16 — Integration (nối hai track)

**Track:** — (phase hợp lưu) · **Priority:** P1 · **Status:** pending · **Effort:** 5h
**Phụ thuộc:** phase-05 (hết Track B) **và** phase-07…15 (hết Track A) · **Mở khoá:** phase-17

## Context Links

- Toàn bộ Integration contract nằm trong phase-06…15
- Tầng dữ liệu: [`phase-04`](./phase-04-data-access-va-business-logic.md) · Realtime: [`phase-05`](./phase-05-realtime.md)
- Quyết định gap #3 (Admin placeholder), #12 (không dịch nội dung user), #13 (word-cloud không realtime): [`clarifications.md`](./clarifications.md)

## Overview

Phase duy nhất được phép sửa file của cả hai track. Việc ở đây là **nối dây**, không phải viết lại: thay mock bằng query thật, truyền callback thật, cắm realtime, hoàn tất i18n, dựng `/admin` placeholder.

## Key Insights

1. **Contract có sẵn nên đây là nối, không phải viết lại.** Nếu thấy mình đang sửa layout hay style của component Track A, tức là contract đã sai — quay lại sửa contract, đừng vá ở đây.
2. **Server Component lấy dữ liệu đầu, Client Component nhận qua prop.** Page là Server Component gọi `lib/data`; component tương tác là Client nhận `initialData` + callback.
3. **`params`/`searchParams` là Promise** ở Next 16 — `/profile?id=` bắt buộc `await searchParams`. Đây là chỗ dễ sai nhất của cả phase.
4. **Đẩy data access xuống page, không lên layout.** Repo không bật `cacheComponents` → layout đọc `cookies()`/fetch chưa cache sẽ chặn cả navigation thay vì stream.
5. **Sanitize rich text tại đúng một chỗ** — trong `kudo-card` khi render `body`. Một hàm `sanitizeKudoBody()`, không rải `dangerouslySetInnerHTML` khắp nơi.
6. **Nội dung do người dùng gõ không dịch** (gap #12) — i18n chỉ chạm UI chrome.
7. `/admin` là placeholder "Coming soon" **có role guard thật** — giữ mục menu để TC ID-5/ID-37 pass mà không hứa hẹn tính năng chưa có.

## Requirements

### Chức năng
- 6 trang (`/`, `/login`, `/kudos`, `/awards`, `/profile`, `/prelaunch`) chạy bằng dữ liệu thật từ Postgres local.
- 3 modal (Viết Kudo, Thể lệ, Open Secret Box) gọi được Server Action thật.
- Live board nhận realtime: kudo mới vào hàng đợi, số tim đổi theo server.
- Đổi ngôn ngữ VN/EN có hiệu lực toàn site và giữ qua reload (cookie `NEXT_LOCALE`).
- `/admin` hiện "Coming soon", chặn user thường.

### Phi chức năng
- Không file nào vượt 200 dòng sau khi nối.
- `npx tsc --noEmit`, `npm run lint`, `npm run build` đều xanh.

## Architecture

### Bảng nối dây

| Callback (Track A) | Nối vào (Track B) |
|---|---|
| `onGoogleLogin` | `lib/auth/sign-in-with-google.ts` |
| `onSignOut` | `signOutAction` |
| `onSubmit` (compose) | `createKudoAction` |
| `searchSunners` | `searchSunners` (`profile-queries`) |
| `onToggleHeart` | `toggleHeartAction` |
| `onOpenBox` | `openSecretBoxAction` |
| `onLoadMore` | `listKudos` / `listReceivedKudos` / `listSentKudos` + `cursor.ts` |
| `onFilterChange` | `listKudos({hashtagId, departmentId})` |
| `newKudosQueue` / `onFlushQueue` | `useKudosStream` (**Broadcast** topic `kudos-board`, không phải `postgres_changes`) |
| `pending` (icon tim) | state cục bộ của `kudo-card` quanh lời gọi `toggleHeartAction` |
| `targetIso` (Homepage) | `process.env.NEXT_PUBLIC_EVENT_START_AT` |
| `targetIso` (Prelaunch) | `process.env.NEXT_PUBLIC_LAUNCH_GATE_AT` |
| `awards` | `lib/content/awards.ts` |
| `isAdmin` | `isCurrentUserAdmin()` |
| `stats` | `getProfileStats(targetId, callerId)` — `null` cho người khác |

### Cấu trúc mỗi trang

```
app/kudos/page.tsx  (Server Component)
  ├─ const user = await verifySession()             // không redirect: board là public
  ├─ const [highlights, first, hashtags, depts] = await Promise.all([...])
  └─ <BoardPage ...initialData onX={serverAction} />   ← Client Component từ phase-09
```

### Một chỗ duy nhất cho mỗi mối quan tâm

| Mối quan tâm | File duy nhất |
|---|---|
| Sanitize rich text | `lib/kudos/sanitize-kudo-body.ts` |
| Map hàng view → card | `lib/kudos/kudo-card-mapper.ts` (phase-04) |
| Nhãn ẩn danh | khoá i18n `kudo.anonymousLabel` |
| Ngưỡng hoa-thị | `lib/kudos/star-count.ts` (phase-04) |

## Related Code Files

**Tạo mới**
- `app/admin/page.tsx` — placeholder + `await requireAdmin()`
- `lib/kudos/sanitize-kudo-body.ts`
- `components/providers/app-providers.tsx` — gom LocaleProvider + toast
- `docs/runbook-su-kien.md` — gom 3 thao tác vận hành đã rải rác thành một chỗ người trực sự kiện đọc được: (1) đổi mốc countdown → **phải `next build` lại** (phase-01); (2) hết Secret Box → `admin_grant_secret_box()` (phase-02); (3) thêm ngày đặc biệt → INSERT `special_days`. Không có file này thì ba thứ đó nằm rải trong ba phase file mà người trực sự kiện sẽ không đọc.

**Sửa** (đây là phase duy nhất được đụng cả hai bên)
- `app/{page,login,kudos,awards,profile,prelaunch}/page.tsx` — thay mock bằng query, truyền callback
- `components/board/**`, `components/profile/**`, `components/kudo-compose/**`, `components/secret-box/**` — chỉ đổi chỗ nhận prop, **không** đổi layout/style
- `locales/{vi,en}/*.json` — rà đủ khoá, khoá thiếu ở bên nào bổ sung bên đó
- `app/layout.tsx` — bọc `AppProviders`
- `lib/data/*` — chỉ khi phát hiện thiếu trường lúc nối

**Xoá:** mọi file/hằng số mock của Track A (`components/**/mock-*.ts`)

**File ownership:** toàn bộ repo — phase này **chạy một mình**, không song song với phase nào khác.

## Implementation Steps

1. Đọc lại mục "Integration contract" của phase-06…15, lập bảng đối chiếu prop ↔ hàm. Chỗ nào lệch → sửa **contract**, ghi lại lý do.
2. `/prelaunch` trước (đơn giản nhất, xác nhận env + gate hoạt động end-to-end).
3. `/login` → nối `signInWithGoogle` + đọc `await searchParams` cho `error`.
4. `/` → env countdown + `lib/content/awards.ts` + `AccountMenu` với `isAdmin` thật.
5. `/awards` → hằng số tĩnh + anchor slug.
6. `/kudos` → nặng nhất: Server Component prefetch (highlights, trang 1, hashtags **kèm mục "Chưa phân loại"**, departments, sidebar stats) → `BoardPage`; nối heart/copy/filter/infinite scroll; cắm `useKudosStream` + `useMyHeartsStream` (**Broadcast**). `useKudosStream` bật cho **cả guest** — board là public, đừng gắn nó sau điều kiện `if (user)`.
7. Modal Viết Kudo → `createKudoAction` + upload ảnh; sau khi gửi thành công `revalidatePath('/kudos')` và đóng modal.
8. Modal Secret Box → `openSecretBoxAction`; đồng bộ `remaining` về sidebar.
9. `/profile` → `await searchParams` lấy `id`; kiểm định dạng UUID **trước** khi query; `stats` `null` cho người khác; dùng lại `kudo-card`.
10. `app/admin/page.tsx` → `await requireAdmin()` + nội dung "Coming soon".
11. `sanitize-kudo-body.ts` + áp vào đúng chỗ render `body`.
12. Rà i18n: script nhỏ so khoá giữa `locales/vi/*.json` và `locales/en/*.json`, báo khoá lệch.
13. Xoá sạch mock; `grep -rn "mock" components/` phải rỗng.
14. `npx tsc --noEmit` + `npm run lint` (**`eslint` trực tiếp — `next lint` đã bị xoá khỏi Next 16**) + `npm run build`. Lưu ý thêm: `next build` ở v16 **không còn tự chạy lint**, nên bước lint phải gọi tường minh.

## Todo List

- [ ] Bảng đối chiếu prop ↔ hàm, ghi lệch contract
- [ ] Nối `/prelaunch`, `/login`, `/`, `/awards`
- [ ] Nối `/kudos` + 2 hook realtime
- [ ] Nối 3 modal với 3 Server Action
- [ ] Nối `/profile` (`await searchParams`, kiểm UUID, `stats=null`)
- [ ] `/admin` placeholder + `requireAdmin()`
- [ ] `sanitize-kudo-body.ts` áp đúng một chỗ
- [ ] Rà khoá i18n hai chiều vi ↔ en
- [ ] Xoá toàn bộ mock
- [ ] Runbook vận hành sự kiện (`docs/runbook-su-kien.md`)
- [ ] `tsc --noEmit` + `npm run lint` + `build` xanh

## Success Criteria

- Từ `/kudos` gửi một kudo thật → xuất hiện trong All Kudos, `select count(*) from kudos` tăng 1, ảnh nằm trong Storage.
- Kudo gửi ẩn danh hiện **nhãn cố định** trên board và trên profile người nhận; mở DevTools → Network, payload **không** chứa `sender_id` của kudo đó.
- Chính người gửi mở `/profile` → tab "Đã gửi" thấy kudo ẩn danh đó kèm tên mình; user khác mở profile người đó → **không có** tab "Đã gửi".
- Thả tim → số hiển thị đúng bằng số server trả; F5 giữ nguyên; tab thứ hai đổi theo trong ~1s.
- **Cửa sổ ẩn danh (chưa login)** mở `/kudos` → user khác gửi kudo → guest thấy dải "1 kudo mới". Nếu chỉ tab đã-login nhận được thì `useKudosStream` đang bị gắn sau điều kiện auth — sửa.
- Filter Phòng ban → chọn "Chưa phân loại" → thấy kudos của user đăng nhập thật (những người chưa có phòng ban).
- Mở Secret Box khi còn hộp → nhận 1 huy hiệu, `remaining` giảm 1 ở cả modal lẫn sidebar; hết hộp → thông báo, nút disabled.
- Đổi VN → EN → reload: giao diện vẫn EN; **nội dung kudo giữ nguyên tiếng người dùng gõ**.
- User thường mở `/admin` → 302 `/`; admin mở → "Coming soon"; mục menu chỉ hiện với admin.
- `NEXT_PUBLIC_LAUNCH_GATE_AT` ở tương lai → mọi URL về `/prelaunch`; đổi sang quá khứ + restart → site mở bình thường.
- Không file nào trong `app/`, `components/`, `lib/` vượt 200 dòng: `find app components lib -name "*.ts*" -exec wc -l {} + | awk '$1>200'` trả rỗng.
- `npm run build` exit 0.

## Risk Assessment

| Rủi ro | K/năng × T/động | Giảm thiểu |
|---|---|---|
| Contract lệch → phải sửa lại UI ở phase này | Cao × Cao | Bước 1 lập bảng đối chiếu **trước khi** gõ code; lệch thì sửa contract chứ không vá tại chỗ |
| Quên `await searchParams` ở `/profile` | Cao × TB | `tsc --noEmit` bắt được; có case riêng trong Success Criteria |
| File phình quá 200 dòng khi nối | Cao × TB | Lệnh `wc -l` nằm trong Success Criteria; tách container/presentational khi vượt |
| Render `body` chưa sanitize | TB × **Rất cao** | Một hàm duy nhất; phase-17 có test XSS |
| Đặt data access lên layout → chặn navigation | TB × TB | Quy ước: layout không gọi `lib/data`; review kiểm |
| Xoá mock làm vỡ component còn tham chiếu | TB × Thấp | Xoá sau cùng, `build` bắt ngay |
| i18n thiếu khoá ở một bên → hiện khoá thô | Cao × Thấp | Script so khoá ở bước 12, phase-17 biến thành test |
| Modal đóng trước khi action xong → mất phản hồi lỗi | TB × TB | Chỉ đóng khi `{ok:true}`; `submitting` disable nút |

## Security Considerations

- **Kiểm tra lại một lượt**: mọi Server Action đều mở đầu bằng `requireUser()`; không action nào dựa vào việc UI đã ẩn nút.
- Xác nhận bằng quan sát mạng: payload feed công khai không mang `sender_id` của kudo ẩn danh.
- `sanitizeKudoBody` chỉ cho whitelist thẻ (b/i/u/s/a/ul/ol/li/blockquote/p/br); `<a>` bắt buộc `rel="noopener noreferrer"` và chỉ `http`/`https`.
- `/admin` guard bằng `requireAdmin()` ở page, không chỉ bằng `proxy.ts`.
- Không log nội dung kudo hay email ra console.

## Next Steps

- phase-17 dựng bộ test và khoá lại các bất biến vừa nối.
- Sau MVP: Hero tier, rule cấp Secret Box, notification bell, màn Admin thật (xem `clarifications.md` mục "Còn treo").

## Rollback

Phase này gồm nhiều commit nhỏ theo từng trang (bước 2→10). Hỏng ở trang nào thì `git revert` đúng commit trang đó — các trang khác không phụ thuộc nhau. Không có migration mới nên DB không cần đụng tới.
