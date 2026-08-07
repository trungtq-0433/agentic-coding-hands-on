import type { KudoCardData, KudoParticipant } from "@/components/board/kudo-card-types";
import type { ProfileSummary } from "./profile-types";

/**
 * Dữ liệu mock cho màn Profile — dùng tạm cho tới phase-16 (Track B nối
 * `public_kudos_feed`/`my_sent_kudos`/`profiles` thật).
 *
 * **Vì sao ID khớp `supabase/seed.sql` chứ không phải id bịa:** Track A không được
 * query DB thật (tầng truy cập Supabase bị cấm import trong `components/profile/**`), nhưng "profile
 * người khác" vẫn cần MỘT nguồn id ổn định để `TC_WEB_PROFILE_FUN_001` (id khớp Sunner
 * có thật) và `TC_WEB_PROFILE_FUN_003` (id lạ → 404) phân biệt được. Lấy đúng id/tên/
 * phòng ban từ 8 profile demo trong `seed.sql` — khi phase-16 query thật, ID này sẽ
 * TRÙNG với hàng thật trong DB local, không phải đổi gì thêm ở phía mock.
 *
 * Avatar dùng `/board/avatar-b.png` (asset đã tải thật từ Figma ở phase-09), KHÔNG
 * dùng URL `dicebear.com` trong `seed.sql` — domain đó không có trong
 * `images.remotePatterns` (`next.config.ts`, ngoài ownership phase này) nên
 * `next/image` sẽ throw.
 */
const MOCK_OTHER_PROFILES: Record<string, ProfileSummary> = {
  // Trần Thị Bình — seed.sql dòng 145, phòng "CEVC1 - DSV".
  "a0000000-0000-0000-0000-000000000002": {
    id: "a0000000-0000-0000-0000-000000000002",
    fullName: "Trần Thị Bình",
    avatarUrl: "/board/avatar-b.png",
    departmentName: "CEVC1 - DSV",
    starCount: 2,
    receivedKudosCount: 22,
  },
  // Đặng Minh Tuấn — KHÔNG có trong seed.sql, id đặt tay theo đúng khuôn UUID để
  // minh hoạ TC_WEB_PROFILE_GUI_009 (roster profile chưa từng đăng nhập: không
  // avatar, không phòng ban, 0 kudos). Ghi rõ để không ai tưởng nhầm đây là hàng
  // seed thật.
  "00000000-0000-4000-8000-000000000000": {
    id: "00000000-0000-4000-8000-000000000000",
    fullName: "Đặng Minh Tuấn",
    avatarUrl: null,
    departmentName: null,
    starCount: 0,
    receivedKudosCount: 0,
  },
};

/** Tra profile mock theo id đã chuẩn hoá chữ thường. `undefined` = không tồn tại (404). */
export function findMockOtherProfile(id: string): ProfileSummary | undefined {
  return MOCK_OTHER_PROFILES[id];
}

/** Hai avatar mẫu khác đã tải từ Figma phase-09, xoay vòng cho người gửi/nhận phụ trong feed mock. */
const SENDER_AVATARS = ["/board/avatar-a.png", "/board/avatar-c.png"] as const;
const SENDER_NAMES = ["Đỗ hoàng Hiệp", "Dương thúy An", "Mai phương Thúy", "Lê Kiều Trang"] as const;

function mockParticipant(index: number): KudoParticipant {
  return {
    id: `mock-sunner-${index}`,
    name: SENDER_NAMES[index % SENDER_NAMES.length],
    avatarUrl: SENDER_AVATARS[index % SENDER_AVATARS.length],
    starCount: (index % 3) + 1,
  };
}

/** Người gửi ẩn danh — nhãn cố định (gap #4), không có tên tự nhập. */
const ANONYMOUS: KudoParticipant = { id: null, name: null, avatarUrl: null, starCount: 0 };

function toParticipant(profile: ProfileSummary): KudoParticipant {
  return {
    id: profile.id,
    name: profile.fullName,
    avatarUrl: profile.avatarUrl,
    starCount: profile.starCount,
  };
}

/** Mốc thời gian cố định — `Date.now()` sẽ vỡ hydration (server/client render lệch nhau). */
const BASE_ISO = "2025-10-30T09:00:00+07:00";
function isoMinus(hours: number): string {
  return new Date(new Date(BASE_ISO).getTime() - hours * 3_600_000).toISOString();
}

/**
 * Feed "Đã nhận" của một profile bất kỳ (chính mình hoặc người khác) — recipient
 * CỐ ĐỊNH là `profile`, sender xoay vòng, cứ 4 thẻ có 1 thẻ ẩn danh (khớp tỉ lệ
 * mock của board) để trạng thái ẩn danh luôn kiểm được (TC_WEB_PROFILE_GUI_006).
 */
export function buildMockReceivedFeed(profile: ProfileSummary, total: number): KudoCardData[] {
  const recipient = toParticipant(profile);
  return Array.from({ length: total }, (_, i) => ({
    id: 1000 + i,
    sender: i % 4 === 3 ? ANONYMOUS : mockParticipant(i),
    recipient,
    createdAtIso: isoMinus(i * 5),
    title: i % 2 === 0 ? "IDOL GIỚI TRẺ" : null,
    body:
      "Cảm ơn bạn đã luôn sẵn sàng hỗ trợ cả nhóm những lúc gấp gáp nhất, " +
      "và vẫn giữ được tinh thần tích cực khiến mọi người xung quanh cùng vững tâm.",
    images: [],
    hashtags: ["Dedicated"],
    heartCount: 50 - i * 3,
    hearted: i % 5 === 0,
  }));
}

/**
 * Feed "Đã gửi" — CHỈ dùng cho chính mình (TC_WEB_PROFILE_SEC_001 cấm hiện mục
 * này ở profile người khác). Sender cố định là `profile`.
 *
 * **TC_WEB_PROFILE_SEC_002** đòi cả kudo ẩn danh chính mình gửi cũng phải hiện
 * TÊN THẬT (không mask), vì đây là danh sách của chính chủ. `kudo-card-types.ts`
 * hiện KHÔNG có cờ "đã gửi ẩn danh nhưng đang xem bởi chính chủ" tách khỏi
 * `sender.id === null` — tái dùng `KudoCard` nguyên vẹn (TC_WEB_PROFILE_GUI_006)
 * nghĩa là card không thể tự vẽ thêm nhãn "(ẩn danh)" cho trường hợp riêng này.
 * MVP chọn hiện tên thật (đúng nửa đầu yêu cầu — "shown as author"), phần đánh
 * dấu "đã gửi ẩn danh" cần một cờ dữ liệu mới trong `KudoCardData` hoặc một prop
 * mới trên `KudoCard` — cả hai đều ngoài phạm vi Track A phase này, để lại cho
 * phase-16/PO quyết định hình dạng.
 */
export function buildMockSentFeed(profile: ProfileSummary, total: number): KudoCardData[] {
  const sender = toParticipant(profile);
  return Array.from({ length: total }, (_, i) => ({
    id: 2000 + i,
    sender,
    recipient: mockParticipant(i + 1),
    createdAtIso: isoMinus(i * 7),
    title: null,
    body: "Cảm ơn bạn đã đồng hành cùng dự án, mong sẽ tiếp tục hợp tác trong các mùa Kudos sau.",
    images: [],
    hashtags: [],
    heartCount: 12 - i,
    hearted: false,
  }));
}
