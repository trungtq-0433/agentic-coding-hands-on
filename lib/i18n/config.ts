/**
 * Cấu hình i18n — tự cuộn, không thêm dependency.
 *
 * Locale nằm ở cookie NEXT_LOCALE, KHÔNG có prefix trên URL (spec Login 1.2).
 * `next-intl` chủ yếu giải bài toán i18n routing nên ở đây là thừa (YAGNI).
 */

export const LOCALES = ["vi", "en"] as const;

export type Locale = (typeof LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "vi";

export const LOCALE_COOKIE = "NEXT_LOCALE";

/** Nhãn hiển thị trong dropdown chọn ngôn ngữ (Track A phase-06 dùng). */
export const LOCALE_LABELS: Record<Locale, string> = {
  vi: "VN",
  en: "EN",
};

export function isLocale(value: string | undefined): value is Locale {
  return value !== undefined && (LOCALES as readonly string[]).includes(value);
}
