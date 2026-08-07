"use client";

import { useNamespaceTranslation, type NamespaceDictionaries } from "@/lib/i18n/use-namespace-translation";
import viRules from "@/locales/vi/rules.json";
import enRules from "@/locales/en/rules.json";

/** Namespace `rules.json` — sở hữu riêng của phase-13 (`locales/*\/rules.json`). */
const DICTIONARIES: NamespaceDictionaries = {
  vi: viRules,
  en: enRules,
};

/** Hook dịch chuỗi cho namespace rules. Key thiếu → trả về chính key đó. */
export function useRulesT() {
  return useNamespaceTranslation(DICTIONARIES);
}
