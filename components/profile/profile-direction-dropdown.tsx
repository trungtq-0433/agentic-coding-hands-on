"use client";

import { ChevronDownIcon } from "@/components/ui/icons";
import { montserrat } from "@/components/ui/fonts";
import { useDropdown } from "@/components/ui/use-dropdown";
import { useProfileT } from "./use-profile-text";
import type { ProfileDirection } from "./profile-types";

export interface ProfileDirectionDropdownProps {
  direction: ProfileDirection;
  receivedCount: number;
  /** `null` → mục "Đã gửi" KHÔNG được liệt kê (TC_WEB_PROFILE_SEC_001), không phải chỉ ẩn số. */
  sentCount: number | null;
  onChange: (direction: ProfileDirection) => void;
}

function directionLabel(t: (key: string) => string, direction: ProfileDirection, count: number): string {
  const key = direction === "received" ? "direction.received" : "direction.sent";
  return t(key).replace("{count}", String(count));
}

/**
 * Dropdown hướng nhận/gửi (`mms_C.3_Button`, node `362:5089`) — số đo THẬT qua
 * MCP: padding `16 24`, viền 1px `#998C5F`, nền `rgba(255,234,158,.10)`, radius
 * 4px, chữ 16px/700. Không tái dùng được `FilterDropdown` (`components/ui/`):
 * dropdown đó phát `null` để "bỏ lọc" khi bấm lại mục đang chọn, còn dropdown
 * này KHÔNG có trạng thái rỗng — bấm lại mục đang chọn phải là no-op tuyệt đối,
 * không đóng thành trạng thái khác (TC_WEB_PROFILE_FUN_011).
 *
 * **`sentCount === null` xoá hẳn mục "Đã gửi" khỏi danh sách**, không phải ẩn số
 * hay disable — TC_WEB_PROFILE_SEC_001 cấm bất kỳ dấu vết nào của "Đã gửi" xuất
 * hiện trên profile người khác, vì số đã gửi tính cả kudos ẩn danh (rò được số
 * lượng ẩn danh nếu công khai).
 */
export function ProfileDirectionDropdown({
  direction,
  receivedCount,
  sentCount,
  onChange,
}: ProfileDirectionDropdownProps) {
  const t = useProfileT();
  const { open, setOpen, rootRef } = useDropdown<HTMLDivElement>();

  const options: Array<{ value: ProfileDirection; label: string }> = [
    { value: "received", label: directionLabel(t, "received", receivedCount) },
    ...(sentCount !== null ? [{ value: "sent" as const, label: directionLabel(t, "sent", sentCount) }] : []),
  ];
  const activeLabel = options.find((option) => option.value === direction)?.label ?? "";

  return (
    <div ref={rootRef} className={`${montserrat.className} relative inline-block text-left`}>
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={t("direction.triggerAria")}
        className="flex items-center gap-2 rounded border border-[#998C5F] bg-[#FFEA9E]/10 px-6 py-4 text-base font-bold text-white"
      >
        <span>{activeLabel}</span>
        <ChevronDownIcon className="h-4 w-4" />
      </button>
      {open && (
        <ul
          role="listbox"
          className="absolute right-0 z-20 mt-1 min-w-[180px] rounded-lg border border-[#998C5F] bg-[#00070C] p-1.5"
        >
          {options.map((option) => {
            const isActive = option.value === direction;
            return (
              <li key={option.value}>
                <button
                  type="button"
                  role="option"
                  aria-selected={isActive}
                  onClick={() => {
                    // Bấm lại đúng mục đang chọn → no-op tuyệt đối: chỉ đóng
                    // dropdown, KHÔNG gọi `onChange` (không phát lại request nạp
                    // trang 1, không đổi state) — khác hẳn `FilterDropdown` vốn
                    // toggle về `null`. TC_WEB_PROFILE_FUN_011 kiểm đúng việc này.
                    if (!isActive) onChange(option.value);
                    setOpen(false);
                  }}
                  className={`w-full rounded px-4 py-4 text-left text-base font-bold leading-6 tracking-[0.5px] text-white ${
                    isActive ? "bg-[#FFEA9E]/10" : "hover:bg-[#FFEA9E]/10"
                  }`}
                >
                  {option.label}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
