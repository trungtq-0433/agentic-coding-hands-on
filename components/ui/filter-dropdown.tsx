"use client";

import { ChevronDownIcon } from "./icons";
import { montserrat } from "./fonts";
import { useCommonUiT } from "./use-common-ui-text";
import { useDropdown } from "./use-dropdown";

export interface FilterDropdownItem {
  value: string;
  label: string;
}

export interface FilterDropdownProps {
  items: FilterDropdownItem[];
  value: string | null;
  onChange: (value: string) => void;
  placeholder: string;
}

/**
 * Dropdown single-select dùng chung cho "Dropdown Hashtag filter" và
 * "Dropdown Phòng ban" (JWpsISMAaM / WXK5AYB_rG) — 2 màn Figma khác nhau
 * nhưng cùng 1 component style (`563:8216`), chỉ khác `items`/`placeholder`
 * do trang cha truyền vào.
 *
 * Figma chỉ có frame ở trạng thái ĐANG MỞ (menu), không có trạng thái nút
 * trigger đóng — chrome nút trigger dưới đây được suy ra nhất quán theo
 * design token chung (viền #998C5F, radius 8px) của MultiHashtagPicker, nơi
 * CÓ trạng thái trigger trong thiết kế.
 */
export function FilterDropdown({ items, value, onChange, placeholder }: FilterDropdownProps) {
  const t = useCommonUiT();
  const { open, setOpen, rootRef } = useDropdown<HTMLDivElement>();
  const selected = items.find((item) => item.value === value);

  return (
    <div ref={rootRef} className={`${montserrat.className} relative inline-block text-left`}>
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className="flex items-center gap-2 rounded-lg border border-[#998C5F] bg-white px-3 py-2 text-sm font-bold text-[#00101A]"
      >
        <span>{selected?.label ?? placeholder}</span>
        <ChevronDownIcon aria-label={t("dropdown.chevronAria")} className="h-4 w-4" />
      </button>
      {open && (
        <ul
          role="listbox"
          className="absolute z-20 mt-1 min-w-[180px] rounded-lg border border-[#998C5F] bg-[#00070C] p-1.5"
        >
          {items.map((item) => {
            const isActive = item.value === value;
            return (
              <li key={item.value}>
                <button
                  type="button"
                  role="option"
                  aria-selected={isActive}
                  onClick={() => {
                    onChange(item.value);
                    setOpen(false);
                  }}
                  style={
                    isActive
                      ? { textShadow: "0 4px 4px rgba(0,0,0,.25), 0 0 6px #FAE287" }
                      : undefined
                  }
                  className={`w-full rounded px-4 py-4 text-left text-base font-bold leading-6 tracking-[0.5px] text-white ${
                    isActive ? "bg-[#FFEA9E]/10" : "hover:bg-[#FFEA9E]/10"
                  }`}
                >
                  {item.label}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
