"use client";

import { useNamespaceTranslation, type NamespaceDictionaries } from "@/lib/i18n/use-namespace-translation";
import viProfile from "@/locales/vi/profile.json";
import enProfile from "@/locales/en/profile.json";

/** Namespace `profile.json` — sở hữu riêng của phase-11 (`locales/*\/profile.json`). */
const DICTIONARIES: NamespaceDictionaries = {
  vi: viProfile,
  en: enProfile,
};

/** Hook dịch chuỗi cho namespace profile. Key thiếu → trả về chính key đó. */
export function useProfileT() {
  return useNamespaceTranslation(DICTIONARIES);
}
