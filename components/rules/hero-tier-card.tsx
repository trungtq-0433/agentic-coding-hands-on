"use client";

import Image from "next/image";

import { montserrat } from "@/components/ui/fonts";
import type { HeroTierContent } from "@/lib/content/rules";

export interface HeroTierCardProps {
  tier: HeroTierContent;
}

/**
 * Một hạng Hero trong khối "Người nhận Kudos" — pill tên hạng + 2 dòng text
 * (ngưỡng số người gửi, mô tả). Tách riêng khỏi `RulesPanel` để component cha
 * không phình quá 200 dòng khi cộng cả khối 6 huy hiệu.
 *
 * Hạng `new` không có ảnh pill (`MM_MEDIA_New Hero` không có URL, giống hệt lý
 * do `HeroBadge` của phase-09 bỏ trống hạng này) — hiện chữ label thay ảnh thay
 * vì bỏ trống hoàn toàn, panel Thể lệ cần liệt kê đủ cả 4 hạng để giải thích luật.
 */
export function HeroTierCard({ tier }: HeroTierCardProps) {
  return (
    <div className="flex flex-col items-start gap-2">
      {tier.badgeSrc ? (
        <Image src={tier.badgeSrc} alt={tier.label} width={tier.badgeWidth} height={tier.badgeHeight} />
      ) : (
        <span className="rounded bg-white/10 px-2 py-0.5 text-xs font-bold tracking-[0.5px] text-white">
          {tier.label}
        </span>
      )}
      <p className={`${montserrat.className} text-base leading-6 font-bold tracking-[0.5px] text-white`}>
        {tier.range}
      </p>
      <p className={`${montserrat.className} text-sm leading-5 font-bold tracking-[0.1px] text-white`}>
        {tier.description}
      </p>
    </div>
  );
}
