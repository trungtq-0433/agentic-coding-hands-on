"use client";

import Image from "next/image";
import { montserrat } from "@/components/ui/fonts";
import { useHomeT } from "@/components/home/use-home-text";

/**
 * Khối "Root Further" trên trang chủ Sun* Kudos (SAA 2025).
 *
 * Nguồn Figma: `Frame 486` (node `3204:10152`) — container rộng 1152,
 * `padding 120px 104px`, không khai fill nên nền để trong suốt (kế thừa nền
 * của trang cha). Không nhận props — nội dung lấy từ namespace `home.json`
 * qua `useHomeT()`.
 */
export function RootFurtherSection() {
  const t = useHomeT();

  return (
    <section
      /* KHÔNG áp `padding: 120px 104px` mà Figma khai cho `Frame 486`.
         Con của frame này được đặt TUYỆT ĐỐI và không tuân theo padding đó:
         node chữ `3204:10156` trải x=180→1332 (đúng bằng mép frame, không thụt
         104px), còn `Group 434` nằm ở y=881 — CAO HƠN cả mép trên frame (899).
         Bản thân frame cũng khai height 1219 trong khi nội dung của nó cao 1256,
         tức nội dung tràn khỏi khung: đây là dữ liệu thiết kế tự mâu thuẫn, không
         phải bố cục thật.
         Đã đo cả hai đường: áp padding ngang → chữ bó còn 944px, khối cao dư
         ~470px; áp thêm padding dọc → dư ~280px. Bỏ cả hai, để `gap 120px` của
         khung `Bìa` lo khoảng cách, sai số còn ~20px đều trên toàn trang. */
      className={`${montserrat.className} mx-auto flex w-full max-w-[1152px] flex-col items-center gap-8`}
    >
      {/* Con 1 — Group 434 (3204:10153): 2 ảnh chữ xếp chồng dọc, canh giữa theo trục ngang của nhóm 290px */}
      <div className="flex w-[290px] max-w-full flex-col items-center">
        <Image
          src="/home/root-text.png"
          alt={t("rootFurther.logoAlt")}
          width={189}
          height={67}
          className="h-auto w-[189px] max-w-full"
        />
        <Image
          src="/home/further-text.png"
          alt=""
          width={290}
          height={67}
          className="h-auto w-[290px] max-w-full"
        />
      </div>

      {/* Con 2 — mms_B4_content (5001:14827): 3 khối văn bản, gap 32px giữa các khối */}
      <div className="flex flex-col gap-8 text-white">
        <p className="whitespace-pre-line text-justify text-base leading-7 font-bold md:text-lg md:leading-8 lg:text-2xl lg:leading-8">
          {t("rootFurther.para1")}
        </p>
        <p className="whitespace-pre-line text-center text-base leading-7 font-bold md:text-xl md:leading-8">
          {t("rootFurther.quote")}
        </p>
        <p className="whitespace-pre-line text-justify text-base leading-7 font-bold md:text-lg md:leading-8 lg:text-2xl lg:leading-8">
          {t("rootFurther.para2")}
        </p>
      </div>
    </section>
  );
}
