"use client";

import Image from "next/image";
import { useEffect, useId, useRef, useState } from "react";

import { CloseIcon, UserIcon } from "@/components/ui/icons";
import { montserrat } from "@/components/ui/fonts";
import { useDropdown } from "@/components/ui/use-dropdown";
import { useComposeText } from "./use-compose-text";
import type { Profile } from "./compose-kudo-types";

export interface RecipientFieldProps {
  value: Profile | null;
  onChange: (value: Profile | null) => void;
  searchSunners: (query: string) => Promise<Profile[]>;
  errorMessage?: string;
}

/** Debounce tìm kiếm — đủ để không gọi `searchSunners` trên từng phím gõ mà vẫn cảm giác tức thời. */
const SEARCH_DEBOUNCE_MS = 200;

/**
 * Trường "Người nhận" (mms_B) — search + autocomplete. Đã chọn thì hiện dạng
 * chip avatar+tên thay ô input (TC_26: chọn xong điền tên, dropdown đóng);
 * bấm "x" trên chip để đổi người nhận khác, mở lại ô tìm kiếm.
 */
export function RecipientField({ value, onChange, searchSunners, errorMessage }: RecipientFieldProps) {
  const t = useComposeText();
  const listboxId = useId();
  const { open, setOpen, rootRef } = useDropdown<HTMLDivElement>();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Profile[]>([]);
  const [loading, setLoading] = useState(false);
  /** Đánh số lời gọi để bỏ qua kết quả TRẢ VỀ TRỄ của một lần gõ đã cũ (race condition). */
  const requestIdRef = useRef(0);

  useEffect(() => {
    const trimmed = query.trim();
    // Rỗng → không có gì để gọi. Việc DỌN kết quả cũ / bật cờ `loading` đều
    // nằm ở `onChange` bên dưới (một sự kiện, không phải effect) — gọi
    // `setState` đồng bộ ngay đầu effect bị `react-hooks/set-state-in-effect`
    // coi là "điều chỉnh state theo input đổi", nên phải tính lúc input đổi
    // (sự kiện), effect chỉ còn việc LÊN LỊCH + GỌI mạng (bất đồng bộ, không bị
    // rule này chạm tới vì nằm trong callback `.then/.catch/.finally`).
    if (trimmed.length === 0) return undefined;
    const requestId = ++requestIdRef.current;
    const timer = window.setTimeout(() => {
      searchSunners(trimmed)
        .then((profiles) => {
          if (requestIdRef.current !== requestId) return; // có lời gọi mới hơn — bỏ kết quả cũ
          setResults(profiles);
        })
        .catch((error: unknown) => {
          console.error("[kudo-compose] tìm sunner thất bại:", error);
          if (requestIdRef.current === requestId) setResults([]);
        })
        .finally(() => {
          if (requestIdRef.current === requestId) setLoading(false);
        });
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [query, searchSunners]);

  function select(profile: Profile) {
    onChange(profile);
    setQuery("");
    setResults([]);
    setOpen(false);
  }

  return (
    <div className={`${montserrat.className} flex flex-col gap-2 sm:flex-row sm:items-start sm:gap-6`}>
      <span className="pt-4 text-[22px] font-bold whitespace-nowrap text-[#00101A]">
        {t("recipient.label")} <span className="text-[#B3261E]">*</span>
      </span>
      <div ref={rootRef} className="relative w-full flex-1">
        {value ? (
          <div className="flex h-14 items-center justify-between rounded-lg border border-[#998C5F] bg-white px-4">
            <span className="flex items-center gap-3">
              {value.avatarUrl ? (
                <Image src={value.avatarUrl} alt="" width={32} height={32} className="h-8 w-8 rounded-full object-cover" />
              ) : (
                <UserIcon className="h-8 w-8 text-[#00101A]" />
              )}
              <span className="font-bold text-[#00101A]">{value.name}</span>
            </span>
            <button type="button" onClick={() => onChange(null)} aria-label={t("recipient.clearAria")} className="text-[#00101A]">
              <CloseIcon className="h-5 w-5" />
            </button>
          </div>
        ) : (
          <input
            value={query}
            onChange={(event) => {
              const next = event.target.value;
              setQuery(next);
              setOpen(true);
              if (next.trim().length === 0) {
                setResults([]);
                setLoading(false);
              } else {
                setLoading(true); // bật ngay khi gõ — effect chỉ lo phần LÊN LỊCH + gọi mạng, tắt lại khi có kết quả
              }
            }}
            onFocus={() => setOpen(true)}
            placeholder={t("recipient.searchPlaceholder")}
            aria-invalid={Boolean(errorMessage)}
            role="combobox"
            aria-autocomplete="list"
            aria-controls={listboxId}
            aria-expanded={open}
            className={`h-14 w-full rounded-lg border bg-white px-6 py-4 text-[#00101A] outline-none ${
              errorMessage ? "border-[#B3261E]" : "border-[#998C5F]"
            }`}
          />
        )}
        {open && !value && query.trim().length > 0 && (
          <ul
            id={listboxId}
            role="listbox"
            className="absolute z-20 mt-1 max-h-64 w-full overflow-auto rounded-lg border border-[#998C5F] bg-[#00070C] p-1.5"
          >
            {loading && <li className="px-4 py-2 text-sm text-white/70">…</li>}
            {!loading && results.length === 0 && (
              <li className="px-4 py-2 text-sm text-white/70">{t("recipient.emptyResult")}</li>
            )}
            {!loading &&
              results.map((profile) => (
                <li key={profile.id}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={false}
                    onClick={() => select(profile)}
                    className="w-full rounded px-4 py-2 text-left text-base font-bold text-white hover:bg-[#FFEA9E]/10"
                  >
                    {profile.name}
                  </button>
                </li>
              ))}
          </ul>
        )}
        {errorMessage && <span className="mt-1 block text-sm font-bold text-[#B3261E]">{errorMessage}</span>}
      </div>
    </div>
  );
}
