"use client";

import { useNamespaceTranslation, type NamespaceDictionaries } from "@/lib/i18n/use-namespace-translation";
import viCommonUi from "@/locales/vi/common-ui.json";
import enCommonUi from "@/locales/en/common-ui.json";

/**
 * Namespace `common-ui.json` là namespace RIÊNG của phase-06 (ownership:
 * `locales/*\/common-ui.json`). Việc tra cứu theo locale hiện dùng chung
 * `useNamespaceTranslation` (bàn giao phase-01 → phase-07, xem
 * `lib/i18n/use-namespace-translation.ts`) — file này giờ chỉ còn khai 2 JSON
 * của namespace mình, không tự cài lại logic tra cứu/fallback nữa.
 */
const DICTIONARIES: NamespaceDictionaries = {
  vi: viCommonUi,
  en: enCommonUi,
};

/** Hook dịch chuỗi cho namespace common-ui. Key thiếu → trả về chính key đó. */
export function useCommonUiT() {
  return useNamespaceTranslation(DICTIONARIES);
}
