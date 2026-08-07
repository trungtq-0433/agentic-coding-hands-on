/**
 * Kiểu dữ liệu riêng của màn Profile — tách khỏi component để `app/profile/page.tsx`
 * (Server Component, được phép import `lib/auth/dal`) và các Client Component trong
 * `components/profile/**` (KHÔNG được phép) đều import được cùng một kiểu.
 *
 * Track A: file này KHÔNG có `"use client"` — thuần kiểu, không runtime, không import
 * tầng truy cập Supabase/data/actions/realtime.
 */

/** Thông tin hiển thị ở khối hero — của CHÍNH NGƯỜI ĐANG XEM hoặc của Sunner khác. */
export interface ProfileSummary {
  id: string;
  fullName: string;
  avatarUrl: string | null;
  /** Tên phòng ban đã resolve sẵn (không phải id) — `null` = chưa phân loại/chưa có. */
  departmentName: string | null;
  /** Số hoa thị suy ra từ tổng kudos nhận được (ngưỡng 10/20/50 → 1/2/3 sao). 0 = không hiện dòng sao. */
  starCount: number;
  /**
   * Tổng kudos ĐÃ NHẬN — cột `received_kudos_count` được grant công khai cho MỌI
   * profile (khác `sentKudosCount`, chỉ chính chủ mới thấy được, xem
   * `ProfileStats`). Dropdown hướng nhận/gửi cần số này ngay cả khi xem profile
   * người khác (`stats === null`), nên nó sống ở đây chứ không phải `ProfileStats`.
   */
  receivedKudosCount: number;
}

/**
 * 5 chỉ số của thẻ thống kê (mms_B_Thống kê). Chỉ tồn tại khi xem CHÍNH MÌNH —
 * `null` ở mọi profile khác là tín hiệu DUY NHẤT quyết định self/other
 * (TC_WEB_PROFILE_FUN_006/007, xem `profile-page.tsx`).
 */
export interface ProfileStats {
  receivedKudos: number;
  /** Tổng kudos đã gửi, TÍNH CẢ ẩn danh — không public khi xem profile người khác (TC_WEB_PROFILE_SEC_001). */
  sentKudos: number;
  hearts: number;
  /** Luôn 0 ở MVP — quy tắc cấp Secret Box chưa chốt (clarifications gap #9). */
  openedBoxes: number;
  /** Luôn 0 ở MVP — cùng lý do trên. */
  unopenedBoxes: number;
}

/** Chiều hiển thị của khối KUDOS. `"sent"` chỉ hợp lệ khi đang xem chính mình. */
export type ProfileDirection = "received" | "sent";
