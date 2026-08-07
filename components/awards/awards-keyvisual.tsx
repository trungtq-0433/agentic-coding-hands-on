"use client";

import Image from "next/image";

import { montserrat } from "@/components/ui/fonts";

import { useAwardsT } from "./use-awards-text";

/**
 * Banner đầu trang `/awards` — CSV item "3" `Keyvisual`: "background image
 * (1200x871px; cover; center-crop); title 'ROOT FURTHER'; subtitle 'Sun*
 * Annual Award 2025'; logo and top-corner icons. Decorative only."
 *
 * **Giới hạn công cụ (đọc trước khi sửa):** phiên dựng trang này KHÔNG có MCP
 * momorph khả dụng (chỉ có sẵn CSV spec tải trước, không gọi được
 * `get_frame`/`get_media_files`) — bài học phase-07/09 nói agent không có
 * MCP thì suy đoán và không tự biết, nên ghi thẳng ra đây thay vì im lặng.
 * Ảnh nền + logo dưới đây là bản SAO THẬT của asset "Root Further" đã tải ở
 * phase-08 (cùng chiến dịch, cùng file Figma) — không phải ảnh bịa — nhưng
 * khung cắt 1200×871 riêng của node Keyvisual màn này chưa lấy được, nên
 * banner dùng `object-cover` trên ảnh keyvisual hiện có, tỉ lệ khung chọn gần
 * đúng 1200:871 (~72.6vw) thay vì đúng pixel gốc.
 */
export function AwardsKeyvisual() {
  const t = useAwardsT();

  return (
    <section
      aria-label={t("keyvisual.alt")}
      className="relative isolate flex w-full items-end overflow-hidden rounded-2xl"
    >
      <div className="absolute inset-0 -z-20">
        <Image
          src="/awards/keyvisual-bg.png"
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover object-top"
        />
      </div>
      <div
        aria-hidden="true"
        className="absolute inset-0 -z-10 bg-gradient-to-t from-[#00101A] via-[#00101A]/40 to-transparent"
      />

      <div className={`${montserrat.className} flex w-full flex-col gap-4 p-6 md:p-12 lg:p-16`}>
        <Image
          src="/awards/root-further-logo.png"
          alt={t("keyvisual.logoAlt")}
          width={451}
          height={200}
          priority
          className="h-auto w-full max-w-[180px] sm:max-w-[260px]"
        />
        <div className="flex flex-col gap-1">
          <h1 className="text-3xl leading-9 font-bold tracking-[-0.25px] text-[#FFEA9E] sm:text-5xl sm:leading-[1.1]">
            {t("keyvisual.title")}
          </h1>
          <p className="text-lg leading-7 font-bold text-white sm:text-2xl sm:leading-8">
            {t("keyvisual.subtitle")}
          </p>
        </div>
      </div>
    </section>
  );
}
