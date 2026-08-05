/**
 * Bảng route + hàm thuần cho lớp Proxy (kiểm tra lạc quan, không query DB).
 *
 * Proxy chỉ biết "có session hay không" (đã lấy từ `updateSession`), KHÔNG biết
 * role — việc đó thuộc DAL (`requireAdmin()`), nơi query bảng `user_roles` mới
 * nhất mỗi request. Vì vậy hàm ở đây chỉ xử lý hai việc: đá route cần đăng nhập
 * về `/login` khi chưa có session, và đá `/login` về `/` khi đã có session rồi.
 */

/** Route bắt buộc phải đăng nhập mới vào được. */
export const PROTECTED_PREFIXES = ["/profile", "/admin"] as const;

/** Route bắt buộc phải có role admin — hiện dùng để tài liệu hoá ma trận quyền
 * và cho DAL/test tái sử dụng; proxy KHÔNG tự kiểm role (không query DB). */
export const ADMIN_PREFIXES = ["/admin"] as const;

/** Route chỉ dành cho khách chưa đăng nhập — có session rồi thì bị đá đi. */
export const GUEST_ONLY_PREFIXES = ["/login"] as const;

export type RouteAccessDecision = { redirectTo: string } | null;

function matchesPrefix(pathname: string, prefixes: readonly string[]): boolean {
  return prefixes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

/**
 * Quyết định proxy có cần redirect hay không, dựa trên pathname và việc
 * request đã có session hợp lệ hay chưa (đọc từ cookie, không phải role).
 */
export function evaluateRouteAccess(pathname: string, hasSession: boolean): RouteAccessDecision {
  if (matchesPrefix(pathname, PROTECTED_PREFIXES) && !hasSession) {
    return { redirectTo: "/login" };
  }

  if (matchesPrefix(pathname, GUEST_ONLY_PREFIXES) && hasSession) {
    return { redirectTo: "/" };
  }

  return null;
}
