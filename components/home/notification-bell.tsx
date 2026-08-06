"use client";

import { useHomeT } from "./use-home-text";

export interface NotificationBellProps {
  /** Có thông báo chưa đọc → hiện chấm đỏ. Mặc định `false`. */
  hasUnread?: boolean;
  onClick?: () => void;
}

/**
 * Chuông thông báo ở header (`mms_A1.6_Notification`, node `186:2098`).
 *
 * **Chỉ có vỏ, chưa có ruột.** `phase-08` chốt rõ: dựng icon + badge, KHÔNG làm
 * dữ liệu — nội dung và trigger của thông báo là gap #14 còn treo trong
 * `clarifications.md` (chưa ai chốt "thông báo cái gì, khi nào"). Vì vậy
 * `hasUnread` là prop chứ không phải state tự truy vấn, và `onClick` được phép
 * bỏ trống: nút vẫn focus/hover được nhưng chưa mở panel nào.
 *
 * Icon chuông vẽ inline thay vì tải asset, theo đúng tiền lệ đã ghi trong
 * `components/ui/icons.tsx` (phase-06): hình đơn giản, tái tạo chính xác được,
 * và `currentColor` cho phép đổi màu theo ngữ cảnh. Endpoint tải asset của
 * MoMorph (`get_media_file`) trả 401 ở phiên này nên đây cũng là đường khả thi
 * duy nhất; nếu sau lấy được SVG gốc thì thay đúng trong file này.
 *
 * Số đo Figma: nút 40×40, `padding 10px`, `border-radius 4px`, nền trong suốt,
 * icon 24×24. Chấm badge 8×8 bo tròn, màu `#D4271D`, đặt lệch trái 23px / trên
 * 9px so với mép nút.
 */
export function NotificationBell({ hasUnread = false, onClick }: NotificationBellProps) {
  const t = useHomeT();
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={t("nav.notificationsAria")}
      className="relative flex h-10 w-10 items-center justify-center rounded p-2.5 text-white transition-colors duration-200 ease-out hover:text-[#FFEA9E] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFEA9E]"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-6 w-6" aria-hidden="true">
        <path
          d="M18 8a6 6 0 10-12 0c0 6-3 7-3 7h18s-3-1-3-7"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path d="M13.7 20a2 2 0 01-3.4 0" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      {hasUnread && (
        <span
          aria-hidden="true"
          className="absolute left-[23px] top-[9px] h-2 w-2 rounded-full bg-[#D4271D]"
        />
      )}
    </button>
  );
}
