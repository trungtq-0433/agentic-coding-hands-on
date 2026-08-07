"use client";

import { montserrat } from "@/components/ui/fonts";
import { useProfileT } from "./use-profile-text";

export interface BadgeCollectionProps {
  /** Heading first-person chỉ hiện trên profile của chính mình. */
  isSelf: boolean;
}

/** Luôn đúng 6 — B2..B7 (`362:5066`..`362:5071`), số slot cố định theo bản vẽ. */
const SLOT_COUNT = 6;

/**
 * Bộ sưu tập icon (`mms_A.3_Huy Hiệu`, node `362:5064`→`362:5065`) — nằm NGAY
 * DƯỚI hero, không phải trong thẻ thống kê (TC_WEB_PROFILE_GUI_002: "Inspect the
 * badge row below the hero").
 *
 * **6 slot KHÔNG có ảnh thật để desaturate.** Đo qua MCP: cả 6 instance
 * (component set `737:20452`) đều fill màu ĐẶC `#323231`, không nằm trong danh
 * sách `get_media_files`/`list_media_nodes` (30 media của màn này không có node
 * nào thuộc B2-B7) — tức bản vẽ tự vẽ trạng thái khoá bằng màu phẳng, không phải
 * ảnh huy hiệu bị làm xám. Không có gì để tải/để desaturate; dùng thẳng màu đó.
 *
 * Kích thước đo thật: ô chứa 80×64, icon con 64×64 viền trắng 2px bo tròn, gap
 * giữa các ô 16px.
 */
export function BadgeCollection({ isSelf }: BadgeCollectionProps) {
  const t = useProfileT();
  const heading = isSelf ? t("badge.headingSelf") : t("badge.headingOther");
  const lockedAria = t("badge.slotLockedAria");

  return (
    <div className="flex w-full flex-col items-center gap-4">
      <h2 className={`${montserrat.className} text-lg font-bold text-white`}>{heading}</h2>
      <div className="flex flex-wrap items-center justify-center gap-4">
        {Array.from({ length: SLOT_COUNT }, (_, i) => (
          <span
            key={i}
            role="img"
            aria-label={lockedAria}
            className="h-16 w-16 shrink-0 rounded-full border-2 border-white bg-[#323231]"
          />
        ))}
      </div>
    </div>
  );
}
