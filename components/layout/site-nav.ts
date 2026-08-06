import type { NavItem } from "./site-header";

/** Route của 3 mục nav chính — dùng làm khoá đánh dấu mục đang mở. */
export const SITE_NAV_HREFS = {
  home: "/",
  awards: "/awards",
  kudos: "/kudos",
} as const;

export type SiteNavHref = (typeof SITE_NAV_HREFS)[keyof typeof SITE_NAV_HREFS];

/**
 * Ba mục nav của header/footer — MỘT nguồn cho mọi màn.
 *
 * Trước đó mảng này bị chép ở 3 chỗ (`home-page.tsx`, `home-footer.tsx`,
 * `board-page.tsx`), và bản trong `board-page.tsx` đã lệch thật: nó dùng
 * `t("section.eyebrow")` ("Sun* Annual Awards 2025") làm nhãn mục đầu thay vì
 * "About SAA 2025", rồi hardcode "Award Information" / "Sun* Kudos" bằng tiếng
 * Anh nên đổi sang tiếng Việt không có tác dụng. Chép ba lần thì lệch là chuyện
 * sớm muộn.
 *
 * `t` nhận từ ngoài vào (thay vì gọi hook bên trong) để hàm này ở lại tầng
 * thuần — gọi được từ Server Component, và test được không cần render. Ba khoá
 * `nav.*` nằm trong namespace `home` vì header/footer xuất hiện lần đầu ở đó.
 */
export function buildSiteNav(t: (key: string) => string, activeHref?: SiteNavHref): NavItem[] {
  return [
    { label: t("nav.aboutSaa"), href: SITE_NAV_HREFS.home },
    { label: t("nav.awardInfo"), href: SITE_NAV_HREFS.awards },
    { label: t("nav.sunKudos"), href: SITE_NAV_HREFS.kudos },
  ].map((item) => (item.href === activeHref ? { ...item, active: true } : item));
}
