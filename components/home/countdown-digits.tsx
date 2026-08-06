"use client";

import { Share_Tech_Mono } from "next/font/google";

import { useCountdownRemaining } from "@/components/ui/countdown-timer";
import { montserrat } from "@/components/ui/fonts";

import { useHomeT } from "./use-home-text";

/**
 * Font chữ số countdown của Homepage.
 * Figma khai `"Digital Numbers"` (font LCD 7 đoạn) cho ô số (node
 * `2167:9035`), nhưng font này KHÔNG có trên Google Fonts và KHÔNG có sẵn
 * trong hệ thống (`fc-list` chỉ trả `KacstDigital` — font tiếng Ả Rập, không
 * dùng được). Đây là THAY THẾ CÓ CHỦ ĐÍCH: `Share_Tech_Mono` là font
 * monospace, giữ đúng tiêu chí quan trọng nhất — chữ số không nhảy ngang khi
 * đếm — dù glyph không giống LCD 7 đoạn của bản gốc. Cần designer cấp file
 * font `Digital Numbers` (kèm license) để thay đúng chỗ này khi có.
 */
const shareTechMono = Share_Tech_Mono({
  subsets: ["latin"],
  weight: "400",
  display: "swap",
});

export interface CountdownDigitsProps {
  targetIso: string;
}

interface CountdownUnit {
  key: string;
  value: number;
  label: string;
}

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

/** Một ô số kính đơn (1 chữ số). Nền mờ tách lớp riêng khỏi chữ số — Figma
 * áp `opacity .5` cho NỀN, không áp cho chữ, nên không thể gộp chung 1 div. */
function DigitBox({ digit }: { digit: string }) {
  return (
    <div className="relative flex h-[clamp(58px,14vw,81.92px)] w-[clamp(36px,9vw,51.2px)] shrink-0 items-center justify-center">
      <div
        aria-hidden="true"
        className="absolute inset-0 rounded-lg border-[0.5px] border-[#FFEA9E] opacity-50 backdrop-blur-[16.64px]"
        style={{ background: "linear-gradient(180deg, #FFF 0%, rgba(255,255,255,0.10) 100%)" }}
      />
      <span
        className={`${shareTechMono.className} relative z-10 text-[clamp(28px,7vw,49.152px)] font-normal tabular-nums text-white`}
      >
        {digit}
      </span>
    </div>
  );
}

/** Một đơn vị đếm (Days/Hours/Minutes): 2 ô số + nhãn dưới. */
function CountdownUnitBlock({ value, label }: { value: number; label: string }) {
  const digits = pad2(value).split("");
  return (
    <div className="flex flex-col items-center gap-2 sm:gap-3.5">
      <div className="flex gap-2 sm:gap-3.5">
        {digits.map((digit, index) => (
          <DigitBox key={index} digit={digit} />
        ))}
      </div>
      <span
        className={`${montserrat.className} text-[clamp(16px,4vw,24px)] font-bold leading-[1.33] text-white`}
      >
        {label}
      </span>
    </div>
  );
}

/**
 * Biến thể countdown ô số của Homepage (Figma `mms_B1_Countdown time`, node
 * `2167:9035`). Dùng lại logic đếm từ `useCountdownRemaining` (phase-06,
 * `components/ui/countdown-timer.tsx`) — chỉ khác giao diện: 3 ô số kính
 * thay vì text inline, và đếm theo PHÚT (60000ms) chứ không phải giây như
 * Prelaunch gate.
 */
export function CountdownDigits({ targetIso }: CountdownDigitsProps) {
  const t = useHomeT();
  const remaining = useCountdownRemaining(targetIso, 60000);

  const units: CountdownUnit[] = [
    { key: "days", value: remaining.days, label: t("hero.days") },
    { key: "hours", value: remaining.hours, label: t("hero.hours") },
    { key: "minutes", value: remaining.minutes, label: t("hero.minutes") },
  ];

  // Chuỗi đọc gộp cho screen reader — tránh đọc rời từng chữ số của mỗi ô.
  const srText = units.map((unit) => `${pad2(unit.value)} ${unit.label}`).join(", ");

  return (
    <div
      className="flex flex-col gap-4"
      role="timer"
      aria-live="polite"
      aria-label={t("hero.countdownAria")}
    >
      {!remaining.finished && (
        <p
          className={`${montserrat.className} text-[clamp(16px,4vw,24px)] font-bold leading-[1.33] text-white`}
        >
          {t("hero.comingSoon")}
        </p>
      )}
      <div className="flex gap-4 sm:gap-8 md:gap-10" aria-hidden="true">
        {units.map((unit) => (
          <CountdownUnitBlock key={unit.key} value={unit.value} label={unit.label} />
        ))}
      </div>
      <span className="sr-only">{srText}</span>
    </div>
  );
}
