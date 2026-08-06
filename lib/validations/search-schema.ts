import { z } from "zod";

/** Tìm kiếm Sunner (Spotlight) — không bắt buộc, tối đa 100 ký tự. */
export const searchSchema = z.object({
  query: z.string().trim().max(100, "Tối đa 100 ký tự").default(""),
});

export type SearchInput = z.infer<typeof searchSchema>;
