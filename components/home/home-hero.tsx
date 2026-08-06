"use client";

import Image from "next/image";

import { montserrat } from "@/components/ui/fonts";

import { CountdownDigits } from "./countdown-digits";
import { useHomeT } from "./use-home-text";

export interface HomeHeroProps {
  targetIso: string;
  onAboutAwards: () => void;
  onAboutKudos: () => void;
}

/** Icon mũi tên chéo lên — nội tuyến từ `public/home/arrow-up.svg`. Đổi
 * `fill="white"` gốc thành `currentColor` vì 2 nút CTA có màu chữ khác nhau
 * (`#00101A` vs trắng) và `<img>` không đổi màu SVG được. */
function ArrowUpIcon() {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M8.49945 18.3104L5.68945 15.5004L12.0595 9.12043H7.10945V5.69043H18.3095V16.8904H14.8895V11.9404L8.49945 18.3104Z"
        fill="currentColor"
      />
    </svg>
  );
}

/**
 * Khối HERO của Homepage SAA 2025 (Figma frame `2167:9027`..`2167:9031`).
 * Track A / phase-08 — chỉ nhận dữ liệu qua props, KHÔNG tự fetch (không
 * import lib/data, lib/actions, lib/supabase, lib/realtime).
 */
export function HomeHero({ targetIso, onAboutAwards, onAboutKudos }: HomeHeroProps) {
  const t = useHomeT();

  return (
    // mm:2167:9031 Frame 487 — CHỈ nội dung hero.
    // Ảnh keyvisual + lớp phủ gradient KHÔNG nằm ở đây: trên Figma chúng là hai
    // node ANH EM của `Bìa` (`2167:9027` cao 1392px, `2167:9029` cao 1480px) chứ
    // không phải con của hero, và chúng trải dài xuống tận sau khối Root Further
    // (hero chỉ cao ~700px). Nhốt nền vào trong hero thì `object-cover` sẽ cắt
    // ảnh còn một dải giữa và khối Root Further mất nền hoạ tiết. Nền do
    // `HomePage` dựng ở tầng trang — xem `components/home/home-page.tsx`.
    // Không tự đệm dọc/ngang: khung `Bìa` ở `home-page.tsx` đã giữ
    // `padding 96px 144px` cho cả 4 khối. Trên Figma `Frame 487` cao đúng bằng
    // nội dung (596px), không có padding riêng.
    <section className="relative flex w-full flex-col gap-10">
      {/* mm:MM_MEDIA_Root Further Logo */}
      <Image
          src="/brand/root-further-logo.png"
          alt={t("hero.logoAlt")}
          width={451}
          height={200}
          priority
          className="h-auto w-full max-w-[220px] sm:max-w-[300px] lg:max-w-[451px]"
        />

        {/* mm:Frame 523 */}
        <div className="flex flex-col gap-4">
          <CountdownDigits targetIso={targetIso} />

          {/* mm:mms_B2_Thông tin sự kiện */}
          <div className="flex flex-col gap-2 lg:max-w-[637px]">
            <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:gap-[60px]">
              <p className={`${montserrat.className} flex items-baseline gap-2 text-white`}>
                <span className="text-base font-bold leading-6 tracking-[0.15px]">
                  {t("hero.timeLabel")}
                </span>
                <span className="text-xl font-bold leading-7 text-[#FFEA9E] sm:text-2xl sm:leading-8">
                  {t("hero.timeValue")}
                </span>
              </p>
              <p className={`${montserrat.className} flex items-baseline gap-2 text-white`}>
                <span className="text-base font-bold leading-6 tracking-[0.15px]">
                  {t("hero.venueLabel")}
                </span>
                <span className="text-xl font-bold leading-7 text-[#FFEA9E] sm:text-2xl sm:leading-8">
                  {t("hero.venueValue")}
                </span>
              </p>
            </div>
            <p
              className={`${montserrat.className} text-base font-bold leading-6 tracking-[0.5px] text-white`}
            >
              {t("hero.livestream")}
            </p>
          </div>
        </div>

        {/* mm:mms_B3_Call-To-Action */}
        <div className="flex flex-col gap-4 sm:flex-row sm:gap-10">
          {/* mm:2167:9063 */}
          <button
            type="button"
            onClick={onAboutAwards}
            className={`${montserrat.className} inline-flex items-center justify-center gap-2 rounded-lg bg-[#FFEA9E] px-6 py-4 text-lg font-bold leading-7 text-[#00101A] transition-colors duration-200 ease-out hover:bg-[#ffe17a] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFEA9E] sm:text-[22px]`}
          >
            <span>{t("hero.ctaAbout")}</span>
            <ArrowUpIcon />
          </button>
          {/* mm:2167:9064 */}
          <button
            type="button"
            onClick={onAboutKudos}
            className={`${montserrat.className} inline-flex items-center justify-center gap-2 rounded-lg border border-[#998C5F] bg-[#FFEA9E]/10 px-6 py-4 text-lg font-bold leading-7 text-white transition-colors duration-200 ease-out hover:bg-[#FFEA9E]/20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFEA9E] sm:text-[22px]`}
          >
            <span>{t("hero.ctaKudos")}</span>
            <ArrowUpIcon />
          </button>
      </div>
    </section>
  );
}
