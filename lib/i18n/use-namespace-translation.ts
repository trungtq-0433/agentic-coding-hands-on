"use client";

import { useLocale } from "./locale-provider";
import type { Locale } from "./config";
import type { Dictionary } from "./get-dictionary";

/** Dictionary đủ cả hai locale cho một namespace — component gọi tự import 2 file JSON tĩnh. */
export type NamespaceDictionaries = Record<Locale, Dictionary>;

/**
 * Hook dịch chuỗi dùng chung cho MỌI namespace phía client (thay cho việc mỗi
 * phase Track A tự viết một hook `use-xxx-text.ts` gần như giống hệt nhau).
 *
 * Namespace JSON vẫn import tĩnh tại nơi gọi (`import viLogin from
 * "@/locales/vi/login.json"`) — component nào cần namespace nào tự import đúng
 * 2 file của mình, không có bảng tra cứu trung tâm nào phải sửa khi thêm màn
 * mới. Hook này chỉ gói phần logic lặp lại: tra theo `locale` hiện tại + fallback
 * về chính key khi thiếu bản dịch (để lộ rõ chỗ chưa dịch thay vì render trống).
 *
 * Locale lấy qua `useLocale()` có sẵn từ `LocaleProvider` (không tạo context mới).
 */
export function useNamespaceTranslation(dictionaries: NamespaceDictionaries) {
  const locale = useLocale();
  const dictionary = dictionaries[locale];
  return (key: string): string => dictionary[key] ?? key;
}
