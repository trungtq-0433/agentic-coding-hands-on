import { cookies } from "next/headers";

import { DEFAULT_LOCALE, isLocale, LOCALE_COOKIE, type Locale } from "./config";

/**
 * Nạp dictionary phía server.
 *
 * Mỗi phase Track A sở hữu namespace JSON riêng (login.json, profile.json…) nên
 * không hai phase nào ghi cùng một file locale. Phase-01 chỉ seed `common`.
 */
export type Dictionary = Record<string, string>;

const loaders: Record<Locale, () => Promise<{ default: Dictionary }>> = {
  vi: () => import("../../locales/vi/common.json"),
  en: () => import("../../locales/en/common.json"),
};

/** Đọc locale từ cookie NEXT_LOCALE; giá trị lạ hoặc thiếu → DEFAULT_LOCALE. */
export async function getLocale(): Promise<Locale> {
  const value = (await cookies()).get(LOCALE_COOKIE)?.value;
  return isLocale(value) ? value : DEFAULT_LOCALE;
}

export async function getDictionary(locale: Locale): Promise<Dictionary> {
  const loaded = await loaders[locale]();
  return loaded.default;
}
