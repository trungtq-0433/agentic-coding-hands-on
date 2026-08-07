"use client";

import { Share_Tech_Mono } from "next/font/google";

import { montserrat } from "@/components/ui/fonts";

/**
 * Font chữ số kiểu LED — cùng lựa chọn thay thế đã dùng ở
 * `components/home/countdown-digits.tsx` (phase-08): Figma khai
 * `"Digital Numbers"` (LCD 7 đoạn) nhưng font đó không có trên Google Fonts và
 * không có sẵn trong hệ thống. `Share_Tech_Mono` là monospace nên chữ số
 * không nhảy ngang khi đếm — tiêu chí quan trọng hơn hình dáng glyph. Khai cục
 * bộ ở đây (không đưa vào `components/ui/fonts.ts`) theo đúng tiền lệ phase-08,
 * đổi font chỉ cần sửa đúng chỗ này khi có file thật.
 */
const shareTechMono = Share_Tech_Mono({
  subsets: ["latin"],
  weight: "400",
  display: "swap",
});

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

/** Một ô số kính đơn (1 chữ số). Nền mờ tách lớp riêng khỏi chữ số vì Figma áp
 * `opacity` cho NỀN chứ không cho chữ, không thể gộp chung một div. */
function DigitBox({ digit }: { digit: string }) {
  return (
    <div className="relative flex h-[clamp(64px,12vw,96px)] w-[clamp(40px,7vw,60px)] shrink-0 items-center justify-center">
      <div
        aria-hidden="true"
        className="absolute inset-0 rounded-xl border-[0.5px] border-[#FFEA9E] opacity-50 backdrop-blur-[16px]"
        style={{ background: "linear-gradient(180deg, #FFF 0%, rgba(255,255,255,0.10) 100%)" }}
      />
      <span
        className={`${shareTechMono.className} relative z-10 text-[clamp(32px,6vw,56px)] font-normal tabular-nums text-white`}
      >
        {digit}
      </span>
    </div>
  );
}

export interface CountdownUnitProps {
  /** Giá trị nguyên đã được chốt hợp lệ ở tầng gọi (`useCountdownRemaining`) —
   * component này chỉ format, không tự validate lại phạm vi 0–99. */
  value: number;
  label: string;
}

/** Một đơn vị đếm (Days/Hours/Minutes): 2 ô số LED + nhãn in hoa bên dưới. */
export function CountdownUnit({ value, label }: CountdownUnitProps) {
  const digits = pad2(value).split("");
  return (
    <div className="flex flex-col items-center gap-3">
      <div className="flex gap-2 sm:gap-3">
        {digits.map((digit, index) => (
          <DigitBox key={index} digit={digit} />
        ))}
      </div>
      <span
        className={`${montserrat.className} text-[clamp(16px,3vw,22px)] font-bold uppercase tracking-wide text-white`}
      >
        {label}
      </span>
    </div>
  );
}
