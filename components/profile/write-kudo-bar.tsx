"use client";

import { montserrat } from "@/components/ui/fonts";
import { useProfileT } from "./use-profile-text";

export interface WriteKudoBarProps {
  /** Tên người đang được xem — chèn vào chuỗi prefill (TC_WEB_PROFILE_FUN_006). */
  recipientName: string;
  onClick: () => void;
}

/**
 * Thanh "viết Kudo" (item 107677 / `mms_B_Thống kê`) — thay THẾ TOÀN BỘ thẻ
 * thống kê khi xem profile người khác (TC_WEB_PROFILE_FUN_006). Không có node
 * Figma riêng cho trạng thái này trên màn `3FoIx6ALVb` (bản vẽ chỉ có trạng thái
 * xem chính mình) nên style dựng theo mẫu nút "Viết Kudo" đã đo thật ở
 * `components/board/board-banner.tsx` (rounded-full, viền `#998C5F`, nền
 * `#FFEA9E/10`) — cùng một hành động (mở modal Viết Kudo) nên cùng một ngôn ngữ
 * hình ảnh, không tự bịa kiểu mới.
 *
 * Bấm vào mở modal Viết Kudo với người đang xem đã điền sẵn ở ô người nhận
 * (TC_WEB_PROFILE_FUN_007) — modal đó thuộc phase-10, chưa tồn tại; `onClick`
 * ở đây chỉ là điểm nối, phase-16 nối dây thật.
 */
export function WriteKudoBar({ recipientName, onClick }: WriteKudoBarProps) {
  const t = useProfileT();

  return (
    <button
      type="button"
      onClick={onClick}
      className={`${montserrat.className} inline-flex min-h-[72px] w-full max-w-[422px] items-center justify-center rounded-full border border-[#998C5F] bg-[#FFEA9E]/10 px-6 py-6 text-center text-base leading-6 font-bold tracking-[0.15px] text-white transition-colors duration-200 ease-out hover:bg-[#FFEA9E]/20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFEA9E] motion-reduce:transition-none`}
    >
      {t("writeBar.prompt").replace("{name}", recipientName)}
    </button>
  );
}
