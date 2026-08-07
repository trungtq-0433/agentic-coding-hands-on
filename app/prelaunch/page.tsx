import { PrelaunchScreen } from "@/components/prelaunch/prelaunch-screen";

/**
 * Trang chặn toàn màn hình `/prelaunch` (MoMorph `8PJQswPZmU`) — CHỈ hiển thị.
 * Logic chặn/redirect thật sự (ai vào được, ai bị đẩy về đây) là việc của
 * `proxy.ts` (Track B, phase-01/16) — trang này không có link, không có
 * header nav, không có nút điều hướng nào.
 *
 * `NEXT_PUBLIC_LAUNCH_GATE_AT` bị **inline vào bundle lúc `next build`**,
 * không đọc lại được lúc chạy — đổi mốc thời gian bắt buộc build lại, restart
 * process là không đủ
 * (`node_modules/next/dist/docs/01-app/02-guides/environment-variables.md`).
 * Vì vậy phải viết `process.env.NEXT_PUBLIC_LAUNCH_GATE_AT` NGUYÊN DẠNG, không
 * qua biến trung gian hay truy cập động `process.env[key]` — bundler chỉ thay
 * thế được khi thấy đúng mẫu chuỗi đó (xem `app/page.tsx`, đã làm đúng).
 *
 * Thiếu biến → chuỗi rỗng; `PrelaunchScreen` (qua `useCountdownRemaining`) coi
 * giá trị không parse được là "đã qua mốc", hiện `00` thay vì làm vỡ trang.
 */
export default function PrelaunchPage() {
  const targetIso = process.env.NEXT_PUBLIC_LAUNCH_GATE_AT ?? "";

  return <PrelaunchScreen targetIso={targetIso} />;
}
