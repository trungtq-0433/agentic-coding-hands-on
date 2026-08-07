"use client";

import { useNamespaceTranslation, type NamespaceDictionaries } from "@/lib/i18n/use-namespace-translation";
import viCompose from "@/locales/vi/compose.json";
import enCompose from "@/locales/en/compose.json";

/** Namespace `compose.json` — sở hữu riêng của phase-10 (`locales/*\/compose.json`). */
const DICTIONARIES: NamespaceDictionaries = {
  vi: viCompose,
  en: enCompose,
};

/** Hook dịch chuỗi cho namespace compose (modal Viết Kudo). Key thiếu → trả về chính key đó. */
export function useComposeText() {
  return useNamespaceTranslation(DICTIONARIES);
}
