"use client";

import { useRouter } from "next/navigation";

import { HomeFooter } from "@/components/home/home-footer";
import { HomeHeader } from "@/components/home/home-header";
import { useHomeT } from "@/components/home/use-home-text";
import { buildSiteNav, SITE_NAV_HREFS } from "@/components/layout/site-nav";
import { montserrat } from "@/components/ui/fonts";
import type { AccountMenuProfile } from "@/components/ui/account-menu";
import { LOCALE_COOKIE, type Locale } from "@/lib/i18n/config";
import { useLocale } from "@/lib/i18n/locale-provider";
import type { AwardContent } from "@/lib/content/awards";

import { AwardCard } from "./award-card";
import { AwardsCta } from "./awards-cta";
import { AwardsKeyvisual } from "./awards-keyvisual";
import { AwardsNav } from "./awards-nav";
import { useAwardsScrollspy } from "./use-awards-scrollspy";
import { useAwardsT } from "./use-awards-text";

export interface AwardsPageProps {
  /** 6 hạng mục giải, nội dung tĩnh từ `lib/content/awards.ts` (phase-12 sở hữu). */
  awards: AwardContent[];
  /** Slug ban đầu từ URL hash (vd `/awards#top-talent` khi bấm "Chi tiết" từ Homepage). */
  activeSlug?: string;
  /** Điều hướng SANG route khác (`/profile`, `/admin`, `/kudos`…). Cuộn NỘI BỘ giữa các thẻ giải KHÔNG đi qua đây — `AwardsPage` tự quản lý (xem `use-awards-scrollspy.ts`), đúng integration contract của phase-12. */
  onNavigate: (path: string) => void;
  /** `null` = khách chưa đăng nhập. Guest xem được toàn bộ nội dung, không chặn gì ở UI. */
  profile: AccountMenuProfile | null;
  isAdmin: boolean;
  onSignOut: () => void;
  /** Mở modal Thể lệ (phase-13, CHƯA TỒN TẠI) — mục "Tiêu chuẩn chung" ở `HomeFooter` cần prop này. Client wrapper stub lại, giống `HomePageClient`/`BoardPageClient`. */
  onRules: () => void;
}

/**
 * Trang `/awards` — Figma frame `Hệ thống giải` (`313:8436`, screenId
 * `zFYDgyj_pD`). Track A / phase-12: `components/awards/**` không import
 * `lib/data|actions|supabase|realtime`, mọi hành vi động qua props.
 *
 * Header/Footer dùng lại `HomeHeader`/`HomeFooter` (phase-08, đã dùng lại ở
 * phase-09 `BoardPage`) — CÙNG component Figma `mms_A_Header`/`mms_D_Footer`,
 * chỉ khác mục nav đang chọn (`SITE_NAV_HREFS.awards`). Dựng lại là chép bản
 * thứ ba của cùng một thứ, đúng vết xe phase-08 đã cảnh báo.
 */
export function AwardsPage({
  awards,
  activeSlug,
  onNavigate,
  profile,
  isAdmin,
  onSignOut,
  onRules,
}: AwardsPageProps) {
  const locale = useLocale();
  const homeT = useHomeT();
  const t = useAwardsT();
  const router = useRouter();

  const slugs = awards.map((award) => award.slug);
  const { activeSlug: currentSlug, registerRef, scrollToSlug } = useAwardsScrollspy({
    slugs,
    initialSlug: activeSlug,
  });

  function handleLocaleChange(next: Locale) {
    if (next === locale) return;
    document.cookie = `${LOCALE_COOKIE}=${next}; path=/; max-age=31536000; SameSite=Lax`;
    router.refresh();
  }

  return (
    <div className="relative isolate flex min-h-full flex-1 flex-col bg-[#00101A]">
      <div className="relative z-20 lg:absolute lg:inset-x-0 lg:top-0">
        <HomeHeader
          locale={locale}
          nav={buildSiteNav(homeT, SITE_NAV_HREFS.awards)}
          profile={profile}
          isAdmin={isAdmin}
          onLocaleChange={handleLocaleChange}
          onProfile={() => onNavigate("/profile")}
          onAdmin={() => onNavigate("/admin")}
          onSignOut={onSignOut}
        />
      </div>

      <main className="mx-auto flex w-full max-w-[1512px] flex-col gap-12 px-6 pt-12 pb-16 md:px-16 lg:gap-20 lg:px-36 lg:pt-[184px] lg:pb-24">
        <AwardsKeyvisual />

        {/* mm:A_Title hệ thống giải thưởng — CSV item A */}
        {/* CẢ HAI dòng đều CANH GIỮA. Đo bản vẽ: eyebrow `313:8454` là khối
            rộng đúng 1152 (= bề ngang khung nội dung) với `textAlign: center`;
            tiêu đề `313:8457` rộng 931 nhưng nằm trong `Frame 488` rộng 1152
            `justify-content: center`, nên mép trái rơi vào x=254 —
            (1152−931)/2 = 110.5, cộng 144 ra đúng 254. Bản trước để cả hai canh
            trái ở x=144, lệch 110px. */}
        <div className={`${montserrat.className} flex flex-col gap-4 text-center`}>
          <p className="text-2xl leading-8 font-bold text-white">{t("section.eyebrow")}</p>
          <div className="h-px w-full bg-[#2E3940]" aria-hidden="true" />
          <h2 className="text-[clamp(2rem,1rem+4vw,3.5625rem)] leading-[1.12] font-bold tracking-[-0.25px] text-[#FFEA9E]">
            {t("section.heading")}
          </h2>
        </div>

        {/* mm:B_Hệ thống giải thưởng — menu trái (C) + danh sách thẻ (D.1–D.6).
            Grid 2 cột cố định `240px` + phần còn lại — khuôn "sticky sidebar
            cạnh nội dung dài" chắc chắn hơn flex (xem comment ở `awards-nav.tsx`
            Lỗi 3). Cả 2 cột cùng bắt đầu ở đây → menu ngang hàng thẻ đầu tiên. */}
        {/* `lg:pl-11` = 44px: bản vẽ thụt cả khối menu+thẻ vào so với khung nội
            dung — menu bắt đầu ở x=188 chứ không phải x=144 (mép khung), và thẻ
            ở x=443. Bản trước bỏ qua khoảng thụt này nên cả hai cột dạt trái.
            `lg:gap-4` (15px) là khoảng thật giữa mép phải menu (428) và mép trái
            thẻ (443) — trước để `gap-16` (64px) nên thẻ bị bóp còn 833 thay vì 856. */}
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-[240px_1fr] lg:items-start lg:gap-4 lg:pl-11">
          <AwardsNav awards={awards} activeSlug={currentSlug} onSelect={scrollToSlug} />
          <div className="flex min-w-0 flex-col gap-12 lg:gap-16">
            {awards.map((award, index) => (
              <AwardCard key={award.slug} award={award} index={index} registerRef={registerRef} />
            ))}
          </div>
        </div>

        <AwardsCta onDetail={() => onNavigate("/kudos")} />
      </main>

      <HomeFooter onRules={onRules} />
    </div>
  );
}
