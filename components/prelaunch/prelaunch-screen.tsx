"use client";

import { useEffect, useRef, useSyncExternalStore } from "react";

import { useCountdownRemaining } from "@/components/ui/countdown-timer";
import { montserrat } from "@/components/ui/fonts";

import { CountdownUnit } from "./countdown-unit";
import { usePrelaunchT } from "./use-prelaunch-text";

/** Không có sự kiện bên ngoài nào để lắng nghe — "mounted" chỉ chuyển
 * false→true đúng một lần rồi đứng yên suốt vòng đời component. */
function noopSubscribe() {
  return () => {};
}

/**
 * Có đang chạy ở client sau khi hydrate xong hay chưa. Dùng
 * `useSyncExternalStore` (không phải `useState` + `useEffect`) vì đây đúng là
 * việc đồng bộ với "hệ thống bên ngoài" (môi trường render server vs client)
 * mà hook đó sinh ra để làm — gọi `setState` ngay trong effect body bị lint
 * rule `react-hooks/set-state-in-effect` của repo chặn (cảnh báo cascading
 * render), còn `useSyncExternalStore` trả thẳng snapshot đúng cho từng môi
 * trường mà không cần setState.
 */
function useHasMounted(): boolean {
  return useSyncExternalStore(
    noopSubscribe,
    () => true, // snapshot phía client
    () => false, // snapshot phía server
  );
}

export interface PrelaunchScreenProps {
  /** ISO datetime của mốc mở cổng sự kiện — Server Component cha đọc từ
   * `NEXT_PUBLIC_LAUNCH_GATE_AT` rồi truyền xuống (không gọi API, xem
   * `app/prelaunch/page.tsx`). Chuỗi rỗng/hỏng được `useCountdownRemaining`
   * coi là "đã qua mốc", không throw. */
  targetIso: string;
  /**
   * Gọi ĐÚNG MỘT LẦN khi đếm ngược về 0. Đồng hồ phía client KHÔNG phải nguồn
   * sự thật để mở khoá điều hướng — việc chặn/redirect thật sự do `proxy.ts`
   * (Track B) quyết định. Callback này chỉ để báo hiệu cho caller (phase-16
   * nối `router.refresh()` để server tự quyết định lại), nên để tuỳ chọn ở
   * đây — trang tự nó không có logic điều hướng nào.
   */
  onReachZero?: () => void;
}

/** Giá trị hiển thị tĩnh dùng cho lần vẽ đầu tiên (trước khi mount xong trên
 * client) — không phụ thuộc đồng hồ, để HTML server và client khớp nhau. */
const STATIC_ZERO = { days: 0, hours: 0, minutes: 0 };

/**
 * Trang chặn toàn màn hình `/prelaunch` (MoMorph `8PJQswPZmU`). Đếm mỗi giây
 * (`tickMs={1000}`), dùng lại `useCountdownRemaining` từ
 * `components/ui/countdown-timer.tsx` (phase-06/08) — không viết bản thứ hai
 * của logic đếm. Không có link/nút điều hướng nào trên trang: đây chỉ là màn
 * hiển thị, logic chặn thật sự nằm ở `proxy.ts`.
 */
export function PrelaunchScreen({ targetIso, onReachZero }: PrelaunchScreenProps) {
  const t = usePrelaunchT();
  const remaining = useCountdownRemaining(targetIso, 1000);

  // `useCountdownRemaining` tính `Date.now()` ngay trong lần render đầu tiên —
  // kể cả trong lần render trên SERVER của Client Component này. Đồng hồ
  // server và đồng hồ client lệch nhau (độ trễ mạng), nên chữ số ban đầu có
  // thể khác nhau giữa hai lần render → hydration mismatch. Chặn bằng cách
  // giữ markup TĨNH (00/00/00, không phụ thuộc đồng hồ) cho tới khi đã mount
  // xong trên client, rồi mới chuyển sang số thật — đúng yêu cầu "đếm ngược
  // khởi động sau khi mount", không phải trong lần render đầu.
  const mounted = useHasMounted();

  // Gọi `onReachZero` đúng một lần khi countdown về 0. `remaining` sinh object
  // mới mỗi tick kể cả sau khi đã finished, nhưng dependency của effect là
  // giá trị boolean nguyên thuỷ `remaining.finished` — effect không chạy lại
  // khi nó vẫn giữ nguyên `true`, nên `firedRef` chỉ cần chặn đúng 1 lần đầu.
  const firedRef = useRef(false);
  useEffect(() => {
    if (mounted && remaining.finished && !firedRef.current) {
      firedRef.current = true;
      onReachZero?.();
    }
  }, [mounted, remaining.finished, onReachZero]);

  const displayed = mounted ? remaining : { ...STATIC_ZERO, finished: false, seconds: 0 };

  return (
    <main className="relative flex min-h-screen w-full items-center justify-center overflow-hidden bg-[#00101A] px-6 py-16">
      {/*
        Nền hoạ tiết hữu cơ (spec: "Nền tối với họa tiết hữu cơ nhiều màu sắc").
        Node Figma "Background Image" (2268:35129) KHÔNG mang tiền tố
        `MM_MEDIA_` nên không có URL tải qua pipeline asset (đúng bẫy đã gặp ở
        phase-07/09 — chỉ node `MM_MEDIA_*` mới tải được). Dùng gradient mã hoá
        thay thế bằng đúng bảng màu thương hiệu đã dùng ở các màn khác
        (`#00101A` nền, `#FFEA9E`/`#998C5F` điểm nhấn), KHÔNG bịa ảnh thay thế.
        Cần designer đổi tên node đúng tiền lệ để lấy ảnh thật.
      */}
      <div
        aria-hidden="true"
        className="absolute inset-0 -z-10"
        style={{
          background:
            "radial-gradient(circle at 18% 22%, rgba(255,234,158,0.16) 0%, rgba(255,234,158,0) 45%), " +
            "radial-gradient(circle at 82% 78%, rgba(153,140,95,0.22) 0%, rgba(153,140,95,0) 50%), " +
            "linear-gradient(160deg, #10222E 0%, #00101A 60%, #00070C 100%)",
        }}
      />
      {/* Lớp phủ bán trong suốt màu tối tăng độ tương phản cho văn bản (spec). */}
      <div aria-hidden="true" className="absolute inset-0 -z-10 bg-black/40" />

      <div className="flex flex-col items-center gap-10 text-center">
        <p className={`${montserrat.className} text-[clamp(18px,3vw,28px)] font-medium text-white`}>
          {t("title")}
        </p>
        <div
          className="flex gap-6 sm:gap-10 md:gap-14"
          role="timer"
          aria-live="polite"
          aria-label={t("countdownAria")}
        >
          <CountdownUnit value={displayed.days} label={t("days")} />
          <CountdownUnit value={displayed.hours} label={t("hours")} />
          <CountdownUnit value={displayed.minutes} label={t("minutes")} />
        </div>
      </div>
    </main>
  );
}
