"use client";

import { useNamespaceTranslation, type NamespaceDictionaries } from "@/lib/i18n/use-namespace-translation";
import viHome from "@/locales/vi/home.json";
import enHome from "@/locales/en/home.json";

/** Namespace `home.json` — sở hữu riêng của phase-08 (`locales/*\/home.json`). */
const DICTIONARIES: NamespaceDictionaries = {
  vi: viHome,
  en: enHome,
};

/** Hook dịch chuỗi cho namespace home. Key thiếu → trả về chính key đó. */
export function useHomeT() {
  return useNamespaceTranslation(DICTIONARIES);
}
