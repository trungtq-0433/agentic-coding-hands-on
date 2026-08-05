"use client";

import { createContext, useContext, useMemo, type ReactNode } from "react";

import type { Locale } from "./config";
import type { Dictionary } from "./get-dictionary";

type LocaleContextValue = {
  locale: Locale;
  dictionary: Dictionary;
};

const LocaleContext = createContext<LocaleContextValue | null>(null);

export function LocaleProvider({
  locale,
  dictionary,
  children,
}: LocaleContextValue & { children: ReactNode }) {
  const value = useMemo(() => ({ locale, dictionary }), [locale, dictionary]);
  return <LocaleContext value={value}>{children}</LocaleContext>;
}

function useLocaleContext(): LocaleContextValue {
  const context = useContext(LocaleContext);
  if (context === null) {
    throw new Error("useT/useLocale phải nằm trong <LocaleProvider>");
  }
  return context;
}

export function useLocale(): Locale {
  return useLocaleContext().locale;
}

/**
 * Hook dịch chuỗi. Key thiếu → trả về chính key đó (hiện rõ chỗ chưa dịch thay
 * vì render ra ô trống).
 */
export function useT() {
  const { dictionary } = useLocaleContext();
  return (key: string): string => dictionary[key] ?? key;
}
