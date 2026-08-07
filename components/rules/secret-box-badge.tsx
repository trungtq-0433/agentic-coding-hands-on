"use client";

import Image from "next/image";

import { montserrat } from "@/components/ui/fonts";
import { useRulesT } from "./use-rules-text";
import type { SecretBoxBadgeContent } from "@/lib/content/rules";

export interface SecretBoxBadgeProps {
  badge: SecretBoxBadgeContent;
}

/**
 * Một trong 6 huy hiệu Secret Box — icon tròn 80px + tên bên dưới (icon đã bao
 * gồm sẵn chữ tên trong ảnh flatten từ Figma, xem `lib/content/rules.ts`).
 *
 * `badge.iconSrc === null` chỉ xảy ra với `revival` (`get_media_files` trả
 * `null` dù đúng tiền tố `MM_MEDIA_` — đã thử lại 2 lần, không phải do URL hết
 * hạn). Vẫn phải hiện ĐỦ TÊN theo acceptance criteria dù thiếu ảnh, nên fallback
 * là một khung tròn viền nét đứt + tên, thay vì bỏ hẳn huy hiệu khỏi lưới 6 ô
 * (bỏ sẽ làm lệch layout 3 cột × 2 hàng và gây hiểu nhầm là chỉ có 5 huy hiệu).
 */
export function SecretBoxBadge({ badge }: SecretBoxBadgeProps) {
  const t = useRulesT();

  return (
    <div className="flex w-20 flex-col items-center gap-2 text-center">
      {badge.iconSrc ? (
        <Image
          src={badge.iconSrc}
          alt={badge.name}
          width={badge.iconWidth}
          height={badge.iconHeight}
          className="h-auto w-20"
        />
      ) : (
        <div
          role="img"
          aria-label={`${badge.name} — ${t("badges.missingIconAria")}`}
          className="flex h-16 w-16 items-center justify-center rounded-full border-2 border-dashed border-white/40"
        >
          <span className={`${montserrat.className} px-1 text-[10px] leading-3 font-bold text-white/70`}>
            {badge.name}
          </span>
        </div>
      )}
    </div>
  );
}
