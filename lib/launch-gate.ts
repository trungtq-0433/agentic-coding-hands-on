/**
 * Launch gate — cổng chặn toàn site trước giờ mở màn.
 *
 * Mốc thời gian đến từ NEXT_PUBLIC_LAUNCH_GATE_AT (ISO-8601 có offset, vd
 * "2025-11-20T09:00:00+07:00"). Biến NEXT_PUBLIC_* bị inline vào bundle lúc
 * `next build` — đổi giá trị BẮT BUỘC build lại, restart process không đủ.
 * Xem runbook ở docs/runbook-su-kien.md.
 */

/** Đường dẫn của màn prelaunch. Dùng chung giữa proxy và page để khỏi lệch. */
export const PRELAUNCH_PATH = "/prelaunch";

/**
 * Đọc mốc launch gate từ env. Trả null khi thiếu hoặc không parse được —
 * chỗ gọi tự quyết định fail-open.
 */
export function getLaunchGateAt(): Date | null {
  const raw = process.env.NEXT_PUBLIC_LAUNCH_GATE_AT;
  if (!raw) return null;

  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) {
    console.warn(
      `[launch-gate] NEXT_PUBLIC_LAUNCH_GATE_AT không parse được: "${raw}" — bỏ qua cổng chặn.`,
    );
    return null;
  }
  return parsed;
}

/**
 * Còn trước giờ mở màn hay không.
 *
 * FAIL-OPEN có chủ đích: env thiếu hoặc sai định dạng → trả false (không chặn).
 * Khoá nhầm cả site vì một biến gõ sai là hỏng nặng hơn nhiều so với mở sớm.
 */
export function isBeforeLaunchGate(now: Date = new Date()): boolean {
  const gateAt = getLaunchGateAt();
  if (gateAt === null) return false;
  return now.getTime() < gateAt.getTime();
}
