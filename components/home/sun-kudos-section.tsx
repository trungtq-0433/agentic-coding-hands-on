"use client";

import Image from "next/image";
import { montserrat } from "@/components/ui/fonts";
import { useHomeT } from "@/components/home/use-home-text";

export interface SunKudosSectionProps {
  onDetail: () => void;
}

/**
 * Icon mũi tên chéo (inline SVG, nội tuyến từ `public/home/arrow-up.svg`).
 * Dùng `currentColor` thay vì `fill="white"` gốc để icon ăn theo màu chữ
 * của nút — `<img>` không cho phép đổi màu theo ngữ cảnh như vậy.
 */
function ArrowUpIcon() {
  return (
    <svg
      width={24}
      height={24}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M8.49945 18.3104L5.68945 15.5004L12.0595 9.12043H7.10945V5.69043H18.3095V16.8904H14.8895V11.9404L8.49945 18.3104Z"
        fill="currentColor"
      />
    </svg>
  );
}

/**
 * Khối "Sun* Kudos" trên trang chủ SAA 2025.
 *
 * Nguồn Figma: `mms_D1_Sunkudos` (node `3390:10349`), khối trong 1120×500.
 * Nền `#0F0F0F` phủ ảnh `kudos-background.png`, nội dung lệch trái, logo lệch phải.
 * Không import `lib/data|actions|supabase|realtime` — hành động "Chi tiết" nhận
 * qua prop `onDetail` từ component cha (điều hướng thuộc Track B).
 */
export function SunKudosSection({ onDetail }: SunKudosSectionProps) {
  const t = useHomeT();

  return (
    <section
      /* `isolate` là BẮT BUỘC, không phải trang trí: ảnh nền dưới đây dùng
         `-z-10`. Nếu section không tự tạo stacking context thì con z âm sẽ
         được vẽ TRƯỚC nền `bg-[#0F0F0F]` của chính section (thứ tự sơn của CSS:
         con z âm nằm ở bước 2, còn phần tử positioned như section này nằm ở
         bước 8) — kết quả là ảnh nền biến mất hoàn toàn. `isolate` khoá z âm
         lại bên trong section. Cùng khuôn với `login-screen.tsx`. */
      /* Bề ngang 1120px chứ không 1224px: `mms_D1_Sunkudos` rộng 1224 nhưng chỉ
         là khung canh giữa, còn TẤM THẺ nhìn thấy được là group `SunKudos`
         (`I3390:10349;313:8415`) rộng 1120, mở ở x=196 trong cột bắt đầu tại 144
         — tức thụt vào mỗi bên 52px. Để 1224 là thẻ tràn rộng hơn bản vẽ. */
      className={`${montserrat.className} relative isolate mx-auto w-full max-w-[1120px] overflow-hidden rounded-2xl bg-[#0F0F0F] px-6 py-12 md:px-12 lg:min-h-[500px] lg:px-16 lg:py-0`}
    >
      <Image
        src="/home/kudos-background.png"
        alt=""
        fill
        sizes="(max-width: 1200px) 100vw, 1120px"
        className="-z-10 object-cover"
      />

      <div className="flex flex-col items-start gap-8 lg:min-h-[500px] lg:flex-row lg:items-center lg:justify-between">
        {/* mms_D2_Content (I3390:10349;313:8419) — nội dung bên trái, gap 32px */}
        <div className="flex max-w-full flex-col items-start gap-8 lg:max-w-[457px]">
          {/* Frame 494 — gap 16px giữa eyebrow / heading / thân bài. Tách khỏi
              nút vì Figma đặt nút ở Frame 495, cách Frame 494 đúng 32px (gap
              của khối cha). Gộp cả 4 vào một flex gap-8 là đẩy 3 phần chữ ra xa
              nhau gấp đôi bản vẽ. */}
          <div className="flex flex-col items-start gap-4">
            <p className="text-2xl leading-8 font-bold text-white">{t("kudos.eyebrow")}</p>

            <h2 className="text-[clamp(2.25rem,5vw,3.5625rem)] leading-[1.1] font-bold tracking-[-0.25px] text-[#FFEA9E] lg:leading-[64px]">
              {t("kudos.heading")}
            </h2>

            <div className="text-base leading-6 font-bold tracking-[0.5px] text-justify text-white">
              <p>{t("kudos.bodyTitle")}</p>
              <p>{t("kudos.body")}</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onDetail}
            className="flex items-center gap-2 rounded bg-[#FFEA9E] p-4 text-base leading-6 font-bold tracking-[0.15px] text-[#00101A]"
          >
            {t("kudos.detail")}
            <ArrowUpIcon />
          </button>
        </div>

        {/* MM_MEDIA_Logo/Kudos — logo bên phải, hơi trên giữa */}
        <Image
          src="/home/kudos-logo.svg"
          alt={t("kudos.logoAlt")}
          width={364}
          height={74}
          className="hidden h-auto lg:mr-[84px] lg:block lg:w-[364px]"
        />
      </div>
    </section>
  );
}
