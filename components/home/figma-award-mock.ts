import type { AwardCardData } from "./award-card";

/**
 * Dữ liệu 6 hạng mục giải — **MOCK TẠM, lấy nguyên văn từ Figma**.
 *
 * Phase-08 KHÔNG sở hữu nội dung này: `clarifications.md` gap #10 chốt 6 hạng
 * mục là nội dung tĩnh trong repo và **phase-12 (`/awards`) mới là chủ sở hữu**.
 * File này tồn tại để trang chủ render được ngay mà không phải chờ phase-12, và
 * để phase-16 (integration) biết chính xác chỗ cần thay: xoá file này, trỏ
 * `HomePageClient` sang nguồn thật của phase-12. Không nơi nào khác đọc nó.
 *
 * Ảnh chữ tên giải tải từ node `MM_MEDIA_*` của màn Homepage; kích thước dưới
 * đây là số đo thật của file trong `public/home/`, không phải số làm tròn của
 * Figma (Figma báo 221.45×35.04 cho Top Talent, file thật 222×36).
 */

/**
 * `slug` được **ghim cứng**, KHÔNG sinh từ `title` lúc chạy.
 *
 * `clarifications.md` gap #16 chốt `slug = kebab-case(title)`, nhưng `title`
 * là chuỗi ĐÃ DỊCH — sinh slug từ nó thì link `/awards#top-talent` (VI) sẽ
 * thành `/awards#award-system`-kiểu khác khi đổi sang EN, và mọi anchor người
 * dùng đã lưu sẽ gãy khi họ đổi ngôn ngữ. Slug là định danh, không phải nội
 * dung hiển thị. Giá trị dưới đây chính là kebab-case của tiêu đề tiếng Việt
 * gốc trong Figma — đúng luật gap #16, chỉ là tính một lần tại đây thay vì
 * mỗi lần render.
 */
interface AwardMockSpec {
  slug: string;
  /** Tiền tố key i18n trong namespace `home` — `<prefix>.title` + `<prefix>.desc`. */
  i18nPrefix: string;
  nameImageSrc: string;
  nameImageWidth: number;
  nameImageHeight: number;
}

const AWARD_SPECS: readonly AwardMockSpec[] = [
  {
    slug: "top-talent",
    i18nPrefix: "awards.topTalent",
    nameImageSrc: "/home/award-top-talent.png",
    nameImageWidth: 222,
    nameImageHeight: 36,
  },
  {
    slug: "top-project",
    i18nPrefix: "awards.topProject",
    nameImageSrc: "/home/award-top-project.png",
    nameImageWidth: 232,
    nameImageHeight: 35,
  },
  {
    slug: "top-project-leader",
    i18nPrefix: "awards.topProjectLeader",
    nameImageSrc: "/home/award-top-project-leader.png",
    nameImageWidth: 232,
    nameImageHeight: 64,
  },
  {
    slug: "best-manager",
    i18nPrefix: "awards.bestManager",
    nameImageSrc: "/home/award-best-manager.png",
    nameImageWidth: 232,
    nameImageHeight: 30,
  },
  {
    slug: "signature-2025-creator",
    i18nPrefix: "awards.signatureCreator",
    nameImageSrc: "/home/award-signature-creator.png",
    nameImageWidth: 232,
    nameImageHeight: 54,
  },
  {
    slug: "mvp",
    i18nPrefix: "awards.mvp",
    nameImageSrc: "/home/award-mvp.png",
    nameImageWidth: 116,
    nameImageHeight: 52,
  },
];

/**
 * Dựng danh sách thẻ giải đã dịch. Nhận `t` thay vì tự gọi hook để module này
 * ở lại tầng dữ liệu thuần (gọi được từ bất kỳ đâu, test được không cần render).
 *
 * **FIXME (thiết kế, không phải code):** 3 thẻ cuối — Best Manager,
 * Signature 2025 - Creator, MVP — dùng CHUNG một câu mô tả "Vinh danh người
 * quản lý có năng lực quản lý tốt, dẫn dắt đội nhóm" trong Figma, và mô tả của
 * Top Project Leader kết thúc bằng dấu phẩy cụt. Đây gần như chắc chắn là
 * copy-paste sót của bản thiết kế (màn này còn `in_progress`, xem
 * `clarifications.md`). Chép nguyên văn theo quyết định "code theo bản hiện
 * tại"; cần người soạn spec cấp mô tả thật cho 3 hạng mục đó.
 */
export function buildFigmaAwardMock(t: (key: string) => string): AwardCardData[] {
  return AWARD_SPECS.map((spec) => ({
    slug: spec.slug,
    title: t(`${spec.i18nPrefix}.title`),
    description: t(`${spec.i18nPrefix}.desc`),
    nameImageSrc: spec.nameImageSrc,
    nameImageWidth: spec.nameImageWidth,
    nameImageHeight: spec.nameImageHeight,
  }));
}
