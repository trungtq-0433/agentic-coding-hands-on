"use client";

import { useNamespaceTranslation, type NamespaceDictionaries } from "@/lib/i18n/use-namespace-translation";
import viLogin from "@/locales/vi/login.json";
import enLogin from "@/locales/en/login.json";

/** Namespace `login.json` — sở hữu riêng của phase-07 (`locales/*\/login.json`). */
const DICTIONARIES: NamespaceDictionaries = {
  vi: viLogin,
  en: enLogin,
};

/** Hook dịch chuỗi cho namespace login. Key thiếu → trả về chính key đó. */
export function useLoginT() {
  return useNamespaceTranslation(DICTIONARIES);
}
