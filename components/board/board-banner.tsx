"use client";

import Image from "next/image";

import { montserrat } from "@/components/ui/fonts";

import { PenIcon, SearchIcon } from "./board-icons";
import { useBoardT } from "./use-board-text";

export interface BoardBannerProps {
  /** Mở modal Viết Kudo (phase-10 sở hữu modal, phase-09 chỉ gọi callback mở). */
  onCompose: () => void;
  /** Mở ô tìm kiếm sunner (hành vi tìm kiếm thật do trang cha/Track B nối dây). */
  onSearchSunner: () => void;
}

/**
 * Banner đầu trang `/kudos` — dựng lại theo số đo tra trực tiếp từ Figma
 * (mm:2940:13437 `A_KV Kudos`, 1152×160 + mm:2940:13448 `Button chuc nang`,
 * 1440×72). Bản trước suy đoán sai cả chuỗi lẫn hình dạng vì dựng khi không
 * tra được Figma — xem lịch sử git.
 *
 * Track A / phase-09 — chỉ nhận dữ liệu qua props, KHÔNG import
 * `lib/data|actions|supabase|realtime`.
 *
 * **Container `max-w-[1152px] mx-auto` khớp đúng lề trái x=144** của khối
 * `A_KV Kudos` trong khung 1440 vì (1440-1152)/2 = 144 — không cần định vị
 * tuyệt đối để đạt đúng offset đó.
 *
 * **Banner KHÔNG tự vẽ ảnh keyvisual.** `MM_MEDIA_KV Background` (1440×512) là
 * nền CẤP TRANG (`2940:13432`, anh em của Header và Bìa) do `BoardBackdrop`
 * dựng; ở đây chỉ có headline + logo nằm trên nó.
 */
export function BoardBanner({ onCompose, onSearchSunner }: BoardBannerProps) {
  const t = useBoardT();

  return (
    <section className="flex w-full flex-col gap-6">
      {/* mm:2940:13437 A_KV Kudos — CHỈ headline + logo, KHÔNG có khung riêng.
          Ảnh keyvisual là nền CẤP TRANG (`2940:13432`, anh em của Header và Bìa,
          1440×512) do `BoardBackdrop` dựng — bản trước bọc thêm một hộp bo góc
          1152×160 và vẽ LẠI ảnh đó bên trong, thành ra trang có HAI ảnh keyvisual
          (đo được: 1350×486 ở tầng trang + 1062×148 trong hộp) và banner trông
          như một tấm thẻ thay vì chữ nằm trên nền tràn lề. */}
      <div className="flex flex-col items-start gap-2.5">
        <h1
          className={`${montserrat.className} text-left text-lg leading-6 font-bold text-[#FFEA9E] sm:text-2xl sm:leading-8 lg:text-[36px] lg:leading-[44px]`}
        >
          {t("banner.headline")}
        </h1>
        <Image
          src="/board/kudos-logo.svg"
          alt={t("banner.logoAlt")}
          width={593}
          height={106}
          priority
          className="h-auto w-full max-w-[200px] shrink-0 sm:max-w-[340px] lg:max-w-[593px]"
        />
      </div>

      {/* mm:2940:13448 Button chuc nang — 2 ô bo tròn dạng thanh tìm kiếm CÙNG kiểu,
          tỉ lệ bề ngang 738:381 giữ bằng flex-[738]/flex-[381] (không hardcode px);
          xuống hàng dọc ở mobile, gap giữa 2 ô 32px (sm:gap-8) khớp Figma. */}
      <div className="mx-auto flex w-full max-w-[1152px] flex-col gap-4 sm:flex-row sm:gap-8">
        <button
          type="button"
          onClick={onCompose}
          className={`${montserrat.className} inline-flex min-h-[72px] items-center justify-center gap-4 rounded-full border border-[#998C5F] bg-[#FFEA9E]/10 px-4 py-6 text-base leading-6 font-bold tracking-[0.15px] text-white transition-colors duration-200 ease-out hover:bg-[#FFEA9E]/20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFEA9E] motion-reduce:transition-none sm:flex-[738]`}
        >
          <PenIcon className="h-6 w-6 shrink-0" />
          <span>{t("banner.composePrompt")}</span>
        </button>
        <button
          type="button"
          onClick={onSearchSunner}
          className={`${montserrat.className} inline-flex min-h-[72px] items-center justify-center gap-4 rounded-full border border-[#998C5F] bg-[#FFEA9E]/10 px-4 py-6 text-base leading-6 font-bold tracking-[0.15px] text-white transition-colors duration-200 ease-out hover:bg-[#FFEA9E]/20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFEA9E] motion-reduce:transition-none sm:flex-[381]`}
        >
          <SearchIcon className="h-6 w-6 shrink-0" />
          <span>{t("banner.searchProfile")}</span>
        </button>
      </div>
    </section>
  );
}
