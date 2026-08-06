"use client";

import { montserrat } from "@/components/ui/fonts";
import { useHomeT } from "@/components/home/use-home-text";
import { AwardCard, type AwardCardData } from "@/components/home/award-card";

export interface AwardSectionProps {
  /** 6 phần tử — dữ liệu tĩnh do phase-12 cấp qua prop, section này không sở hữu nguồn dữ liệu. */
  awards: AwardCardData[];
  onAwardDetail: (slug: string) => void;
}

/**
 * Khối "Hệ thống giải thưởng" — trang chủ Sun* Kudos (SAA 2025).
 *
 * Header — `mms_C1_Header Giải thưởng` (node 2167:9069): flex col gap 16px
 * (eyebrow → đường kẻ 1px #2E3940 → heading). Heading dùng `clamp()` để co
 * giãn từ 57px (thiết kế 1512px) xuống mobile mà vẫn giữ tỉ lệ leading gần
 * đúng bản vẽ (64/57 ≈ 1.12).
 *
 * Lưới 6 thẻ — `mms_C2_Award list` (node 5005:14974): grid responsive
 * 1 → 2 → 3 cột, `items-start` để các thẻ cùng hàng canh đỉnh (ảnh giải
 * 336×336 đồng nhất nhưng Frame 490 mỗi thẻ cao khác nhau). Gap 80px trên
 * desktop, giảm còn 40px ở mobile/tablet cho đỡ chật.
 *
 * Khối rộng tối đa 1224px, canh giữa trang — không hardcode width tuyệt đối.
 */
export function AwardSection({ awards, onAwardDetail }: AwardSectionProps) {
  const t = useHomeT();

  return (
    /* Không tự đệm: khung `Bìa` ở `home-page.tsx` giữ `padding 96px 144px` và
       `gap 120px`. Trên Figma khối này cao đúng bằng nội dung (1353px). */
    <section className="mx-auto flex w-full max-w-[1224px] flex-col gap-10 lg:gap-20">
      {/* Con 1 — Header khối */}
      <div className={`${montserrat.className} flex flex-col gap-4`}>
        <p className="text-2xl leading-8 font-bold text-white">{t("awards.eyebrow")}</p>
        <div className="h-px w-full bg-[#2E3940]" />
        <h2 className="text-[clamp(2rem,1rem+4vw,3.5625rem)] leading-[1.12] font-bold tracking-[-0.25px] text-[#FFEA9E]">
          {t("awards.heading")}
        </h2>
      </div>

      {/* Con 2 — Lưới 6 thẻ giải */}
      {/* Khoảng cách cột THẬT là 108px, không phải 80px như thuộc tính `gap` của
          Figma khai: `Frame 491` dùng `justify-content: space-between`, nên `gap`
          chỉ là mức tối thiểu còn khoảng cách thực do phần dư quyết định. Đối
          chiếu toạ độ: thẻ 1 đóng ở x=480, thẻ 2 mở ở x=588 → 108px. Và
          3×336 + 2×108 = 1224, khớp đúng bề ngang khối. Khoảng cách HÀNG vẫn là
          80px (hàng 1 đóng 2975, hàng 2 mở 3055) — hai trục khác nhau. */}
      <div className="grid grid-cols-1 items-start gap-10 md:grid-cols-2 lg:grid-cols-3 lg:gap-x-[108px] lg:gap-y-20">
        {awards.map((award) => (
          <AwardCard key={award.slug} award={award} detailLabel={t("awards.detail")} onDetail={onAwardDetail} />
        ))}
      </div>
    </section>
  );
}
