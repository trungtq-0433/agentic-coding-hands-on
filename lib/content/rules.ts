/**
 * Nội dung panel "Thể lệ" — **hằng số tĩnh**, cùng lý do với `figma-award-mock.ts`
 * (phase-08): clarifications.md gap #10 chốt nội dung dạng này không có màn admin
 * quản lý, và phase-13 (đây) là chủ sở hữu duy nhất của khối nội dung này.
 *
 * Toàn bộ chuỗi tiếng Việt lấy VERBATIM từ node Figma `3204:6053` (frame
 * "Thể lệ UPDATE", fileKey `9ypp4enmFmdK3YAFJLIu6C`, screenId `b1Filzi9i6`) qua
 * MCP momorph — KHÔNG bịa. Một vài đoạn mô tả trong Figma có `\n` thừa ở cuối
 * chuỗi (dấu vết auto-layout "hug" của Figma, không mang nghĩa) — đã cắt bỏ khi
 * chép vào đây vì đó là khoảng trắng thừa, không phải nội dung.
 *
 * `t` được truyền vào thay vì tự gọi hook, để module này ở tầng dữ liệu thuần
 * (gọi được từ bất kỳ đâu, kể cả test không cần render) — cùng khuôn với
 * `buildFigmaAwardMock` của phase-08.
 */

/** Một hạng Hero — ngưỡng SỐ NGƯỜI GỬI Kudos cho bạn (không phải tổng Kudos nhận). */
export interface HeroTierContent {
  key: "new" | "rising" | "super" | "legend";
  /** Ảnh pill tên hạng — TÁI DÙNG asset đã tải ở `public/board/` (phase-09), không
   * tải lại bản sao thứ hai của cùng một ảnh thương hiệu. */
  badgeSrc: string | null;
  badgeWidth: number;
  badgeHeight: number;
  label: string;
  range: string;
  description: string;
}

/** Một trong 6 huy hiệu Secret Box — `code` khớp `badges.code` seed phase-02. */
export interface SecretBoxBadgeContent {
  code: string;
  name: string;
  iconSrc: string | null;
  iconWidth: number;
  iconHeight: number;
}

export interface RulesContent {
  title: string;
  closeLabel: string;
  composeLabel: string;
  heroSection: {
    heading: string;
    description: string;
    tiers: HeroTierContent[];
  };
  secretBoxSection: {
    heading: string;
    description: string;
    badges: SecretBoxBadgeContent[];
    closingText: string;
    nationalHeading: string;
    nationalDescription: string;
  };
}

/**
 * Thứ tự 6 huy hiệu trong 2 hàng của Figma (`Frame 511`/`Frame 513`) suy ra từ
 * thứ tự nodeId liên tiếp trong mỗi frame (Figma luôn sinh id tăng dần theo thứ
 * tự tạo/visual trong cùng 1 frame): hàng 1 = 6082→6084, hàng 2 = 6086→6088.
 * INFERRED (không có field "order" tường minh trong response MCP), nhưng không
 * ảnh hưởng acceptance (chỉ yêu cầu hiện đủ 6 tên đúng, không yêu cầu đúng thứ tự).
 *
 * `revival` KHÔNG lấy được ảnh: node `MM_MEDIA_ Badge REVIVAL` (`3204:6082`) có
 * đúng tiền tố MM_MEDIA_ nhưng `get_media_files` trả `null` ngay từ đầu (không
 * phải do URL hết hạn — đã gọi lại 2 lần, cùng kết quả). `RulesBadge` phải tự xử
 * lý `iconSrc: null` bằng fallback, không phải bỏ huy hiệu đó khỏi danh sách.
 *
 * Tên file layer Figma của Root Further ghi "MM_MEDIA_ Badge ROOT FUTHER" (lỗi
 * chính tả FUTHER/FURTHER trong tên LAYER) nhưng text hiển thị THẬT trên canvas
 * là "ROOT FURTHER" (đúng chính tả) — dùng đúng text hiển thị, không dùng tên layer.
 */
const SECRET_BOX_BADGES: readonly Omit<SecretBoxBadgeContent, "name">[] = [
  { code: "revival", iconSrc: null, iconWidth: 80, iconHeight: 104 },
  { code: "flow_to_horizon", iconSrc: "/rules/badge-flow-to-horizon.png", iconWidth: 80, iconHeight: 104 },
  { code: "beyond_the_boundary", iconSrc: "/rules/badge-beyond-the-boundary.png", iconWidth: 80, iconHeight: 104 },
  { code: "stay_gold", iconSrc: "/rules/badge-stay-gold.png", iconWidth: 80, iconHeight: 88 },
  { code: "touch_of_light", iconSrc: "/rules/badge-touch-of-light.png", iconWidth: 80, iconHeight: 104 },
  { code: "root_further", iconSrc: "/rules/badge-root-further.png", iconWidth: 80, iconHeight: 104 },
];

/** `i18nPrefix` trỏ vào namespace `rules` — xem `locales/{vi,en}/rules.json`. */
const HERO_TIERS: readonly {
  key: HeroTierContent["key"];
  i18nPrefix: string;
  badgeSrc: string | null;
  badgeWidth: number;
  badgeHeight: number;
}[] = [
  { key: "new", i18nPrefix: "heroTier.new", badgeSrc: null, badgeWidth: 110, badgeHeight: 20 },
  { key: "rising", i18nPrefix: "heroTier.rising", badgeSrc: "/board/badge-rising-hero.png", badgeWidth: 110, badgeHeight: 20 },
  { key: "super", i18nPrefix: "heroTier.super", badgeSrc: "/board/badge-super-hero.png", badgeWidth: 109, badgeHeight: 19 },
  { key: "legend", i18nPrefix: "heroTier.legend", badgeSrc: "/board/badge-legend-hero.png", badgeWidth: 110, badgeHeight: 20 },
];

const BADGE_I18N_KEY: Record<string, string> = {
  revival: "badges.revival",
  flow_to_horizon: "badges.flowToHorizon",
  beyond_the_boundary: "badges.beyondTheBoundary",
  stay_gold: "badges.stayGold",
  touch_of_light: "badges.touchOfLight",
  root_further: "badges.rootFurther",
};

/** Dựng nội dung panel đã dịch. Nhận `t` của namespace `rules` (xem `use-rules-text.ts`). */
export function buildRulesContent(t: (key: string) => string): RulesContent {
  return {
    title: t("panel.title"),
    closeLabel: t("panel.close"),
    composeLabel: t("panel.compose"),
    heroSection: {
      heading: t("heroSection.heading"),
      description: t("heroSection.description"),
      tiers: HERO_TIERS.map((tier) => ({
        key: tier.key,
        badgeSrc: tier.badgeSrc,
        badgeWidth: tier.badgeWidth,
        badgeHeight: tier.badgeHeight,
        label: t(`${tier.i18nPrefix}.label`),
        range: t(`${tier.i18nPrefix}.range`),
        description: t(`${tier.i18nPrefix}.description`),
      })),
    },
    secretBoxSection: {
      heading: t("secretBox.heading"),
      description: t("secretBox.description"),
      badges: SECRET_BOX_BADGES.map((badge) => ({
        ...badge,
        name: t(BADGE_I18N_KEY[badge.code]),
      })),
      closingText: t("secretBox.closingText"),
      nationalHeading: t("national.heading"),
      nationalDescription: t("national.description"),
    },
  };
}
