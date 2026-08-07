"use client";

import Image from "next/image";

import { montserrat } from "@/components/ui/fonts";
import type { AwardContent } from "@/lib/content/awards";

import { MedalIcon } from "./award-icons";

export interface AwardCardProps {
  award: AwardContent;
  /** Thứ tự hiển thị (0-based) — quyết định thẻ so le ảnh trái/phải, xem "Lỗi 1". */
  index: number;
  /** Callback ref — đăng ký node DOM của thẻ vào bảng scrollspy của `AwardsPage`. */
  registerRef: (slug: string, node: HTMLElement | null) => void;
}

/**
 * Tách 1 dòng nhãn giá trị/số lượng thành các đoạn con theo `\n` — cho phép
 * `quantityLabel`/`prizeValueLabel` trong `lib/content/awards.ts` mang kèm
 * dòng phụ (vd "cho mỗi giải thưởng") hoặc mốc phân cách "Hoặc" (Signature có
 * 2 khối giá trị) mà KHÔNG phải đổi hình dạng interface `AwardContent` (vẫn
 * là 1 chuỗi duy nhất) — chỉ thêm quy ước dựng chuỗi ở nguồn dữ liệu.
 */
function ValueLines({ text }: { text: string }) {
  return (
    <>
      {text.split("\n").map((line, i) =>
        line === "Hoặc" ? (
          <p key={i} className="py-1 text-sm leading-5 font-bold tracking-[0.15px] text-[#998C5F]">
            {line}
          </p>
        ) : (
          <p key={i} className="text-base leading-6 font-bold tracking-[0.15px] text-white">
            {line}
          </p>
        ),
      )}
    </>
  );
}

/**
 * Thẻ chi tiết một hạng mục giải — `mms_D.1..D.6_*` (CSV item D.1–D.6).
 *
 * **Sửa lỗi 1 (so le trái/phải, đo bằng MCP của orchestrator):** D.1 có ảnh
 * TRÁI/chữ PHẢI (`Picture-Award` startX=443 < `D.1.2_Content` startX=819),
 * D.2 NGƯỢC LẠI (chữ startX=443 < ảnh startX=963). Thẻ chỉ số CHẴN (0,2,4 →
 * D.1/D.3/D.5) ảnh trái; LẺ (1,3,5 → D.2/D.4/D.6) ảnh phải — dùng
 * `flex-row-reverse` cho thẻ lẻ. Khoảng cách ảnh↔chữ 40px (toạ độ 779→819,
 * `gap-10` = 2.5rem = 40px), không phải 32px như bản trước.
 *
 * **Sửa lỗi 2 (khối chữ, đo bằng MCP):** thứ tự đúng là tiêu đề (hàng có icon,
 * cao 32px) → mô tả (khung 480×192, `font-bold`, `text-justify`, KHÔNG
 * `font-normal` như bản trước) → đường kẻ `1px #2E3940` → số lượng → đường kẻ
 * → giá trị (có thể nhiều dòng, xem `ValueLines`).
 *
 * Ảnh (336×336, nền `award-bg.png` dùng chung + `mix-blend-screen`, đã kiểm
 * chứng ở phase-08) và `next/image fill` (né lỗi khai sai width/height cố
 * định — bẫy đã gặp ở phase-08) giữ nguyên như bản trước.
 */
export function AwardCard({ award, index, registerRef }: AwardCardProps) {
  const imageOnRight = index % 2 === 1;

  return (
    <div
      id={award.slug}
      ref={(node) => registerRef(award.slug, node)}
      // scroll-margin-top chừa chỗ cho tiêu đề không dán sát mép trên khi cuộn
      // tới bằng anchor/scrollspy (header trang KHÔNG `fixed`, xem `awards-nav.tsx`).
      className={`flex scroll-mt-6 flex-col items-start gap-6 sm:gap-10 ${
        imageOnRight ? "sm:flex-row-reverse" : "sm:flex-row"
      }`}
    >
      <div
        className="relative aspect-square w-full max-w-[336px] shrink-0 overflow-hidden rounded-[5%] mix-blend-screen"
        // Bóng nhiều lớp: viết inline, KHÔNG dùng `shadow-[...]` — Tailwind v4
        // bỏ qua giá trị có dấu phẩy lồng trong `rgba()` (đã trả giá ở phase-08).
        style={{ boxShadow: "0 4px 4px 0 rgba(0, 0, 0, 0.25), 0 0 6px 0 #FAE287" }}
      >
        <Image src="/awards/award-bg.png" alt="" fill sizes="336px" className="object-cover" />
        <div className="absolute inset-0 flex items-center justify-center p-8">
          <Image src={award.imageUrl} alt={award.title} fill sizes="336px" className="object-contain p-2" />
        </div>
      </div>

      <div className={`${montserrat.className} flex min-w-0 flex-1 flex-col gap-4 pt-1`}>
        {/* Hàng tiêu đề — icon + tên, cao 32px theo số đo Figma. */}
        <div className="flex h-8 items-center gap-2">
          <MedalIcon className="h-6 w-6 shrink-0 text-[#FFEA9E]" />
          <h3 className="text-2xl leading-8 font-bold text-[#FFEA9E]">{award.title}</h3>
        </div>

        {/* Mô tả — khung 480×192, justify, bold, tracking 0.5px. */}
        <p className="min-h-[192px] w-full max-w-[480px] text-base leading-6 font-bold tracking-[0.5px] text-justify text-white">
          {award.description}
        </p>

        <div className="h-px w-full max-w-[480px] bg-[#2E3940]" aria-hidden="true" />
        <ValueLines text={award.quantityLabel} />

        <div className="h-px w-full max-w-[480px] bg-[#2E3940]" aria-hidden="true" />
        <ValueLines text={award.prizeValueLabel} />
      </div>
    </div>
  );
}
