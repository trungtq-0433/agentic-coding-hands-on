"use client";

import { CheckCircleIcon, PlusIcon } from "./icons";
import { montserrat } from "./fonts";
import { useCommonUiT } from "./use-common-ui-text";
import { useDropdown } from "./use-dropdown";

export interface HashtagItem {
  value: string;
  label: string;
}

export interface MultiHashtagPickerProps {
  items: HashtagItem[];
  value: string[];
  onChange: (value: string[]) => void;
  max?: number;
}

/**
 * Dropdown multi-select hashtag (p9zO-c4a4x) — chọn tối đa `max` (mặc định
 * 5) hashtag. Đủ số lượng tối đa → các item CHƯA chọn bị disable (item ĐÃ
 * chọn vẫn bấm được để bỏ chọn).
 */
export function MultiHashtagPicker({ items, value, onChange, max = 5 }: MultiHashtagPickerProps) {
  const t = useCommonUiT();
  const { open, setOpen, rootRef } = useDropdown<HTMLDivElement>();
  const reachedMax = value.length >= max;

  function toggle(itemValue: string) {
    const isSelected = value.includes(itemValue);
    if (isSelected) {
      onChange(value.filter((v) => v !== itemValue));
      return;
    }
    if (reachedMax) return; // đủ tối đa — khoá phần còn lại, không cho chọn thêm
    onChange([...value, itemValue]);
  }

  return (
    <div ref={rootRef} className={`${montserrat.className} relative inline-block`}>
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className="flex items-center gap-2 rounded-lg border border-[#998C5F] bg-white px-2 py-1"
      >
        <PlusIcon className="h-6 w-6 text-[#00101A]" />
        <span className="flex flex-col items-start leading-none">
          <span className="text-sm font-bold text-[#00101A]">
            {t("multiHashtagPicker.triggerLabel")}
          </span>
          <span className="text-[11px] font-bold text-[#999999]">
            {t("multiHashtagPicker.triggerHint").replace("{max}", String(max))}
          </span>
        </span>
      </button>
      {open && (
        <ul
          role="listbox"
          aria-multiselectable="true"
          className="absolute z-20 mt-1 w-[318px] rounded-lg border border-[#998C5F] bg-[#00070C] p-1.5"
        >
          {items.map((item) => {
            const isSelected = value.includes(item.value);
            const disableUnselected = !isSelected && reachedMax;
            return (
              <li key={item.value}>
                <button
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  disabled={disableUnselected}
                  onClick={() => toggle(item.value)}
                  className={`flex w-full items-center justify-between rounded-sm px-4 py-2 text-left text-base font-bold leading-6 tracking-[0.15px] text-white disabled:cursor-not-allowed disabled:opacity-40 ${
                    isSelected ? "bg-[#FFEA9E]/20" : "hover:bg-[#FFEA9E]/10"
                  }`}
                >
                  <span>{item.label}</span>
                  {isSelected && (
                    <CheckCircleIcon
                      aria-label={t("multiHashtagPicker.selectedAria")}
                      className="h-6 w-6"
                    />
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
