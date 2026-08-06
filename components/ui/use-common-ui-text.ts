"use client";

import { useLocale } from "@/lib/i18n/locale-provider";
import type { Locale } from "@/lib/i18n/config";
import viCommonUi from "@/locales/vi/common-ui.json";
import enCommonUi from "@/locales/en/common-ui.json";

type Dictionary = Record<string, string>;

/**
 * Namespace `common-ui.json` là namespace RIÊNG của phase-06 (ownership:
 * `locales/*\/common-ui.json`). `lib/i18n/get-dictionary.ts` (ngoài ownership
 * phase-06) hiện chỉ nạp `common.json` — mở rộng loader đó để gộp thêm
 * namespace này nằm ngoài quyền sửa của phase-06 (rule: sửa lib/i18n/** phải
 * BÁO, không tự sửa). Giải pháp không cần đụng lib/i18n/**: tự import tĩnh 2
 * file JSON ở đây và tra cứu theo locale hiện tại — locale vẫn đọc qua hook
 * `useLocale()` có sẵn (chỉ ĐỌC, không sửa lib/i18n).
 */
const DICTIONARIES: Record<Locale, Dictionary> = {
  vi: viCommonUi,
  en: enCommonUi,
};

/** Hook dịch chuỗi cho namespace common-ui. Key thiếu → trả về chính key đó. */
export function useCommonUiT() {
  const locale = useLocale();
  const dictionary = DICTIONARIES[locale];
  return (key: string): string => dictionary[key] ?? key;
}
