import { NextResponse, type NextRequest } from "next/server";

import { isBeforeLaunchGate, PRELAUNCH_PATH } from "./lib/launch-gate";
import { updateSession } from "./lib/supabase/proxy-session";

/**
 * Next 16 đã đổi tên Middleware → Proxy: file `proxy.ts` ở root, export tên `proxy`.
 * (`node_modules/next/dist/docs/01-app/03-api-reference/03-file-conventions/proxy.md`)
 * KHÔNG tạo `middleware.ts` — nó deprecated.
 *
 * Đây là kiểm tra LẠC QUAN phục vụ UX, không phải hàng rào an ninh.
 * Bảo mật thật nằm ở RLS (phase-02) và tầng truy cập dữ liệu (phase-03).
 * Không truy vấn DB ở đây — proxy chạy trên mọi request, kể cả prefetch.
 */
export async function proxy(request: NextRequest) {
  const { response } = await updateSession(request);

  const { pathname } = request.nextUrl;
  const onPrelaunch = pathname === PRELAUNCH_PATH;
  const beforeLaunch = isBeforeLaunchGate();

  // Chưa tới giờ mở màn → dồn hết về màn prelaunch.
  if (beforeLaunch && !onPrelaunch) {
    return redirectKeepingSession(new URL(PRELAUNCH_PATH, request.url), response);
  }

  // Đã mở màn nhưng còn nằm ở /prelaunch → đá về trang chủ.
  if (!beforeLaunch && onPrelaunch) {
    return redirectKeepingSession(new URL("/", request.url), response);
  }

  return response;
}

/**
 * Redirect mà KHÔNG đánh rơi cookie session vừa được refresh.
 *
 * `updateSession` ghi cookie mới lên `refreshed`. Trả về một NextResponse.redirect
 * trần là vứt luôn đám cookie đó — mà refresh token của Supabase là single-use:
 * server đã đốt token cũ để lấy token mới, browser thì không nhận được cái mới
 * → lần request sau mất phiên. Trong giai đoạn prelaunch MỌI request đều redirect,
 * nên lỗi này sẽ đăng xuất toàn bộ người dùng chứ không phải thi thoảng.
 */
function redirectKeepingSession(to: URL, refreshed: NextResponse): NextResponse {
  const redirect = NextResponse.redirect(to);
  for (const cookie of refreshed.cookies.getAll()) {
    redirect.cookies.set(cookie);
  }
  return redirect;
}

export const config = {
  // Loại static asset và file ảnh: proxy chạy mọi request nếu không có matcher,
  // sẽ chặn nhầm cả CSS/JS/ảnh. /prelaunch vẫn nằm trong matcher (cần refresh
  // session ở đó), việc chống redirect vòng do early-return theo pathname lo.
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};
