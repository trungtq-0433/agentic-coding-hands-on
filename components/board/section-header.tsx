"use client";

import type { ReactNode } from "react";

import { montserrat } from "@/components/ui/fonts";

import { useBoardT } from "./use-board-text";

export interface SectionHeaderProps {
  /** Tiêu đề lớn, vd "HIGHLIGHT KUDOS". */
  title: string;
  /** Vùng bên phải cùng hàng tiêu đề (bộ lọc…). Không có thì tiêu đề chiếm cả hàng. */
  slot?: ReactNode;
}

/**
 * Header của một khối nội dung — mẫu lặp lại 3 lần trên màn Live board
 * (`B.1_header` 2940:13452, `B.6_` 2940:13476, `C.1_` 2940:14221) và cũng chính
 * là mẫu đã dùng ở khối "Hệ thống giải thưởng" trang chủ.
 *
 * Số đo Figma, giống hệt ở cả ba chỗ:
 *   eyebrow "Sun* Annual Awards 2025" — Montserrat 700 `24px/32px`, trắng
 *   ↓ gap 16px
 *   đường kẻ 1px `#2E3940`, rộng hết khối
 *   ↓ gap 16px
 *   hàng tiêu đề `space-between`: tiêu đề `57px/64px` `ls -0.25` `#FFEA9E`
 *                                 + slot phải (vd 2 dropdown lọc)
 *
 * Bản dựng đầu bỏ hẳn phần này — chỉ còn mỗi chữ "HIGHLIGHT KUDOS" trần, hai
 * khối kia không có gì. Đó là hệ quả của việc agent dựng khi không tra được
 * thiết kế; nay đo lại từ Figma.
 */
export function SectionHeader({ title, slot }: SectionHeaderProps) {
  const t = useBoardT();

  return (
    <div className={`${montserrat.className} flex w-full flex-col gap-4`}>
      <p className="text-2xl leading-8 font-bold text-white">{t("section.eyebrow")}</p>
      <div className="h-px w-full bg-[#2E3940]" aria-hidden="true" />
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <h2 className="text-[clamp(2rem,1rem+4vw,3.5625rem)] leading-[1.12] font-bold tracking-[-0.25px] text-[#FFEA9E]">
          {title}
        </h2>
        {slot && <div className="flex shrink-0 items-center gap-2">{slot}</div>}
      </div>
    </div>
  );
}
