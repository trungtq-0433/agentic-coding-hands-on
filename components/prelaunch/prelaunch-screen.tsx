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
    // Khối đếm ngược KHÔNG căn giữa dọc — bản vẽ đặt nó CAO HƠN tâm khung.
    // Đo `2268:35137`→`2268:35143`: khối chiếm y 314→577 trong khung cao 1077,
    // tâm khối 445 so với tâm khung 538 → lệch lên 93px. Căn giữa dọc (bản
    // trước) đẩy tiêu đề xuống y=407 thay vì 314. `pt-[29.16vh]` = 314/1077 nên
    // tỉ lệ giữ nguyên ở mọi chiều cao màn hình.
    <main className="relative flex min-h-screen w-full items-start justify-center overflow-hidden bg-[#00101A] px-6 pt-[29.16vh] pb-16">
      {/* Nền hoạ tiết hữu cơ — ẢNH THẬT từ node `MM_MEDIA_BG Image`
          (`2268:35129`, 1512×1077, đúng bằng khung thiết kế).

          Ghi lại vì đây là một chẩn đoán SAI kéo dài ba lượt: bản trước ghi node
          này "không mang tiền tố MM_MEDIA_ nên không tải được" và thay bằng
          gradient tự chế. Chạy `list_media_nodes(8PJQswPZmU)` thì màn này có
          đúng MỘT media node, tên `MM_MEDIA_BG Image` — CÓ tiền tố, CÓ URL, tải
          bình thường. Bài học: kiểm `list_media_nodes` của CHÍNH màn đang dựng,
          đừng suy từ màn khác.

          Dùng ảnh **1:1**, KHÔNG áp `background-size` mà node khai. Node ghi
          `url(...) -142px -789.753px / 109.392% 216.017%` — đó là phép biến hình
          của ảnh NGUỒN bên trong ô fill của Figma, không phải cách hiển thị ảnh
          mà MoMorph xuất ra. Ảnh MoMorph trả về đã đúng 1512×1077 = bằng khung
          thiết kế, tức đã cắt/scale sẵn. Áp thêm 109%/216% nữa là phóng chồng
          lên một lần nữa, ra hoạ tiết to gấp đôi.

          Kiểm bằng số, không phải bằng mắt: dựng lại ảnh (asset 1:1 + lớp Cover)
          rồi so 8 điểm mẫu với ảnh render của bản vẽ — lệch trung bình 24.6/255,
          so với 67.8 khi dùng asset trần và lệch còn tệ hơn khi áp 109%/216%.

          KHÔNG dùng `-z-10`: `<main>` có `overflow-hidden` + `bg-[#00101A]`, mà
          `position: relative` với `z-index: auto` KHÔNG tạo stacking context —
          nền của `main` sẽ sơn ĐÈ lên con z âm và ảnh biến mất không báo lỗi.
          Đúng lỗi RR-7 đã ghi ở phase-08 (nền keyvisual trang chủ). Cách đúng:
          lớp nền `absolute` không z, nội dung nhận `relative z-10`. */}
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: "url(/prelaunch/prelaunch-bg.webp)" }}
      />
      {/* Lớp phủ `Cover` (`2268:35130`) — gradient CHÉO 18°, không phải một lớp
          đen phẳng. Bản trước đoán `bg-black/40`; đây là giá trị thật của node. */}
      <div
        aria-hidden="true"
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(18deg, #00101A 15.48%, rgba(0, 18, 29, 0.46) 52.13%, rgba(0, 19, 32, 0.00) 63.41%)",
        }}
      />

      {/* `gap-6` (24px) giữa tiêu đề và hàng số: bản vẽ để tiêu đề kết thúc ở
          y=362 và ô số bắt đầu ở y=386. Bản trước dùng `gap-10` (40px). */}
      <div className="relative z-10 flex flex-col items-center gap-6 text-center">
        {/* Tiêu đề `2268:35137`: 36px/48px Montserrat **700** canh giữa — bản
            trước để 28px `font-medium`, sai cả cỡ lẫn độ đậm. */}
        <p
          className={`${montserrat.className} text-[clamp(18px,2.38vw,36px)] leading-[1.333] font-bold text-white`}
        >
          {t("title")}
        </p>
        {/* Khoảng cách giữa ba nhóm là 60px: nhóm Days kết thúc x=608, nhóm
            Hours bắt đầu x=668. Bản trước 24/40/56px. */}
        <div
          className="flex gap-[clamp(16px,3.97vw,60px)]"
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
