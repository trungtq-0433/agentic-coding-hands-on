"use client";

import { useNamespaceTranslation, type NamespaceDictionaries } from "@/lib/i18n/use-namespace-translation";
import viBoard from "@/locales/vi/board.json";
import enBoard from "@/locales/en/board.json";

/** Namespace `board.json` — sở hữu riêng của phase-09 (`locales/*\/board.json`). */
const DICTIONARIES: NamespaceDictionaries = {
  vi: viBoard,
  en: enBoard,
};

/** Hook dịch chuỗi cho namespace board. Key thiếu → trả về chính key đó. */
export function useBoardT() {
  return useNamespaceTranslation(DICTIONARIES);
}
