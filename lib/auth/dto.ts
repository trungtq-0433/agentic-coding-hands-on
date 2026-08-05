import type { Database } from "@/lib/supabase/database.types";

/**
 * Ranh giới chống rò dữ liệu profile ra client. KHÔNG BAO GIỜ thêm bất kỳ
 * trường định danh xác thực nào (địa chỉ hộp thư, số điện thoại, provider id...)
 * vào đây — TC_WEB_PROFILE_SEC_004 cấm lộ danh tính xác thực trên màn Profile.
 * Cũng KHÔNG thêm `sentKudosCount`: cột đó bị loại khỏi grant công khai ở
 * phase-02 vì suy ra được số kudo ẩn danh đã gửi (xem comment
 * `grant select (...)` ở 0006_views_and_rls.sql).
 */

/** Đúng các cột được grant công khai trên bảng `profiles` (0006_views_and_rls.sql). */
type ProfileRow = Pick<
  Database["public"]["Tables"]["profiles"]["Row"],
  | "id"
  | "full_name"
  | "avatar_url"
  | "department_id"
  | "received_kudos_count"
  | "received_hearts_count"
  | "created_at"
>;

export interface PublicProfile {
  id: string;
  fullName: string;
  avatarUrl: string | null;
  departmentId: number | null;
  receivedKudosCount: number;
  receivedHeartsCount: number;
  createdAt: string;
  /** Số hoa thị suy ra từ received_kudos_count (ngưỡng 10/20/50 → 1/2/3 sao). */
  starCount: number;
}

/** Ngưỡng hoa-thị theo received_kudos_count — khớp Key Insight #7 clarifications.md. */
const STAR_THRESHOLDS: ReadonlyArray<{ min: number; stars: number }> = [
  { min: 50, stars: 3 },
  { min: 20, stars: 2 },
  { min: 10, stars: 1 },
];

function computeStarCount(receivedKudosCount: number): number {
  const matched = STAR_THRESHOLDS.find((tier) => receivedKudosCount >= tier.min);
  return matched?.stars ?? 0;
}

/** Lọc một hàng `profiles` (đã query đúng cột được phép) thành DTO công khai. */
export function toPublicProfile(row: ProfileRow): PublicProfile {
  return {
    id: row.id,
    fullName: row.full_name,
    avatarUrl: row.avatar_url,
    departmentId: row.department_id,
    receivedKudosCount: row.received_kudos_count,
    receivedHeartsCount: row.received_hearts_count,
    createdAt: row.created_at,
    starCount: computeStarCount(row.received_kudos_count),
  };
}
