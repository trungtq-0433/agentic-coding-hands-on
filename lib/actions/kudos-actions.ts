"use server";

import { randomUUID } from "node:crypto";
import { revalidatePath } from "next/cache";

import { requireUser } from "@/lib/auth/dal";
import { createClient } from "@/lib/supabase/server";
import { mapRpcErrorCode } from "@/lib/kudos/rpc-error";
import {
  createKudoRpcInputSchema,
  isAllowedKudoImageFile,
  type CreateKudoRpcInput,
} from "@/lib/validations/kudo-schema";

const STORAGE_BUCKET = "kudos-images";
const MAX_IMAGES = 5;
const MIME_EXTENSION: Readonly<Record<string, string>> = {
  "image/jpeg": "jpg",
  "image/png": "png",
};

export type CreateKudoErrorCode =
  | "UNAUTHENTICATED"
  | "VALIDATION_ERROR"
  | "SELF_KUDOS"
  | "RECIPIENT_NOT_FOUND"
  | "HASHTAG_NOT_FOUND"
  | "UNKNOWN";

export type CreateKudoResult =
  | { ok: true; kudoId: number }
  | { ok: false; code: CreateKudoErrorCode; fieldErrors?: Record<string, string[]> };

/** RPC `create_kudos` cũng ép lại 4 bất biến này (defense-in-depth — Success
 * Criteria yêu cầu kiểm bằng cách gọi RPC trực tiếp, bỏ qua UI/Zod). 3 mã cuối
 * lẽ ra Zod đã chặn trước, chỉ còn ý nghĩa nếu ai đó gọi RPC vòng qua action. */
const RPC_KNOWN_CODES = [
  "UNAUTHENTICATED",
  "SELF_KUDOS",
  "RECIPIENT_NOT_FOUND",
  "HASHTAG_NOT_FOUND",
  "EMPTY_BODY",
  "HASHTAG_COUNT_INVALID",
  "IMAGE_COUNT_INVALID",
] as const;

/**
 * Ghi kudo qua RPC `create_kudos` — validate lại đúng schema client đã dùng
 * (Requirements phi chức năng: "Schema Zod dùng chung cho client và server").
 * KHÔNG throw lỗi nghiệp vụ, trả `{ok:false, code, fieldErrors}` để UI hiện
 * lỗi theo trường (Implementation Steps bước 10). Ảnh phải upload xong từ
 * `uploadKudoImagesAction` trước, truyền vào đây dưới dạng URL — hàm này
 * không nhận `File`.
 */
export async function createKudoAction(input: unknown): Promise<CreateKudoResult> {
  await requireUser();

  const parsed = createKudoRpcInputSchema.safeParse(input);
  if (!parsed.success) {
    return {
      ok: false,
      code: "VALIDATION_ERROR",
      fieldErrors: parsed.error.flatten().fieldErrors as Record<string, string[]>,
    };
  }

  const payload: CreateKudoRpcInput = parsed.data;
  const supabase = await createClient();
  const { data, error } = await supabase.rpc("create_kudos", {
    p_recipient: payload.recipientId,
    p_body: payload.body,
    p_is_anonymous: payload.isAnonymous,
    p_hashtag_ids: payload.hashtagIds,
    p_image_urls: payload.imageUrls,
  });

  if (error) {
    const rawCode = mapRpcErrorCode(error, RPC_KNOWN_CODES, "UNKNOWN" as const);
    const validationCodes = new Set(["EMPTY_BODY", "HASHTAG_COUNT_INVALID", "IMAGE_COUNT_INVALID"]);
    const code: CreateKudoErrorCode = validationCodes.has(rawCode) ? "VALIDATION_ERROR" : (rawCode as CreateKudoErrorCode);
    return { ok: false, code };
  }

  if (data === null || data === undefined) {
    return { ok: false, code: "UNKNOWN" };
  }

  revalidatePath("/kudos");
  revalidatePath("/profile");

  return { ok: true, kudoId: data };
}

export type UploadKudoImagesErrorCode =
  | "UNAUTHENTICATED"
  | "TOO_MANY_IMAGES"
  | "INVALID_IMAGE_TYPE"
  | "UPLOAD_FAILED";

export type UploadKudoImagesResult = { ok: true; urls: string[] } | { ok: false; code: UploadKudoImagesErrorCode };

/**
 * Upload ảnh đính kèm LÊN TRƯỚC khi gọi `createKudoAction` (Architecture §Xử
 * lý ảnh: "Upload xong mới gọi create_kudos với mảng URL"). Kiểm MIME lớp THẬT
 * ở đây — `file.type` VÀ phần mở rộng tên file (client `accept` chỉ là UX) —
 * từ chối ngay khi gặp file sai định dạng, KHÔNG upload bất kỳ file nào nếu có
 * dù chỉ một file sai (Success Criteria: "Upload .pdf/.mp4/.txt → từ chối ở
 * action, không có file nào vào Storage").
 */
export async function uploadKudoImagesAction(formData: FormData): Promise<UploadKudoImagesResult> {
  const user = await requireUser();

  const files = formData
    .getAll("images")
    .filter((entry): entry is File => entry instanceof File && entry.size > 0);

  if (files.length === 0) {
    return { ok: true, urls: [] };
  }

  if (files.length > MAX_IMAGES) {
    return { ok: false, code: "TOO_MANY_IMAGES" };
  }

  for (const file of files) {
    if (!isAllowedKudoImageFile(file) || !hasAllowedImageExtension(file.name)) {
      return { ok: false, code: "INVALID_IMAGE_TYPE" };
    }
  }

  const supabase = await createClient();
  const uploadedPaths: string[] = [];
  const urls: string[] = [];

  for (const file of files) {
    const extension = MIME_EXTENSION[file.type] ?? "bin";
    const path = `${user.id}/${randomUUID()}.${extension}`;
    const { error: uploadError } = await supabase.storage
      .from(STORAGE_BUCKET)
      .upload(path, file, { contentType: file.type });

    if (uploadError) {
      console.error("[kudos-actions] Upload ảnh thất bại:", uploadError.message);
      // Dọn ảnh đã upload trước đó trong CÙNG lượt gọi này để không để lại rác
      // mồ côi trong Storage khi ảnh thứ N (N>1) lỗi giữa chừng.
      if (uploadedPaths.length > 0) {
        await supabase.storage.from(STORAGE_BUCKET).remove(uploadedPaths);
      }
      return { ok: false, code: "UPLOAD_FAILED" };
    }

    uploadedPaths.push(path);
    const { data: publicUrlData } = supabase.storage.from(STORAGE_BUCKET).getPublicUrl(path);
    urls.push(publicUrlData.publicUrl);
  }

  return { ok: true, urls };
}

function hasAllowedImageExtension(fileName: string): boolean {
  const lower = fileName.toLowerCase();
  return lower.endsWith(".jpg") || lower.endsWith(".jpeg") || lower.endsWith(".png");
}
