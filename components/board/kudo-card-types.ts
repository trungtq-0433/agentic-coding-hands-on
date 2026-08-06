/**
 * Kiểu dữ liệu của thẻ Kudo — tách riêng khỏi `kudo-card.tsx` vì **phase-11
 * (Profile) dùng lại thẻ này nguyên vẹn** (TC_WEB_PROFILE_GUI_006), và cả
 * phase-16 khi nối dữ liệu thật cũng phải import kiểu mà không kéo theo cả
 * component. File này KHÔNG có `"use client"` — thuần kiểu, không runtime.
 *
 * Track A: mọi giá trị đến từ props. Không import `lib/data|actions|supabase`.
 */

/**
 * Hạng Hero hiển thị cạnh tên người dùng.
 *
 * **Vì sao là prop chứ không tự tính:** `clarifications.md` gap #7 chốt bỏ Hero
 * tier khỏi MVP vì "thiếu tên tier + ngưỡng". Màn Live board cho biết 4 TÊN
 * (`New Hero` / `Rising Hero` / `Super Hero` / `Legend Hero`) nhưng **vẫn không
 * cho biết NGƯỠNG**. Nên UI dựng đủ chỗ để hiển thị huy hiệu (khớp bản vẽ),
 * còn luật suy ra hạng thì để nguyên chỗ trống — phase-16/PO chốt sau. Không
 * bịa ngưỡng.
 *
 * `new` chưa có ảnh: node `MM_MEDIA_New Hero` không có URL trong
 * `get_media_files` và `get_figma_image` trả 500 (cùng lỗi endpoint đã gặp ở
 * phase-07). Gặp `new` thì không render huy hiệu, các hạng khác render bình thường.
 */
export type HeroTier = "new" | "rising" | "super" | "legend";

/** Một người trong thẻ (người gửi hoặc người nhận). */
export interface KudoParticipant {
  /** `null` khi là kudo ẩn danh — UI hiện NHÃN CỐ ĐỊNH, không có tên tự nhập (gap #4). */
  id: string | null;
  /** `null` = ẩn danh. Nhãn hiển thị lấy từ i18n, không phải từ đây. */
  name: string | null;
  avatarUrl: string | null;
  /** Số hoa thị: ngưỡng 10/20/50 tổng kudos nhận được → 1/2/3 sao. */
  starCount: number;
  heroTier?: HeroTier;
}

export interface KudoImage {
  url: string;
  /** Chiều rộng/cao thật để `next/image` không phải đoán; thiếu thì dùng ô 88×88. */
  width?: number;
  height?: number;
}

export interface KudoCardData {
  id: number;
  sender: KudoParticipant;
  recipient: KudoParticipant;
  /** ISO datetime — thẻ tự định dạng theo locale, KHÔNG nhận chuỗi đã format sẵn. */
  createdAtIso: string;
  /** Danh hiệu trao tặng, vd "IDOL GIỚI TRẺ". `null` thì ẩn cả dòng. */
  title: string | null;
  body: string;
  images: KudoImage[];
  hashtags: string[];
  heartCount: number;
  /** Người đang xem đã thả tim thẻ này chưa. */
  hearted: boolean;
}

/** Kết quả thả tim. Track B trả về; UI lấy CON SỐ TỪ ĐÂY, không tự cộng trừ. */
export interface ToggleHeartResult {
  ok: boolean;
  hearted?: boolean;
  heartCount?: number;
  /** Mã lỗi để trang cha dịch sang thông báo; `ok:false` thì giữ nguyên trạng thái cũ. */
  code?: string;
}
