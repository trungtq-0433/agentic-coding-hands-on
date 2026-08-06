/**
 * Hoa-thị là hàm THUẦN, không phải query (Key Insight #8) — tính trực tiếp từ
 * `profiles.received_kudos_count` đã có sẵn, ngưỡng 10/20/50 → 1/2/3 sao.
 *
 * LƯU Ý TRÙNG LẶP (đã kiểm theo yêu cầu bàn giao): `lib/auth/dto.ts` có một bản
 * private `computeStarCount` với cùng ngưỡng, dùng cho `toPublicProfile()`.
 * KHÔNG gộp về một chỗ ở đây vì `lib/auth/**` nằm ngoài phạm vi sở hữu của
 * phase-04 (không được sửa — xem ràng buộc trong task). Đã báo lại ở báo cáo
 * bàn giao cuối phase-04 để phase sau (17 hoặc dọn dẹp riêng) import
 * `computeStarCount` từ đây thay vì giữ 2 bản.
 */
export const STAR_THRESHOLDS: ReadonlyArray<{ readonly min: number; readonly stars: number }> = [
  { min: 50, stars: 3 },
  { min: 20, stars: 2 },
  { min: 10, stars: 1 },
];

export function computeStarCount(receivedKudosCount: number): number {
  const matched = STAR_THRESHOLDS.find((tier) => receivedKudosCount >= tier.min);
  return matched?.stars ?? 0;
}
