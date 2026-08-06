import { z } from "zod";

/**
 * Add Link Box: text 1–100 ký tự (không chỉ khoảng trắng — `.trim()` chạy
 * trước `.min()` nên chuỗi toàn space sẽ còn lại rỗng và bị chặn), url
 * http/https 5–2048 ký tự.
 */
export const linkSchema = z.object({
  text: z.string().trim().min(1, "Nội dung không được để trống").max(100, "Tối đa 100 ký tự"),
  url: z
    .string()
    .trim()
    .min(5, "URL quá ngắn")
    .max(2048, "URL quá dài")
    .refine((value) => /^https?:\/\//i.test(value), "URL phải bắt đầu bằng http hoặc https")
    .refine((value) => z.url().safeParse(value).success, "URL không hợp lệ"),
});

export type LinkInput = z.infer<typeof linkSchema>;
