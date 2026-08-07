import type { HashtagItem } from "@/components/ui/multi-hashtag-picker";

/**
 * Kiểu dữ liệu cho modal Viết Kudo — tách khỏi component để phase-16 (nối dữ
 * liệu thật) import type mà không kéo theo runtime UI, cùng khuôn mẫu
 * `kudo-card-types.ts` của phase-09.
 *
 * Track A: KHÔNG import `lib/data|actions|supabase|realtime`. Mọi dữ liệu vào
 * qua props (`searchSunners`, `hashtags`, `presetRecipient`) hoặc do người
 * dùng tạo ra ngay trong modal (ảnh chọn từ máy, nội dung soạn).
 */

/** Một Sunner tối thiểu đủ để hiển thị ở ô người nhận / gợi ý mention. */
export interface Profile {
  id: string;
  name: string;
  avatarUrl: string | null;
}

/**
 * Dữ liệu gửi lên khi bấm "Gửi". `body` là text thuần — @mention sống ngay
 * trong chuỗi này (bảng `kudos_mentions` đã bỏ khỏi MVP, xem clarifications
 * §"Session 2026-08-05 (bổ sung sau Red Team Review)" #15). KHÔNG có
 * `mentionIds`. `images` là file gốc người dùng chọn — việc tải lên Storage
 * thật thuộc phase-16, modal chỉ giữ `File[]` trong bộ nhớ.
 */
export interface ComposeKudoDraft {
  recipientId: string;
  body: string;
  hashtagIds: string[];
  images: File[];
  isAnonymous: boolean;
}

/**
 * Lỗi theo từng trường — server (phase-16, qua prop `errors`) và validate nội
 * bộ (bắt buộc rỗng) đều dùng chung hình dạng này để modal chỉ có MỘT chỗ
 * hiển thị lỗi cho mỗi trường.
 */
export interface ComposeKudoFieldErrors {
  recipientId?: string;
  body?: string;
  hashtagIds?: string;
  images?: string;
}

export interface ComposeKudoSubmitResult {
  ok: boolean;
  fieldErrors?: ComposeKudoFieldErrors;
}

export interface ComposeKudoModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (draft: ComposeKudoDraft) => Promise<ComposeKudoSubmitResult>;
  /** Autocomplete người nhận / gợi ý mention — tối thiểu 1 ký tự mới gọi (spec mms_B.2). */
  searchSunners: (query: string) => Promise<Profile[]>;
  hashtags: HashtagItem[];
  /** Pre-fill khi mở từ trang Profile người khác (TC_WEB_PROFILE_FUN_007). Mặc định `null`. */
  presetRecipient?: Profile | null;
  submitting: boolean;
  errors: ComposeKudoFieldErrors;
}
