import type { PostgrestError } from "@supabase/supabase-js";

/**
 * Trích mã lỗi nghiệp vụ từ một RPC `security definer` (`create_kudos`,
 * `toggle_heart`, `open_secret_box`). Ba RPC này `raise exception '<CODE>'`
 * (chuỗi thuần, không SQLSTATE tuỳ biến) nên `error.message` CHÍNH LÀ code khi
 * nó khớp danh sách đã biết trước — khác thì rơi về `fallback` để không rò
 * message lỗi hạ tầng thô (vd lỗi kết nối DB) thẳng lên UI.
 *
 * Dùng chung cho cả 3 `lib/actions/*.ts` — tránh viết lặp cùng một logic parse
 * 3 lần (mỗi action một bộ code khác nhau, nhưng cách trích ra thì giống hệt).
 */
export function mapRpcErrorCode<TCode extends string>(
  error: Pick<PostgrestError, "message">,
  knownCodes: readonly TCode[],
  fallback: TCode,
): TCode {
  const message = error.message.trim();
  return (knownCodes as readonly string[]).includes(message) ? (message as TCode) : fallback;
}
