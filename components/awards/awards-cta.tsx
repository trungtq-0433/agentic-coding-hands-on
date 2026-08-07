"use client";

import Image from "next/image";

import { montserrat } from "@/components/ui/fonts";

import { useAwardsT } from "./use-awards-text";

export interface AwardsCtaProps {
  onDetail: () => void;
}

/** Icon mũi tên chéo — nội tuyến, cùng path dùng chung toàn bộ site (arrow-up.svg). */
function ArrowUpRightIcon() {
  return (
    <svg width={24} height={24} viewBox="0 0 24 24" fill="none" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M8.49945 18.3104L5.68945 15.5004L12.0595 9.12043H7.10945V5.69043H18.3095V16.8904H14.8895V11.9404L8.49945 18.3104Z"
        fill="currentColor"
      />
    </svg>
  );
}

/**
 * Block CTA "Sun* Kudos" ở cuối trang `/awards` — CSV item D1/D2/D2.1
 * "Promotional block for 'Sun* Kudos' recognition program", nút "Chi tiết"
 * điều hướng sang `/kudos`.
 *
 * Cùng nội dung quảng bá với khối tương tự ở Homepage
 * (`components/home/sun-kudos-section.tsx`, node Figma KHÁC — `335:12023` ở
 * đây so với `3390:10349` bên Homepage, tức hai instance riêng chứ không phải
 * cùng một component) nên dựng LẠI độc lập ở đây thay vì import chéo sang
 * `components/home/**` (ngoài phạm vi sở hữu phase-12). Chuỗi tiếng Việt/Anh
 * trùng nội dung là nội dung quảng bá thật giống nhau, không phải chép nhầm —
 * xem `locales/vi/awards.json` mục `cta.*`.
 *
 * Không tự gọi `useRouter()`: `onDetail` nhận từ `AwardsPage` qua prop
 * `onNavigate`, giữ component này thuần hiển thị.
 */
export function AwardsCta({ onDetail }: AwardsCtaProps) {
  const t = useAwardsT();

  return (
    <section
      className={`${montserrat.className} relative isolate mx-auto w-full max-w-[1120px] overflow-hidden rounded-2xl border border-[#998C5F]/40 bg-[#0F0F0F] px-6 py-12 md:px-12 lg:px-16 lg:py-16`}
    >
      <div className="flex flex-col items-start gap-8 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex max-w-full flex-col items-start gap-8 lg:max-w-[457px]">
          <div className="flex flex-col items-start gap-4">
            <p className="text-2xl leading-8 font-bold text-white">{t("cta.eyebrow")}</p>
            <h2 className="text-[clamp(2.25rem,5vw,3.5625rem)] leading-[1.1] font-bold tracking-[-0.25px] text-[#FFEA9E]">
              {t("cta.heading")}
            </h2>
            <div className="text-base leading-6 font-bold tracking-[0.5px] text-justify text-white">
              <p>{t("cta.bodyTitle")}</p>
              <p>{t("cta.body")}</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onDetail}
            className="flex items-center gap-2 rounded bg-[#FFEA9E] p-4 text-base leading-6 font-bold tracking-[0.15px] text-[#00101A] transition-colors duration-200 ease-out hover:bg-[#ffe17a] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFEA9E] motion-reduce:transition-none"
          >
            {t("cta.detail")}
            <ArrowUpRightIcon />
          </button>
        </div>

        {/* Cùng logo `MM_MEDIA_Logo/Kudos` đã tải ở phase-08 — sao chép riêng
            vào `public/awards/` để phase này tự chủ, không phụ thuộc đường dẫn
            do phase-08 sở hữu (có thể đổi/xoá lúc dọn dẹp phase-16). */}
        <Image
          src="/awards/kudos-logo.svg"
          alt={t("cta.logoAlt")}
          width={364}
          height={74}
          className="hidden h-auto lg:block lg:w-[300px]"
        />
      </div>
    </section>
  );
}
