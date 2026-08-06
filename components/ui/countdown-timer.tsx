"use client";

import { useEffect, useState } from "react";

import { montserrat } from "./fonts";

export interface CountdownTimerLabels {
  days: string;
  hours: string;
  minutes: string;
  seconds?: string;
  /** Hiển thị khi đã qua mốc `targetIso`. */
  finished?: string;
}

export interface CountdownTimerProps {
  targetIso: string;
  /** 1000 (đếm giây, vd Prelaunch gate) hoặc 60000 (đếm phút, vd Homepage). */
  tickMs: number;
  labels: CountdownTimerLabels;
}

export interface RemainingParts {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  finished: boolean;
}

function computeRemaining(targetIso: string): RemainingParts {
  const targetMs = new Date(targetIso).getTime();
  // targetIso đến từ prop bên ngoài (env var qua trang cha) — chuỗi hỏng
  // (NaN) hoặc đã qua mốc đều coi là "đã kết thúc", không throw.
  if (Number.isNaN(targetMs) || targetMs - Date.now() <= 0) {
    return { days: 0, hours: 0, minutes: 0, seconds: 0, finished: true };
  }
  const totalSeconds = Math.floor((targetMs - Date.now()) / 1000);
  return {
    days: Math.floor(totalSeconds / 86400),
    hours: Math.floor((totalSeconds % 86400) / 3600),
    minutes: Math.floor((totalSeconds % 3600) / 60),
    seconds: totalSeconds % 60,
    finished: false,
  };
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

/**
 * Hook tính + tự cập nhật phần thời gian còn lại tới `targetIso`. Tách ra
 * khỏi `CountdownTimer` để dùng lại được cho biến thể giao diện khác của
 * phase-08 (`components/home/countdown-digits.tsx` — 3 ô số kính trên
 * Homepage thay vì text inline như Prelaunch gate). Logic tính + interval
 * giữ nguyên 100%, chỉ đổi nơi gọi setState.
 */
export function useCountdownRemaining(targetIso: string, tickMs: number): RemainingParts {
  const [remaining, setRemaining] = useState<RemainingParts>(() => computeRemaining(targetIso));
  // Theo dõi `targetIso` của lần render trước để phát hiện khi prop đổi và
  // tính lại NGAY TRONG RENDER (không phải setState đồng bộ trong effect —
  // tránh cascading render mà rule `react-hooks/set-state-in-effect` chặn).
  const [prevTargetIso, setPrevTargetIso] = useState(targetIso);
  if (targetIso !== prevTargetIso) {
    setPrevTargetIso(targetIso);
    setRemaining(computeRemaining(targetIso));
  }

  // Effect chỉ còn nhiệm vụ ĐÚNG của nó: đăng ký hẹn giờ với hệ thống bên
  // ngoài (setInterval) và gọi setState từ TRONG callback của hẹn giờ đó khi
  // nó bắn — không gọi setState đồng bộ ngay khi effect chạy.
  useEffect(() => {
    const timer = setInterval(() => {
      setRemaining(computeRemaining(targetIso));
    }, tickMs);
    return () => clearInterval(timer);
  }, [targetIso, tickMs]);

  return remaining;
}

export function CountdownTimer({ targetIso, tickMs, labels }: CountdownTimerProps) {
  const remaining = useCountdownRemaining(targetIso, tickMs);

  if (remaining.finished) {
    return (
      <p className={`${montserrat.className} text-lg font-bold text-white`}>
        {labels.finished ?? "00:00:00:00"}
      </p>
    );
  }

  // tickMs >= 60000 (đếm phút): không hiển thị giây vì số giây sẽ đứng yên
  // suốt cả phút, dễ gây hiểu lầm là timer đã treo.
  const showSeconds = tickMs < 60000;

  return (
    <div
      className={`${montserrat.className} flex items-baseline gap-3 text-white`}
      role="timer"
      aria-live="polite"
    >
      <span>
        <strong className="text-2xl font-bold">{pad(remaining.days)}</strong> {labels.days}
      </span>
      <span>
        <strong className="text-2xl font-bold">{pad(remaining.hours)}</strong> {labels.hours}
      </span>
      <span>
        <strong className="text-2xl font-bold">{pad(remaining.minutes)}</strong> {labels.minutes}
      </span>
      {showSeconds && (
        <span>
          <strong className="text-2xl font-bold">{pad(remaining.seconds)}</strong> {labels.seconds}
        </span>
      )}
    </div>
  );
}
