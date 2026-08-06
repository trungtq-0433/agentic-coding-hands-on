"use client";

import type { SVGProps } from "react";
import Image from "next/image";
import { montserrat } from "@/components/ui/fonts";

/**
 * Dữ liệu hiển thị của một thẻ giải thưởng. KHÔNG sở hữu nguồn dữ liệu —
 * phase-12 cấp nội dung tĩnh (tiêu đề, mô tả, ảnh chữ tên giải) qua props;
 * component này chỉ render những gì được truyền vào.
 */
export interface AwardCardData {
  /** kebab-case(title), dùng cho anchor /awards#<slug> khi bấm "Chi tiết". */
  slug: string;
  title: string;
  description: string;
  /** Ảnh chữ tên giải (vd "/home/award-top-talent.png"), đặt trên nền dùng chung award-bg.png. */
  nameImageSrc: string;
  nameImageWidth: number;
  nameImageHeight: number;
}

export interface AwardCardProps {
  award: AwardCardData;
  /** t("awards.detail") — nhãn nút, lấy từ section cha để tránh gọi useHomeT() 2 lần. */
  detailLabel: string;
  onDetail: (slug: string) => void;
}

/**
 * Icon mũi tên chéo (nút "Chi tiết") — nội tuyến từ `public/home/arrow-up.svg`,
 * đổi `fill="white"` gốc thành `currentColor` để ăn theo màu chữ nút khi hover/focus.
 * Khai cục bộ trong file này vì chỉ dùng riêng cho award-card (theo yêu cầu task).
 */
function ArrowUpRightIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" {...props}>
      <path
        d="M8.49945 18.3104L5.68945 15.5004L12.0595 9.12043H7.10945V5.69043H18.3095V16.8904H14.8895V11.9404L8.49945 18.3104Z"
        fill="currentColor"
      />
    </svg>
  );
}

/**
 * Một thẻ giải thưởng — Figma `mms_C2.1_Top Talent Award` (node 2167:9075).
 *
 * Ảnh giải (336×336, `mms_C2.1.1_Picture-Award`): nền `award-bg.png` DÙNG CHUNG
 * cho cả 6 thẻ, ảnh chữ tên giải canh giữa tuyệt đối lên trên. Bán kính bo góc
 * của khối bọc lấy đúng theo `award-bg.png` (đo pixel: ~17px trên ảnh gốc 336px
 * ≈ 5% — dùng `rounded-[5%]` để bo góc luôn khớp nền dù ảnh co giãn responsive),
 * nếu không có bo góc, box-shadow sẽ lộ viền chữ nhật sắc cạnh quanh ảnh nền
 * vốn đã bo tròn. `mix-blend-screen` áp cho cả khối (nền + ảnh chữ) theo đúng
 * thuộc tính `mix-blend-mode: screen` trong Figma.
 *
 * LƯU Ý: `title`/`description` dùng `font-normal` (400) và nút "Chi tiết" dùng
 * `font-medium` (500), nhưng `components/ui/fonts.ts` (ngoài ownership của task
 * này) hiện chỉ khai `weight: ["700"]` cho Montserrat — nếu phase sở hữu
 * fonts.ts không bổ sung các weight 400/500, trình duyệt sẽ không có font-face
 * tương ứng và có thể hiển thị lệch trọng số so với thiết kế dù CSS đã đúng.
 */
export function AwardCard({ award, detailLabel, onDetail }: AwardCardProps) {
  return (
    <div className="flex w-full max-w-[336px] flex-col items-start gap-6">
      {/* Ảnh giải — nền dùng chung + ảnh chữ tên giải canh giữa */}
      <div
        className="relative aspect-square w-full max-w-[336px] overflow-hidden rounded-[5%] mix-blend-screen"
        /* `boxShadow` viết inline chứ không dùng `shadow-[...]` của Tailwind:
           giá trị hai lớp có dấu phẩy bên trong `rgba()` không được lớp arbitrary
           của Tailwind v4 dựng ra — kiểm bằng `getComputedStyle` thì `box-shadow`
           ra `rgba(0,0,0,0) 0px 0px 0px 0px`, tức bóng biến mất hoàn toàn mà
           không có lỗi build nào. Quầng sáng vàng quanh thẻ là chi tiết thật của
           thiết kế, không phải trang trí thêm. */
        style={{ boxShadow: "0 4px 4px 0 rgba(0, 0, 0, 0.25), 0 0 6px 0 #FAE287" }}
      >
        <Image
          src="/home/award-bg.png"
          alt=""
          fill
          sizes="(min-width: 1024px) 336px, (min-width: 768px) 45vw, 90vw"
          className="object-cover"
        />
        <div className="absolute inset-0 flex items-center justify-center p-8 md:p-10">
          <Image
            src={award.nameImageSrc}
            alt={award.title}
            width={award.nameImageWidth}
            height={award.nameImageHeight}
            className="h-auto max-h-full w-auto max-w-full object-contain"
          />
        </div>
      </div>

      {/* Frame 490 — tiêu đề, mô tả, nút Chi tiết. Chiều cao KHÔNG ép cố định
          vì độ dài chữ khác nhau giữa các thẻ (144/168/176px trên Figma). */}
      <div className={`${montserrat.className} flex flex-col gap-1`}>
        <h3 className="text-2xl leading-8 font-normal text-[#FFEA9E]">{award.title}</h3>
        <p className="text-base leading-6 font-normal tracking-[0.5px] text-white">{award.description}</p>
        <button
          type="button"
          onClick={() => onDetail(award.slug)}
          className="inline-flex w-fit items-center gap-1 py-4 text-base leading-6 font-medium tracking-[0.15px] text-white transition-colors duration-200 ease-out hover:text-[#FFEA9E] focus-visible:text-[#FFEA9E] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFEA9E] motion-reduce:transition-none"
        >
          {detailLabel}
          <ArrowUpRightIcon className="h-6 w-6" />
        </button>
      </div>
    </div>
  );
}
