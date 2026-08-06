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
  /**
   * `null` = bỏ lọc, quay về `placeholder`.
   *
   * Bàn giao kiểm soát phase-06 → phase-09: chữ ký cũ là `(value: string)`,
   * tức **không có cách nào biểu đạt "bỏ chọn"**. Người dùng chọn một giá trị
   * rồi thì kẹt luôn ở đó — bộ lọc không xoá được là một cái bẫy, không phải
   * một lựa chọn thiết kế. Trang cha vốn đã nhận `string | null`, chỉ có
   * dropdown là không bao giờ phát `null`.
   */
  onChange: (value: string | null) => void;
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
                  /* Bấm lại đúng mục đang chọn → BỎ chọn. Bản vẽ dropdown
                     (`721:5580` Hashtag, `WXK5AYB_rG` Phòng ban) chỉ liệt kê
                     các mục giá trị, KHÔNG có mục "Tất cả" — nên thêm một mục
                     như vậy là tự bịa thêm UI. Toggle giữ đúng danh sách mục
                     của thiết kế mà vẫn cho đường thoát. */
                  onClick={() => {
                    onChange(isActive ? null : item.value);
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
