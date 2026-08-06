"use client";

import Image from "next/image";

import type { HeroTier } from "./kudo-card-types";
import { useBoardT } from "./use-board-text";

/**
 * Huy hiệu hạng Hero cạnh tên người dùng — **109×19** theo bản vẽ
 * (`MM_MEDIA_Legend Hero` và các anh em, node `…;3106:17694`).
 *
 * Gom về một component vì trước đó bảng tra bị chép ở CẢ `kudo-card.tsx` lẫn
 * `highlight-slide.tsx` (hai agent dựng song song), và bản trong carousel khai
 * nhầm `width=20 height=20` — huy hiệu hình chữ nhật bị ép thành ô vuông rồi
 * co xuống 20×4px, bé đến mức không đọc được chữ trên đó. Một nguồn thì một
 * lần sửa là xong.
 *
 * `shrink-0` là bắt buộc: huy hiệu luôn nằm trong flex row bên trong một cột
 * hẹp, không chặn co thì flex bóp nát nó.
 *
 * Hạng `new` KHÔNG có ảnh: node `MM_MEDIA_New Hero` không có URL trong
 * `get_media_files`, `get_figma_image` trả 500 (cùng lỗi endpoint đã gặp ở
 * phase-07). Gặp `new` thì không render gì thay vì hiện ảnh vỡ.
 */
const BADGES: Record<Exclude<HeroTier, "new">, { src: string; labelKey: string }> = {
  rising: { src: "/board/badge-rising-hero.png", labelKey: "card.tierRising" },
  super: { src: "/board/badge-super-hero.png", labelKey: "card.tierSuper" },
  legend: { src: "/board/badge-legend-hero.png", labelKey: "card.tierLegend" },
};

export interface HeroBadgeProps {
  tier: HeroTier | undefined;
}

export function HeroBadge({ tier }: HeroBadgeProps) {
  const t = useBoardT();
  if (!tier || tier === "new") return null;

  const badge = BADGES[tier];
  return (
    <Image
      src={badge.src}
      alt={t(badge.labelKey)}
      width={109}
      height={19}
      className="h-[19px] w-[109px] shrink-0"
    />
  );
}
