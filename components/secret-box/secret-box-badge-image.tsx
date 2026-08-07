"use client";

import Image from "next/image";

import type { SecretBoxBadge } from "./secret-box-types";
import { useSecretBoxT } from "./use-secret-box-text";

export interface SecretBoxBadgeImageProps {
  badge: SecretBoxBadge | null;
}

/**
 * Huy hiệu nhận được, hiển thị đè lên giữa hộp quà (spec item C).
 *
 * **Vì sao có fallback dạng chữ:** TC `43badf5d-…` (spec-open-secret-box) yêu
 * cầu tường minh "A fallback/default image is displayed for invalid badge
 * data" khi ảnh huy hiệu hỏng/thiếu. Track A không có node Figma nào cho 6
 * huy hiệu (Stay Gold/Flow to Horizon/Beyond the Boundary/Root Further/Touch
 * of Light/Revival) ở màn này — `get_overview` xác nhận `C_Box image`
 * (node `1466:7684`) chỉ có đúng 2 layer minh họa hộp
 * (`MM_MEDIA_box quà chưa mở`, `MM_MEDIA_hiệu ứng box quà`), không có node
 * huy hiệu thứ ba nào. Ảnh huy hiệu phải đến từ `badge.imageUrl` do server
 * cấp (bảng `badges`, phase-16) — thiếu/`null` thì hiện fallback chữ, không
 * tự vẽ ảnh thay thế (đúng cạm bẫy "đừng bịa ảnh" đã cảnh báo ở phase-07/09).
 *
 * `unoptimized`: `imageUrl` tới từ server ở phase-16, host chưa biết trước —
 * Track A không được sửa `next.config.ts` (ngoài ownership) để khai
 * `remotePatterns` cho host đó. Bỏ qua bộ tối ưu ảnh của Next tránh phải đụng
 * file cấu hình ngoài phạm vi phase này.
 */
export function SecretBoxBadgeImage({ badge }: SecretBoxBadgeImageProps) {
  const t = useSecretBoxT();

  if (!badge) return null;

  const label = badge.name || t("badge.fallbackLabel");

  if (!badge.imageUrl) {
    return (
      <span className="relative z-10 max-w-[70%] rounded-full bg-[#00101A]/85 px-4 py-2 text-center text-[11px] font-bold text-[#FFEA9E] sm:text-sm">
        {label}
      </span>
    );
  }

  return (
    <Image
      src={badge.imageUrl}
      alt={label}
      width={220}
      height={220}
      unoptimized
      className="relative z-10 h-[40%] w-[40%] object-contain"
    />
  );
}
