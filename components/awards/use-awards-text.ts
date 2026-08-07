"use client";

import { useNamespaceTranslation, type NamespaceDictionaries } from "@/lib/i18n/use-namespace-translation";
import viAwards from "@/locales/vi/awards.json";
import enAwards from "@/locales/en/awards.json";

/** Namespace `awards.json` — sở hữu riêng của phase-12 (`locales/*\/awards.json`). */
const DICTIONARIES: NamespaceDictionaries = {
  vi: viAwards,
  en: enAwards,
};

/** Hook dịch chuỗi cho namespace awards. Key thiếu → trả về chính key đó. */
export function useAwardsT() {
  return useNamespaceTranslation(DICTIONARIES);
}
