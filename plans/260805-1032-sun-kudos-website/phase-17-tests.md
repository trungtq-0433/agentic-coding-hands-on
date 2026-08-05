# Phase 17 — Test suite

**Track:** — (phase kết) · **Priority:** P1 · **Status:** pending · **Effort:** 14h
**Phụ thuộc:** phase-16 · **Mở khoá:** không (phase cuối)

> **Effort đã sửa 5h → 14h.** Con số 5h ban đầu là ước lượng sai: nó bỏ qua việc phase này phải **dựng hạ tầng test từ số không** (repo chưa có gì) rồi mới viết ~25 file test trải bốn tầng công cụ, trong đó có 8 kịch bản Playwright đa-context và 4 file pgTAP. Giữ **một** phase (không chẻ nhỏ) nhưng ghi effort thật.
> Phân bổ: hạ tầng 2h · unit 2h · component 2h · pgTAP 3h · E2E 4h · ổn định hoá chống flaky 1h.

## Context Links

- Bất biến cần khoá: [`phase-02`](./phase-02-schema-migrations-rls.md) (RLS/view), [`phase-04`](./phase-04-data-access-va-business-logic.md) (RPC), [`phase-16`](./phase-16-integration.md) (luồng end-to-end)
- Cách test RLS ở local (pgTAP / giả lập JWT trong Studio): [`reports/researcher-260805-1032-nextjs16-supabase-local.md`](./reports/researcher-260805-1032-nextjs16-supabase-local.md) §5
- Nguồn kịch bản: **292 test case** trong `research/momorph/csv/tc-*.csv` — đếm bằng `csv.DictReader`, 0 dòng thiếu `TC_ID` (đếm dòng thô cũng ra 292; con số 284 từng được nêu là sai)
- ⚠ **Phân bố TC rất lệch — đọc kỹ trước khi tin vào con số 292**

## Overview

Repo **chưa có bất kỳ hạ tầng test nào**. Phase này chọn framework, dựng hạ tầng, rồi viết test cho các bất biến mà nếu vỡ thì hỏng nghiệp vụ hoặc rò dữ liệu. Không đuổi theo con số coverage — đuổi theo đúng những mệnh đề đã viết trong Success Criteria của các phase trước.

### 292 TC nhưng 8/18 file rỗng hoàn toàn

Đếm thật bằng CSV parser (`csv.DictReader`, không đếm dòng thô):

| Nhóm | File | TC |
|---|---|---|
| Có TC | live-board 41 · homepage 62 · viết-kudo 57 · profile 30 · addlink 25 · open-secret-box 19 · login 17 · countdown 17 · hệ-thống-giải 15 · thể-lệ 9 | **292** |
| **Rỗng 0 byte** | dropdown-hashtag-filter · dropdown-list-hashtag · dropdown-ngôn-ngữ · dropdown-phòng-ban · dropdown-profile · dropdown-profile-admin · FAB 1 · FAB 2 | **0** |

**Hệ quả cho phase này:** toàn bộ **phase-06 (shared components) không có một TC gốc nào để bám**. Con số "292" dễ tạo ảo giác coverage trải đều, trong khi thực tế mọi dropdown và cả hai FAB đều trắng. Test cho nhóm đó phải **tự suy từ spec item** (`spec-dropdown-*.csv`, `spec-fab-*.csv`) chứ không copy từ TC — và phải nói rõ trong test là nguồn suy ra, không phải nguồn trích. Đây cũng là nhóm dễ bị bỏ quên nhất vì "không có TC thì chắc không cần test".

## Key Insights

1. **Chọn Vitest + React Testing Library + Playwright + pgTAP.** Lý do từng lựa chọn:
   - **Vitest** thay Jest: ESM-native, không cần babel/transform cho React 19 + TS, khởi động nhanh, API tương thích Jest nên không tốn chi phí học. Jest với ESM + Next 16 cần cấu hình đáng kể mà không đổi lại lợi ích nào.
   - **Node test runner có sẵn** bị loại: không có DOM, không parse JSX — component test sẽ phải tự dựng hạ tầng.
   - **Playwright** cho E2E: cần chạy thật OAuth callback, cookie, realtime hai tab — jsdom không mô phỏng được. Đa-context (2 tab, 2 user) là yêu cầu bắt buộc của TC_WEB_PROFILE_SEC_003 ("một phiên không chứng minh được").
   - **pgTAP** qua `npx supabase test db`: RLS và RPC là SQL, phải test bằng SQL. Test qua JS client sẽ không phân biệt được "policy chặn" với "query sai".
2. **Ba bất biến bảo mật là ưu tiên số một**, xếp trên mọi test khác: (a) không rò `sender_id` của kudo ẩn danh; (b) Sent-list chỉ chính chủ thấy; (c) `secret_box_grants` không thao túng được từ client.
3. **Test hồi quy cho Next 16** rẻ và đáng: một test khẳng định `middleware.ts` không tồn tại; `tsc --noEmit` bắt hết chỗ quên `await`.
3b. **`next lint` đã bị XOÁ khỏi Next 16** — `node_modules/next/dist/docs/01-app/02-guides/upgrading/version-16.md:1084`: *"The `next lint` command has been removed. Use Biome or ESLint directly. `next build` no longer runs linting."* `package.json` gốc đã có sẵn `"lint": "eslint"`. → script `validate` gọi `npm run lint`, **không** `next lint` (lệnh đó sẽ fail). Và vì `next build` không còn tự lint, bỏ bước lint = không lint gì cả.
4. **Test dùng DB thật (Supabase local), không mock.** Mock DB sẽ để lọt đúng loại lỗi mà RLS sinh ra.

## Requirements

### Chức năng
| Tầng | Công cụ | Phạm vi |
|---|---|---|
| Unit | Vitest | `star-count`, `cursor` (encode/decode/rác), `launch-gate`, `route-guard`, 3 Zod schema, `sanitize-kudo-body`, `kudo-card-mapper` |
| Component | Vitest + RTL | `MultiHashtagPicker` (chặn thứ 6), `AddLinkDialog` (validate), `CountdownTimer` (tick + về 0), `SecretBoxModal` (không state đếm nội bộ), `ProfilePage` (`stats=null` → thanh viết Kudo) |
| DB | pgTAP | RLS mọi bảng, 2 view, 4 RPC (3 nghiệp vụ + `admin_grant_secret_box`), 5 trigger (3 counter + 2 broadcast), CHECK `kudos_no_self`, UNIQUE `hearts`, **khối `revoke` ghi trực tiếp**, `search_path` của mọi hàm definer |
| E2E | Playwright | login → gửi kudo → thả tim → mở box → đổi ngôn ngữ → xem profile; gate prelaunch; guard `/admin`; **realtime với phiên anon**; rò rỉ ẩn danh 2 phiên |
| i18n | Vitest | parity khoá giữa `locales/vi/*.json` và `locales/en/*.json` |
| Hồi quy Next 16 | Vitest | `middleware.ts` không tồn tại ở root |

### Phi chức năng
- `npm test` chạy được không cần Playwright; `npm run test:e2e` tách riêng (cần Supabase local đang chạy).
- Test DB tự `db reset` trước khi chạy để có trạng thái xác định.

## Architecture

```
tests/
  unit/            *.test.ts        (Vitest, node env)
  components/      *.test.tsx       (Vitest, jsdom env)
  e2e/             *.spec.ts        (Playwright, cần supabase start + next dev)
supabase/tests/    *.test.sql       (pgTAP, chạy bằng npx supabase test db)
vitest.config.ts   projects: [unit(node), components(jsdom)]
playwright.config.ts
```

E2E dùng tài khoản seed sẵn (`seed.sql` phase-02) + `storageState` đã đăng nhập, **không** đi qua Google thật trong CI — luồng OAuth thật kiểm bằng một test chạy tay có đánh dấu `@manual`.

## Related Code Files

**Tạo mới**
- `vitest.config.ts`, `playwright.config.ts`, `tests/setup.ts`
- `tests/unit/*.test.ts` (7 file theo bảng trên)
- `tests/components/*.test.tsx` (5 file)
- `tests/e2e/{auth,compose-kudo,heart,secret-box,i18n,profile-privacy,prelaunch-gate,realtime}.spec.ts`
- `supabase/tests/{rls,views,rpc,triggers}.test.sql`
- `tests/unit/i18n-key-parity.test.ts`, `tests/unit/no-middleware-file.test.ts`

**Sửa:** `package.json` (devDeps + script `test`, `test:components`, `test:db`, `test:e2e`, `validate`)

**Xoá:** không

**File ownership (glob):** `tests/**`, `supabase/tests/**`, `vitest.config.ts`, `playwright.config.ts`, `package.json` (chỉ khối devDependencies + scripts)

## Implementation Steps

1. `npm i -D vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/user-event @playwright/test`; `npx playwright install chromium`.
2. `vitest.config.ts` với 2 project (node / jsdom), alias `@/` trỏ root.
3. Unit test theo bảng — bắt đầu bằng `cursor.ts` (cursor rác phải trả `null`, không throw) và `star-count` (biên 9/10/19/20/49/50).
4. Component test — `SecretBoxModal` kiểm bằng cách truyền `remaining` nghịch lý và khẳng định UI theo prop, chứng minh không có bộ đếm cục bộ.
5. pgTAP: `supabase/tests/rls.test.sql` dùng `set local role authenticated; set local request.jwt.claims = ...` cho 2 user giả, khẳng định `my_sent_kudos` cách ly, và khẳng định **4 lệnh ghi trực tiếp đều bị từ chối** (`insert into kudos`, `insert into kudos_hashtags`, `insert into hearts`, `delete from hearts`); `views.test.sql` khẳng định `sender_id is null` với mọi hàng `is_anonymous`; `rpc.test.sql` khẳng định tự-tim bị chặn, bonus +2 do hàm tự tra, thu hồi đúng số, `open_secret_box` không double-open, `toggle_heart` gọi trùng là no-op, `admin_grant_secret_box` chặn non-admin; `triggers.test.sql` khẳng định counter khớp `count(*)` và **mọi hàm `security definer` đều có `search_path`** (`select … from pg_proc where prosecdef and proconfig is null` phải trả 0 hàng).
6. Test phân phối badge: gọi `open_secret_box` 10.000 lần trên dữ liệu giả, khẳng định lệch < 2% mỗi loại. Chạy tách (`@slow`), không nằm trong `npm test` mặc định.
7. Playwright: fixture đăng nhập bằng `storageState`; test `profile-privacy.spec.ts` dùng **hai** browser context để chứng minh cách ly Sent-list.
8. `realtime.spec.ts`: **context B là phiên `anon` chưa đăng nhập** (không dùng `storageState`), context A đã login gửi kudo → chờ dải "1 kudo mới" ở B trong 5s. Dùng anon là điểm mấu chốt: bản thiết kế đầu chọn Postgres Changes và test bằng 2 tab đã-login, nên không ai phát hiện `revoke select on kudos` đã giết realtime cho toàn bộ khách. Thêm assert đọc frame WS: payload không chứa `sender_id`/`body`.
9. `i18n-key-parity.test.ts`: đệ quy so khoá hai chiều, báo tên khoá thiếu.
10. `no-middleware-file.test.ts`: `existsSync('middleware.ts')` phải `false`.
11. Script `validate` = `tsc --noEmit && npm run lint && vitest run && next build`.
    **KHÔNG dùng `next lint`** — lệnh đã bị xoá khỏi Next 16 (xem Key Insight #3b), chạy sẽ fail ngay. `package.json` gốc đã có `"lint": "eslint"`, dùng lại nó.
12. Chạy toàn bộ, sửa cho xanh. **Không** bỏ qua test đỏ để build xanh.
13. Test cho phase-06 (dropdown + FAB): suy từ `spec-dropdown-*.csv` / `spec-fab-*.csv` vì **không có TC gốc**. Ghi comment đầu file nêu rõ nguồn là spec suy ra.

## Todo List

- [ ] Cài Vitest + RTL + Playwright, `vitest.config.ts`, `playwright.config.ts`
- [ ] 7 file unit test
- [ ] 5 file component test
- [ ] 4 file pgTAP (rls, views, rpc, triggers) — gồm 4 case "ghi trực tiếp bị chặn" + case `search_path`
- [ ] 8 file E2E, có fixture `storageState`; `realtime.spec.ts` dùng **context anon**
- [ ] Test cho phase-06 suy từ spec (8 màn không có TC gốc), ghi rõ nguồn trong comment
- [ ] `validate` dùng `npm run lint`, **không** `next lint`
- [ ] Test phân phối badge (đánh dấu `@slow`)
- [ ] Test parity khoá i18n
- [ ] Test hồi quy `middleware.ts` không tồn tại
- [ ] Script `test`, `test:components`, `test:db`, `test:e2e`, `validate`
- [ ] Toàn bộ xanh, không skip test nào

## Success Criteria

- `npm run validate` exit 0 và **không** có test nào ở trạng thái `skipped`/`todo`.
- `npx supabase test db` xanh, phủ đủ: 12 bảng có RLS, 2 view, 4 RPC, 5 trigger, 2 ràng buộc, khối `revoke`, `search_path`.
- Test cách ly Sent-list chạy với **hai** phiên thật và đỏ nếu ai đó đổi `my_sent_kudos` thành `security_invoker = true`.
- Test rò ẩn danh đỏ nếu ai đó bỏ `revoke select on kudos`.
- **Test ghi trực tiếp đỏ nếu ai đó `grant insert on kudos/hearts to authenticated`** — đây là hàng rào giữ mọi luật nghiệp vụ nằm trong RPC.
- Test `search_path` đỏ nếu ai đó thêm hàm `security definer` mới mà quên cố định schema.
- Test double-open đỏ nếu ai đó bỏ `for update` trong `open_secret_box`; test race tim đỏ nếu bỏ `on conflict` trong `toggle_heart`.
- **Test realtime chạy bằng phiên anon** và đỏ nếu ai đó quay lại `postgres_changes`.
- `npm run validate` không chứa `next lint` ở bất kỳ đâu: `grep -rn "next lint" package.json` trả rỗng.
- Test parity i18n đỏ khi thêm một khoá vào `locales/vi` mà quên `locales/en`.
- Tạo thử `middleware.ts` ở root → test đỏ; xoá đi → xanh.
- E2E realtime xanh khi chạy hai lần liên tiếp (không flaky).

## Risk Assessment

| Rủi ro | K/năng × T/động | Giảm thiểu |
|---|---|---|
| E2E flaky do chờ realtime bằng `sleep` cố định | Cao × TB | Dùng `expect.poll`/`waitFor` của Playwright, không `waitForTimeout` |
| Test phụ thuộc dữ liệu seed đổi theo thời gian | TB × TB | E2E tự tạo dữ liệu của chính nó; seed chỉ dùng cho tài khoản đăng nhập |
| Test 10.000 lần mở hộp làm chậm vòng lặp dev | Cao × Thấp | Đánh dấu `@slow`, ngoài `npm test` mặc định |
| Playwright cần Supabase + `next dev` đang chạy | Cao × TB | `webServer` trong `playwright.config.ts` + kiểm `supabase status` ở global setup, fail sớm với thông báo rõ |
| Sa đà chạy theo coverage % | TB × TB | Danh sách test bám sát Success Criteria các phase trước, không đặt ngưỡng coverage |
| Con số "292 TC" tạo ảo giác phủ đều, bỏ quên 8 màn trắng TC | **Cao** × TB | Bảng phân bố ở Overview + todo riêng cho test phase-06 suy từ spec |
| Dùng `next lint` theo trí nhớ Next 14/15 → `validate` fail ngay | **Cao** × Thấp | Key Insight #3b + case `grep "next lint"` trong Success Criteria |
| Ước lượng effort lại trượt như lần đầu (5h → thực tế 14h) | TB × TB | Phân bổ theo tầng ghi ở đầu file; đo lại sau tầng pgTAP để hiệu chỉnh sớm |
| Test đỏ bị bỏ qua để build xanh | TB × Cao | Quy tắc dự án cấm; `validate` không có cờ `--passWithNoTests` hay `--bail=0` |

## Security Considerations

- Ba test bảo mật (rò ẩn danh, cách ly Sent-list, chống thao túng Secret Box) là **cổng chặn**, không phải test tuỳ chọn — đỏ thì không merge.
- Test XSS: gửi kudo có `<img src=x onerror=alert(1)>` trong `body`, khẳng định render ra text vô hại.
- Không đưa key/secret thật vào file test; dùng key local từ `.env.local`.
- Test không được ghi log nội dung kudo hay email.

## Next Steps

- Sau khi xanh: cập nhật `docs/development-roadmap.md` + `docs/project-changelog.md` theo `documentation-management.md`.
- Các mục còn treo (Hero tier, rule cấp Secret Box, notification bell, Admin thật) cần plan riêng, kèm test riêng.

## Rollback

Test là phụ trợ — revert phase này không ảnh hưởng sản phẩm chạy. Ngược lại, nếu một test khoá bất biến mà lại đỏ vì lỗi thật, **fix code chứ không xoá test**.
