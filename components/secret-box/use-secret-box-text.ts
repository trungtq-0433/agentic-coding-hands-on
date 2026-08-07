"use client";

import { useNamespaceTranslation, type NamespaceDictionaries } from "@/lib/i18n/use-namespace-translation";
import viSecretBox from "@/locales/vi/secret-box.json";
import enSecretBox from "@/locales/en/secret-box.json";

/** Namespace `secret-box.json` — sở hữu riêng của phase-15 (`locales/*\/secret-box.json`). */
const DICTIONARIES: NamespaceDictionaries = {
  vi: viSecretBox,
  en: enSecretBox,
};

/** Hook dịch chuỗi cho namespace secret-box. Key thiếu → trả về chính key đó. */
export function useSecretBoxT() {
  return useNamespaceTranslation(DICTIONARIES);
}
