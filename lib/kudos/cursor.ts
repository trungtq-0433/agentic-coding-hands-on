/**
 * Keyset cursor cho `listKudos` (Key Insight #6) — cặp `(created_at, id)`,
 * KHÔNG dùng OFFSET. Cursor đi qua URL nên `decodeCursor` phải trả `null` khi
 * hỏng thay vì throw (Risk Assessment: "Keyset cursor rác từ URL làm sập trang").
 */
export interface KudoCursor {
  createdAt: string;
  id: number;
}

/**
 * ISO-8601 UTC như Postgres trả về: `2026-08-06T01:23:45.678Z` / `...+00:00`.
 *
 * BẮT BUỘC kiểm định dạng, không chỉ kiểm `typeof === "string"`. `createdAt`
 * được ghép thẳng vào chuỗi filter PostgREST (`.or("created_at.lt.<X>,…")`),
 * mà dấu phẩy là ký tự ngăn cách mệnh đề của PostgREST. Một cursor mang
 * `createdAt = "2000-01-01T00:00:00Z,id.gt.0"` sẽ chèn thêm một vế OR và phá
 * sạch ranh giới keyset — đã tái hiện thật: cursor hợp lệ trả 0 hàng, cursor
 * độc trả về cả trang đầu. Cursor đến từ URL nên phải coi là input thù địch.
 *
 * `id` đã được kiểm là số hữu hạn nên không phải đường vào.
 */
const ISO_8601_UTC = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?(Z|\+00:00)$/;

/** Mã hoá cursor thành chuỗi base64url an toàn để nhét vào query string. */
export function encodeCursor(cursor: KudoCursor): string {
  return Buffer.from(JSON.stringify(cursor), "utf-8").toString("base64url");
}

/**
 * Giải mã cursor. Trả `null` (không throw) khi input rỗng, sai định dạng
 * base64url, không phải JSON hợp lệ, hoặc thiếu trường — gọi nơi dùng tự
 * fallback về trang đầu tiên.
 */
export function decodeCursor(raw: string | null | undefined): KudoCursor | null {
  if (!raw) return null;

  try {
    const parsed: unknown = JSON.parse(Buffer.from(raw, "base64url").toString("utf-8"));

    if (
      typeof parsed === "object" &&
      parsed !== null &&
      "createdAt" in parsed &&
      "id" in parsed &&
      typeof (parsed as { createdAt: unknown }).createdAt === "string" &&
      ISO_8601_UTC.test((parsed as { createdAt: string }).createdAt) &&
      typeof (parsed as { id: unknown }).id === "number" &&
      Number.isFinite((parsed as { id: number }).id)
    ) {
      const candidate = parsed as KudoCursor;
      return { createdAt: candidate.createdAt, id: candidate.id };
    }

    return null;
  } catch {
    return null;
  }
}
