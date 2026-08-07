/**
 * Validate loại file ảnh — tách khỏi `image-upload-field.tsx` để test được
 * không cần DOM/File thật giả lập phức tạp (Track A, không backend nào ép
 * lại luật này ở đây — server phase-16 vẫn là nguồn chặn thật).
 *
 * Kiểm bằng MIME prefix `image/` thay vì whitelist đuôi file: bao trọn
 * jpg/png/gif/webp (TC_21/22) và loại đúng pdf/mp4/txt (TC_23/24/55) mà không
 * phải liệt kê từng đuôi.
 */
export function isAcceptedImageFile(file: File): boolean {
  return file.type.startsWith("image/");
}

export const MAX_IMAGES = 5;
