"use client";

import { montserrat } from "@/components/ui/fonts";

import { SevenSegmentDigit } from "./seven-segment-digit";

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

/**
 * Một ô số kính đơn (1 chữ số). Nền mờ tách lớp riêng khỏi chữ số vì Figma áp
 * `opacity` cho NỀN chứ không cho chữ, không thể gộp chung một div.
 *
 * Số đo lấy từ `2268:35141` (`Group 5` → `Rectangle 1`) của bản vẽ, khung gốc
 * rộng 1512: ô **76.8×122.88**, viền **0.75px** `#FFEA9E`, bo 12px, `opacity .5`,
 * gradient trắng→10%, `backdrop-blur 24.96px`; chữ số cao **95** trong ô.
 *
 * Trần của `clamp` quy về đúng các số trên (bản trước chặn ở 60/96 — nhỏ hơn bản
 * vẽ ~22%, khiến cả khối co lại). Điểm giữa `vw` tính theo khung 1512 để ở đúng
 * khổ thiết kế thì `clamp` chạm trần: 76.8/1512 = 5.08vw, 122.88/1512 = 8.13vw.
 */
function DigitBox({ digit }: { digit: string }) {
  return (
    <div className="relative flex h-[clamp(64px,8.13vw,122.88px)] w-[clamp(40px,5.08vw,76.8px)] shrink-0 items-center justify-center">
      <div
        aria-hidden="true"
        className="absolute inset-0 rounded-xl border-[0.75px] border-[#FFEA9E] opacity-50 backdrop-blur-[24.96px]"
        style={{ background: "linear-gradient(180deg, #FFF 0%, rgba(255,255,255,0.10) 100%)" }}
      />
      {/* Chữ số cao 95/122.88 = 77.3% chiều cao ô, khớp bản vẽ (text node 59×95
          trong ô 76.8×122.88). Tỉ lệ khung SVG 60:96 giữ đúng dáng chữ. */}
      <SevenSegmentDigit digit={digit} className="relative z-10 h-[77.3%] w-auto text-white" />
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
    /* Khoảng cách 21px ở CẢ HAI chỗ — `1_Days` (`2268:35139`) khai `gap: 21px`
       cho cột (số ↔ nhãn) và `Frame 485` khai `gap: 21px` cho hàng (ô ↔ ô). */
    <div className="flex flex-col items-center gap-[21px]">
      {/* Chữ số vẽ bằng SVG nên KHÔNG có text cho trình đọc màn hình. Bù bằng
          một dòng `sr-only` mang cả giá trị lẫn nhãn ("5 HOURS"), và ẩn phần
          hình khỏi cây trợ năng — nếu không, vùng `aria-live` ở cha sẽ không có
          gì để đọc mỗi khi số đổi. Đọc theo ĐƠN VỊ chứ không theo từng chữ số,
          vì "không, năm" nghe vô nghĩa. */}
      <span className="sr-only">
        {value} {label}
      </span>
      <div aria-hidden="true" className="flex gap-[21px]">
        {digits.map((digit, index) => (
          <DigitBox key={index} digit={digit} />
        ))}
      </div>
      <span
        aria-hidden="true"
        className={`${montserrat.className} text-[clamp(16px,2.38vw,36px)] leading-[1.333] font-bold uppercase tracking-wide text-white`}
      >
        {label}
      </span>
    </div>
  );
}
