"use client";

import { LOCALES, LOCALE_LABELS, type Locale } from "@/lib/i18n/config";

import { FlagENIcon, FlagVNIcon } from "./icons";
import { montserrat } from "./fonts";
import { useCommonUiT } from "./use-common-ui-text";
import { useDropdown } from "./use-dropdown";

export interface LanguageSwitcherProps {
  locale: Locale;
  onChange: (locale: Locale) => void;
}

const FLAG_ICON: Record<Locale, typeof FlagVNIcon> = {
  vi: FlagVNIcon,
  en: FlagENIcon,
};

/** Dropdown chọn ngôn ngữ (hUyaaugye2) — nhãn "VN"/"EN" tái dùng `LOCALE_LABELS`
 * đã có sẵn ở `lib/i18n/config.ts` (comment ở đó ghi rõ dành cho phase-06). */
export function LanguageSwitcher({ locale, onChange }: LanguageSwitcherProps) {
  const t = useCommonUiT();
  const { open, setOpen, rootRef } = useDropdown<HTMLDivElement>();
  const TriggerFlag = FLAG_ICON[locale];

  return (
    <div ref={rootRef} className={`${montserrat.className} relative inline-block`}>
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={t("languageSwitcher.ariaLabel")}
        className="flex items-center gap-2 rounded-lg border border-[#998C5F] bg-[#00070C] px-3 py-2"
      >
        <TriggerFlag className="h-6 w-6" />
        <span className="text-base font-bold text-white">{LOCALE_LABELS[locale]}</span>
      </button>
      {open && (
        <ul
          role="listbox"
          className="absolute z-20 mt-1 min-w-[140px] rounded-lg border border-[#998C5F] bg-[#00070C] p-1.5"
        >
          {LOCALES.map((code) => {
            const isActive = code === locale;
            const Flag = FLAG_ICON[code];
            return (
              <li key={code}>
                <button
                  type="button"
                  role="option"
                  aria-selected={isActive}
                  onClick={() => {
                    onChange(code);
                    setOpen(false);
                  }}
                  className={`flex w-full items-center gap-2 rounded px-4 py-4 text-base font-bold leading-6 tracking-[0.15px] text-white ${
                    isActive ? "justify-between bg-[#FFEA9E]/20" : "justify-center hover:bg-[#FFEA9E]/10"
                  }`}
                >
                  <Flag className="h-6 w-6" />
                  <span>{LOCALE_LABELS[code]}</span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
