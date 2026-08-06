"use client";

import Image from "next/image";

import { SiteHeader, type NavItem } from "@/components/layout/site-header";
import { AccountMenu, type AccountMenuProfile } from "@/components/ui/account-menu";
import { LanguageSwitcher } from "@/components/ui/language-switcher";
import { montserrat } from "@/components/ui/fonts";
import type { Locale } from "@/lib/i18n/config";
import { useT } from "@/lib/i18n/locale-provider";

import { NotificationBell } from "./notification-bell";
import { useHomeT } from "./use-home-text";

export interface HomeHeaderProps {
  locale: Locale;
  nav: NavItem[];
  /** `null` = khách chưa đăng nhập. */
  profile: AccountMenuProfile | null;
  isAdmin: boolean;
  onLocaleChange: (next: Locale) => void;
  onProfile: () => void;
  onAdmin: () => void;
  onSignOut: () => void;
}

/**
 * Header trang chủ (`mms_A1_Header`, node `2167:9091`) — chỉ là phần COMPOSE:
 * `SiteHeader` (phase-06) lo phần khung, file này lo việc nhét logo thật, bộ
 * chọn ngôn ngữ, chuông thông báo và menu tài khoản vào đúng chỗ.
 *
 * Tách khỏi `home-page.tsx` để file đó ở lại dưới ngưỡng 200 dòng của
 * `development-rules.md`.
 */
export function HomeHeader({
  locale,
  nav,
  profile,
  isAdmin,
  onLocaleChange,
  onProfile,
  onAdmin,
  onSignOut,
}: HomeHeaderProps) {
  const commonT = useT();
  const t = useHomeT();

  return (
    <SiteHeader
      appName={commonT("app.name")}
      nav={nav}
      logo={
        /* mm:I2167:9091;178:1033;178:1030 — 52×48 (footer dùng bản 69×64). */
        <Image src="/brand/saa-logo.png" alt={commonT("app.name")} width={52} height={48} priority />
      }
      slot={
        <>
          <LanguageSwitcher locale={locale} onChange={onLocaleChange} />
          {/* mm:I2167:9091;186:2101 — vỏ chuông, chưa nối dữ liệu (gap #14 còn treo). */}
          <NotificationBell />
          {profile ? (
            /* mm:I2167:9091;186:1597 */
            <AccountMenu
              profile={profile}
              isAdmin={isAdmin}
              onProfile={onProfile}
              onAdmin={isAdmin ? onAdmin : undefined}
              onSignOut={onSignOut}
            />
          ) : (
            /* Figma CHỈ vẽ trạng thái đã đăng nhập. Nhưng Acceptance phase-08
               bắt guest xem được toàn bộ trang, nên chỗ `AccountMenu` đổi thành
               lối vào `/login` thay vì để trống — không chặn nội dung nào. */
            <a
              href="/login"
              className={`${montserrat.className} rounded border border-[#998C5F] px-4 py-2 text-sm font-bold text-white transition-colors duration-200 ease-out hover:text-[#FFEA9E] motion-reduce:transition-none`}
            >
              {t("nav.login")}
            </a>
          )}
        </>
      }
    />
  );
}
