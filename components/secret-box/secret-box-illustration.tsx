"use client";

import Image from "next/image";

import type { SecretBoxBadge } from "./secret-box-types";
import { SecretBoxBadgeImage } from "./secret-box-badge-image";
import { useSecretBoxOpen } from "./use-secret-box-open";
import { useSecretBoxT } from "./use-secret-box-text";

export interface SecretBoxIllustrationProps {
  lastBadge: SecretBoxBadge | null;
  remaining: number;
  opening: boolean;
  errorCode?: "NO_UNOPENED_BOX";
  onOpenBox: () => Promise<{ badge: SecretBoxBadge; remaining: number }>;
}

/**
 * Khung minh họa hộp quà + huy hiệu nhận được (spec item C, node `1466:7684`
 * "C_Box image", 557×557px). Có đúng 2 asset Figma hợp lệ (tiền tố `MM_MEDIA_`
 * — đã tải về `public/secret-box/`):
 * - `MM_MEDIA_box quà chưa mở` → `box-illustration.svg` (minh họa hộp)
 * - `MM_MEDIA_hiệu ứng box quà` → `box-effect.png` (lớp hào quang phía sau,
 *   node khai `background-position: -102.944px -102.487px` và
 *   `background-size: 138.527%` — giữ nguyên hai giá trị này bằng inline
 *   style vì đây là cặp phần trăm/âm phức tạp, cùng loại giá trị mà Tailwind
 *   v4 từng âm thầm bỏ qua ở `shadow-[...]` nhiều lớp của phase-08).
 *
 * Nút bấm disable khi `opening` (prop, cha đang gọi RPC) HOẶC `remaining<=0`
 * HOẶC `errorCode==="NO_UNOPENED_BOX"` (race: server báo hết hộp dù prop
 * `remaining` đo lúc mở modal vẫn còn >0). Chốt chặn double-click nằm ở
 * `useSecretBoxOpen` (ref, không phải state) — thuộc tính `disabled` của
 * `<button>` chỉ là lớp phòng vệ thứ hai, không đủ để chặn nhiều cú bấm
 * trong cùng một tick vì `opening` là prop, chỉ đổi SAU khi cha re-render.
 */
export function SecretBoxIllustration({
  lastBadge,
  remaining,
  opening,
  errorCode,
  onOpenBox,
}: SecretBoxIllustrationProps) {
  const t = useSecretBoxT();
  const handleOpen = useSecretBoxOpen(onOpenBox);
  const disabled = opening || remaining <= 0 || errorCode === "NO_UNOPENED_BOX";

  return (
    <button
      type="button"
      onClick={handleOpen}
      disabled={disabled}
      aria-label={t("modal.boxAria")}
      className="relative aspect-square w-[min(70vw,557px)] shrink-0 disabled:cursor-not-allowed disabled:opacity-60"
    >
      <div
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: "url(/secret-box/box-effect.png)",
          backgroundPosition: "-102.944px -102.487px",
          backgroundSize: "138.527%",
          backgroundRepeat: "no-repeat",
        }}
        aria-hidden="true"
      />
      <Image src="/secret-box/box-illustration.svg" alt="" fill unoptimized className="relative z-[1] object-contain" />
      <div className="absolute inset-0 z-[2] flex items-center justify-center">
        <SecretBoxBadgeImage badge={lastBadge} />
      </div>
    </button>
  );
}
