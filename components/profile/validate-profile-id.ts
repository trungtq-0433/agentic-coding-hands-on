/**
 * Diễn giải query param `?id` của `/profile` — hàm THUẦN (không I/O, không React),
 * để test được không cần mock Next.js/Supabase. `app/profile/page.tsx` gọi hàm này
 * TRƯỚC khi chạm tới bất kỳ dữ liệu nào (Track B thật sẽ query ở phase-16).
 *
 * Bốn quy tắc theo test case (TC_WEB_PROFILE_FUN_002/003/004/005):
 * 1. `id` LẶP (`?id=a&id=b`, Next trả `string[]`) → `invalid` (404) — hai id trong
 *    một request không phải trang ai đó đã hỏi, tự chọn một cái là che giấu lỗi.
 * 2. `id` rỗng hoặc vắng mặt → `self` — query string bị xoá không phải là lỗi.
 * 3. `id` không đúng khuôn UUID chuẩn → `invalid` NGAY, không chạm DB — chặn
 *    Postgres 22P02 (kiểu dữ liệu sai) lộ ra thành lỗi 500.
 * 4. `id` đúng khuôn UUID và TRÙNG với id người đang đăng nhập → `self` (canonicalize) —
 *    copy link profile của chính mình không được hiện "một người lạ" của chính mình.
 * 5. Còn lại → `other` với id đã chuẩn hoá chữ thường (Postgres trả UUID chữ thường).
 */

/** Khuôn UUID chuẩn (8-4-4-4-12 hex), không phân biệt hoa/thường — không ràng buộc version/variant vì seed dùng UUID tự đặt tay (`a0000000-...`), không phải `gen_random_uuid()` thật. */
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export type ProfileIdResolution =
  | { kind: "self" }
  | { kind: "other"; id: string }
  | { kind: "invalid" };

export function resolveProfileIdParam(
  idParam: string | string[] | undefined,
  viewerId: string,
): ProfileIdResolution {
  if (Array.isArray(idParam)) {
    return { kind: "invalid" };
  }
  if (idParam === undefined || idParam === "") {
    return { kind: "self" };
  }
  if (!UUID_PATTERN.test(idParam)) {
    return { kind: "invalid" };
  }
  const normalized = idParam.toLowerCase();
  if (normalized === viewerId.toLowerCase()) {
    return { kind: "self" };
  }
  return { kind: "other", id: normalized };
}
