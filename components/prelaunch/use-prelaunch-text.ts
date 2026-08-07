"use client";

import { useNamespaceTranslation, type NamespaceDictionaries } from "@/lib/i18n/use-namespace-translation";
import viPrelaunch from "@/locales/vi/prelaunch.json";
import enPrelaunch from "@/locales/en/prelaunch.json";

/** Namespace `prelaunch.json` — sở hữu riêng của phase-14 (`locales/*\/prelaunch.json`). */
const DICTIONARIES: NamespaceDictionaries = {
  vi: viPrelaunch,
  en: enPrelaunch,
};

/** Hook dịch chuỗi cho namespace prelaunch. Key thiếu → trả về chính key đó. */
export function usePrelaunchT() {
  return useNamespaceTranslation(DICTIONARIES);
}
