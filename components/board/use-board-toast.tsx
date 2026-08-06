"use client";

import { useCallback, useState, type ReactNode } from "react";

import { montserrat } from "@/components/ui/fonts";

/** Thời gian một thông báo nằm trên màn hình (ms). */
const TOAST_MS = 3000;

export interface UseBoardToastResult {
  /** Đặt vào cuối cây trang; `null` khi không có gì để báo. */
  toastNode: ReactNode;
  showToast: (message: string) => void;
}

/**
 * Toast một dòng cho màn Live board — "Link copied…" và lỗi thả tim.
 *
 * `role="status"` + `aria-live="polite"` chứ không `role="alert"`: đây là xác
 * nhận một hành động người dùng vừa chủ động làm, không phải cảnh báo cắt ngang.
 * `alert` sẽ ngắt lời trình đọc màn hình giữa chừng.
 *
 * Bấm liên tiếp thì hẹn giờ cũ bị huỷ chứ không xếp chồng — nếu không, thông
 * báo thứ hai sẽ biến mất sớm theo hẹn giờ của thông báo thứ nhất.
 */
export function useBoardToast(): UseBoardToastResult {
  const [message, setMessage] = useState<string | null>(null);
  const [timer, setTimer] = useState<number | null>(null);

  const showToast = useCallback(
    (next: string) => {
      if (timer !== null) window.clearTimeout(timer);
      setMessage(next);
      setTimer(window.setTimeout(() => setMessage(null), TOAST_MS));
    },
    [timer],
  );

  const toastNode = message ? (
    <div
      role="status"
      aria-live="polite"
      className={`${montserrat.className} fixed bottom-8 left-1/2 z-50 -translate-x-1/2 rounded-lg bg-[#FFEA9E] px-6 py-3 text-base font-bold text-[#00101A]`}
      style={{ boxShadow: "0 4px 4px 0 rgba(0, 0, 0, 0.25), 0 0 6px 0 #FAE287" }}
    >
      {message}
    </div>
  ) : null;

  return { toastNode, showToast };
}
