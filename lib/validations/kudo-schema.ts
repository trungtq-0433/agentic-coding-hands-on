import { z } from "zod";

/**
 * MIME cho phép cho ảnh đính kèm kudos. Đây chỉ là lớp validate UX (client +
 * schema); lớp validate THẬT (không tin client) là kiểm `file.type` VÀ phần mở
 * rộng tên file lại một lần nữa trong `lib/actions/kudos-actions.ts` trước khi
 * upload (Architecture §Xử lý ảnh — "kiểm MIME hai lớp").
 */
export const ALLOWED_KUDO_IMAGE_MIME_TYPES = ["image/jpeg", "image/png"] as const;

export function isAllowedKudoImageFile(file: File): boolean {
  return (ALLOWED_KUDO_IMAGE_MIME_TYPES as readonly string[]).includes(file.type);
}

const MAX_HASHTAGS = 5;
const MAX_IMAGES = 5;

/**
 * Các trường dùng chung giữa form input (ảnh còn là `File` thô, trước upload)
 * và RPC input (ảnh đã thành URL, sau upload) — Requirements phi chức năng:
 * "Schema Zod dùng chung cho client và server (DRY) — một định nghĩa, hai nơi gọi."
 *
 * KHÔNG có trường tên ẩn danh tự nhập (clarifications Gap #4: nhãn cố định, bỏ
 * field tự nhập) và KHÔNG có `mentionIds` (Key Insight #1b).
 */
const kudoBaseFields = {
  // z.guid() (định dạng 8-4-4-4-12 hex tổng quát) thay vì z.uuid() (ép version/
  // variant bit theo RFC 4122): id thật từ auth.users do Supabase sinh luôn là
  // v4 hợp lệ, nhưng seed demo dùng id thủ công dạng 'a0000000-...-0000000000X'
  // KHÔNG khớp version nibble bắt buộc của z.uuid() — DB (foreign key trong RPC)
  // mới là nơi xác nhận tồn tại thật, Zod ở đây chỉ cần đúng HÌNH DẠNG.
  recipientId: z.guid({ message: "Người nhận không hợp lệ" }),
  body: z.string().trim().min(1, "Nội dung không được để trống"),
  isAnonymous: z.boolean().default(false),
  hashtagIds: z
    .array(z.number().int().positive())
    .min(1, "Chọn ít nhất 1 hashtag")
    .max(MAX_HASHTAGS, "Tối đa 5 hashtag"),
};

/**
 * Input từ modal "Viết Kudo" phía client, TRƯỚC khi upload ảnh — dùng để
 * validate UX ngay trong form (0-5 ảnh, chỉ jpeg/png) trước khi gọi
 * `uploadKudoImagesAction`.
 */
export const kudoFormSchema = z.object({
  ...kudoBaseFields,
  images: z
    .array(
      z
        .instanceof(File, { message: "Tệp đính kèm không hợp lệ" })
        .refine(isAllowedKudoImageFile, "Chỉ chấp nhận ảnh JPEG hoặc PNG"),
    )
    .max(MAX_IMAGES, "Tối đa 5 ảnh")
    .default([]),
});

export type KudoFormInput = z.infer<typeof kudoFormSchema>;

/**
 * Input cho `createKudoAction` → RPC `create_kudos`, SAU khi ảnh đã upload
 * xong (URL, không còn `File` — Architecture: "Upload xong mới gọi
 * create_kudos với mảng URL").
 */
export const createKudoRpcInputSchema = z.object({
  ...kudoBaseFields,
  imageUrls: z.array(z.url({ message: "URL ảnh không hợp lệ" })).max(MAX_IMAGES, "Tối đa 5 ảnh").default([]),
});

export type CreateKudoRpcInput = z.infer<typeof createKudoRpcInputSchema>;
