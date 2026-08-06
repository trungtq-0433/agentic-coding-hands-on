# Debug — Header trang chủ mâu thuẫn trạng thái đăng nhập

**Ngày:** 2026-08-06 · **Phạm vi:** `app/page.tsx`, `components/home/home-page-client.tsx`

## Tóm tắt

Ba triệu chứng được báo, **một nguyên nhân gốc**: trang chủ có HAI nguồn sự thật khác nhau
cho câu hỏi "đã đăng nhập chưa".

| Tầng | Đọc từ đâu | Kết luận |
|---|---|---|
| `proxy.ts` → `route-guard.ts` | cookie phiên THẬT | đã đăng nhập |
| `app/page.tsx` → header | `profile={null}` **ghi cứng** | chưa đăng nhập |

Hệ quả: người đã đăng nhập bị `/login` đá về `/`, mà `/` vẫn vẽ nút "Đăng nhập" — bấm vào
thì quay lại đúng chỗ cũ. Không có đường nào thoát khỏi vòng đó, và cũng không có đường
đăng xuất vì menu tài khoản không bao giờ render.

## Bằng chứng

**1. Phiên có thật.** Truy vấn thẳng GoTrue:

```
$ docker exec supabase_db_… psql -Atc "select u.email, s.updated_at from auth.sessions s join auth.users u on u.id=s.user_id"
tran.quang.trung@sun-asterisk.com | 2026-08-06 06:42:55+00
```

Đúng 1 phiên đang hoạt động, cập nhật vài phút trước lúc báo lỗi.

**2. Luật điều hướng.** `lib/auth/route-guard.ts:37`

```ts
if (matchesPrefix(pathname, GUEST_ONLY_PREFIXES) && hasSession) {
  return { redirectTo: "/" };
}
```

`GUEST_ONLY_PREFIXES = ["/login"]`. → giải thích triệu chứng #1 và #2. **Đây là hành vi
đúng của phase-03, không phải lỗi.**

**3. Nguồn sự thật thứ hai.** `home-page-client.tsx` (bản cũ) truyền cứng `profile={null}`,
`isAdmin={false}` bất kể cookie. → giải thích triệu chứng #3.

**4. Tái hiện có kiểm soát.** Tạo user test riêng (`debug-probe@example.com`) để **không
đụng phiên thật**, dựng cookie phiên, gọi bằng curl:

```
/login  + cookie → status=307  location=http://localhost:3000/     ← khớp triệu chứng #2
/       + cookie → HTML vẫn chứa nút "Đăng nhập", không có tên user ← khớp triệu chứng #3
```

## Nguyên nhân gốc

Không phải lỗi logic mà là **ranh giới kiến trúc chưa được nối**. Plan tách Track A (UI) và
Track B (backend), cấm import chéo trước phase-16; `HomePage` khai sẵn prop `profile`/`isAdmin`
đúng contract, nhưng `app/page.tsx` chưa có ai nối vào. Khi phase-08 chỉ dựng UI thì trạng
thái "khách cứng" là vô hại — nhưng `proxy.ts` của Track B đã hoạt động từ phase-03, nên
ngay khi có người đăng nhập thật, hai tầng bắt đầu nói ngược nhau.

## Bản vá

Kéo sớm phần auth của phase-16 cho trang chủ. **Không viết hàm mới** — dùng đúng ba API
Track B đã có và đã kiểm:

- `getCurrentProfile()` — `lib/auth/dal.ts`
- `isCurrentUserAdmin()` — `lib/auth/dal.ts`
- `signOutAction()` — `lib/actions/auth-actions.ts` (Server Action)

`app/page.tsx` thành async Server Component, đọc phiên thật rồi truyền xuống. `verifySession()`
bọc `cache()` nên hai lệnh gọi song song chỉ hỏi Supabase Auth một lần.

`signOutAction` truyền xuống Client Component được **vì nó là Server Action** — function
thường thì Next chặn.

`profile` được thu hẹp còn 2 trường `AccountMenu` cần, không đẩy nguyên DTO xuống client.

## Kiểm chứng sau vá

Vòng đầy đủ, chạy trên trình duyệt thật với phiên user test:

| Bước | Kỳ vọng | Kết quả |
|---|---|---|
| `/` có phiên | header hiện menu tài khoản, KHÔNG có nút Đăng nhập | ✅ `coNutDangNhap:false`, `coAvatarMenu:true`, tên "Debug Probe" |
| `/login` có phiên | 307 về `/` | ✅ (hành vi phase-03 giữ nguyên) |
| Bấm Logout | phiên bị huỷ trong DB | ✅ `auth.sessions` mất hàng của user test, **phiên thật của user còn nguyên** |
| Sau Logout | header quay về nút Đăng nhập, cookie bị xoá | ✅ `coNutDangNhap:true`, `conCookiePhien:false` |
| Khách bấm "Đăng nhập" | sang `/login` | ✅ URL đổi thành `/login` |
| Khách vào `/` và `/login` | 200 cả hai | ✅ |

Gate: `tsc` 0 · `lint` 0 error · `build` thành công.

Dọn sau kiểm: user test đã xoá, DB về đúng **10 user / 10 profile / 10 role** như trước.

## Lệch so với plan — cần biết

`app/page.tsx` giờ import từ `lib/auth` và `lib/actions`, tức **file này đã chạm cả hai
track** trong khi plan ghi "phase-16 là phase duy nhất được sửa file của cả hai track".
Đây là cố ý: giữ đúng ranh giới thì trang ở trạng thái tự mâu thuẫn không dùng được.
Phần còn lại của phase-16 (modal Viết Kudo, modal Thể lệ) vẫn để nguyên, grep `phase-16`
trong `components/home/home-page-client.tsx` để tìm.

## Câu hỏi chưa giải quyết

1. **Các trang khác chưa nối** — `/kudos`, `/awards`, `/profile` khi dựng ở phase-09..12 sẽ
   dính đúng cái bẫy này nếu lại truyền cứng `profile={null}`. Nên nối phiên ngay từ lúc
   dựng thay vì hoãn tới phase-16.
2. **`accountMenu.profile` / `accountMenu.logout` trong `locales/vi/common-ui.json` đang là
   tiếng Anh** ("Profile" / "Logout"). Phase-06 chép đúng nhãn từ Figma nên không phải lỗi
   code, nhưng cần người soạn thiết kế xác nhận có chủ đích hay quên dịch.
