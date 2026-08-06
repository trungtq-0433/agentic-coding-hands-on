"use client";

import { useRouter } from "next/navigation";
import { useCallback } from "react";

import type { AccountMenuProfile } from "@/components/ui/account-menu";
import { KudosFab } from "@/components/ui/kudos-fab";
import { LOCALE_COOKIE, type Locale } from "@/lib/i18n/config";
import { useLocale } from "@/lib/i18n/locale-provider";
import { HomeFooter } from "@/components/home/home-footer";
import { HomeHeader } from "@/components/home/home-header";
import { useHomeT } from "@/components/home/use-home-text";
import { buildSiteNav, SITE_NAV_HREFS } from "@/components/layout/site-nav";

import { BoardBackdrop } from "./board-backdrop";
import { BoardBanner } from "./board-banner";
import { BoardSidebar, type SidebarStats } from "./board-sidebar";
import { HighlightCarousel, type FilterOption } from "./highlight-carousel";
import type { KudoCardData, ToggleHeartResult } from "./kudo-card-types";
import { KudosFeed } from "./kudos-feed";
import { SectionHeader } from "./section-header";
import type { LeaderboardEntry } from "./leaderboard-list";
import { SpotlightSection, type SpotlightName, type SpotlightTicker } from "./spotlight-section";
import { useBoardT } from "./use-board-text";
import { useBoardToast } from "./use-board-toast";
import { useHeartToggle } from "./use-heart-toggle";

export interface BoardPageProps {
  profile: AccountMenuProfile | null;
  isAdmin: boolean;
  highlights: KudoCardData[];
  allKudos: KudoCardData[];
  hashtagOptions: FilterOption[];
  departmentOptions: FilterOption[];
  selectedHashtag: string | null;
  selectedDepartment: string | null;
  totalKudos: number;
  spotlightNames: SpotlightName[];
  spotlightTicker: SpotlightTicker[];
  stats: SidebarStats;
  recentGiftReceivers: LeaderboardEntry[];
  newKudosQueue: number;
  hasMore: boolean;
  loading: boolean;
  onFilterChange: (kind: "hashtag" | "department", value: string | null) => void;
  onLoadMore: () => void;
  onFlushQueue: () => void;
  onToggleHeart: (kudosId: number) => Promise<ToggleHeartResult>;
  onCompose: () => void;
  onRules: () => void;
  onOpenBox: () => void;
  onSignOut: () => void;
}

/**
 * Màn `/kudos` — Figma `Sun* Kudos - Live board` (`2940:13431`, screenId
 * `MaZUn5xHXZ`). Track A / phase-09: `components/board/**` không import
 * `lib/data|actions|supabase|realtime`; mọi hành vi động đi qua props.
 *
 * Header/Footer dùng lại `HomeHeader`/`HomeFooter` (phase-08): hai màn dùng
 * CHUNG component Figma (`186:1602`, `342:1427`), chỉ khác mục nav đang chọn.
 * Dựng lại là chép hai bản của cùng một thứ — lần sửa chrome sau sẽ sót một
 * chỗ, đúng vết xe đã đổ với logo Root Further ở phase-08.
 */
export function BoardPage({
  profile,
  isAdmin,
  highlights,
  allKudos,
  hashtagOptions,
  departmentOptions,
  selectedHashtag,
  selectedDepartment,
  totalKudos,
  spotlightNames,
  spotlightTicker,
  stats,
  recentGiftReceivers,
  newKudosQueue,
  hasMore,
  loading,
  onFilterChange,
  onLoadMore,
  onFlushQueue,
  onToggleHeart,
  onCompose,
  onRules,
  onOpenBox,
  onSignOut,
}: BoardPageProps) {
  const locale = useLocale();
  const t = useBoardT();
  // Nhãn nav nằm ở namespace `home` (header/footer xuất hiện lần đầu ở trang chủ).
  const homeT = useHomeT();
  const router = useRouter();
  const { toastNode, showToast } = useBoardToast();

  const heartFailed = useCallback(() => showToast(t("card.heartFailed")), [showToast, t]);
  const { pendingHeartIds, applyOverrides, toggle } = useHeartToggle({
    onToggleHeart,
    onError: heartFailed,
  });

  function handleLocaleChange(next: Locale) {
    if (next === locale) return;
    document.cookie = `${LOCALE_COOKIE}=${next}; path=/; max-age=31536000; SameSite=Lax`;
    router.refresh();
  }

  const handleCopyLink = useCallback(
    (kudosId: number) => {
      const url = `${window.location.origin}/kudos#kudo-${kudosId}`;
      void navigator.clipboard
        .writeText(url)
        .then(() => showToast(t("card.copied")))
        // Clipboard API cần ngữ cảnh bảo mật và có thể bị từ chối quyền — nuốt
        // lỗi im lặng là để lại nút bấm không phản hồi.
        .catch(() => showToast(t("card.heartFailed")));
    },
    [showToast, t],
  );

  const openProfile = useCallback((userId: string) => router.push(`/profile?id=${userId}`), [router]);

  return (
    <div className="relative isolate flex min-h-full flex-1 flex-col bg-[#00101A]">
      <BoardBackdrop />

      <div className="relative z-20 lg:absolute lg:inset-x-0 lg:top-0">
        <HomeHeader
          locale={locale}
          nav={buildSiteNav(homeT, SITE_NAV_HREFS.kudos)}
          profile={profile}
          isAdmin={isAdmin}
          onLocaleChange={handleLocaleChange}
          onProfile={() => router.push("/profile")}
          onAdmin={() => router.push("/admin")}
          onSignOut={onSignOut}
        />
      </div>

      <main className="mx-auto flex w-full max-w-[1440px] flex-col gap-12 px-6 pt-12 pb-16 md:px-16 lg:gap-20 lg:px-36 lg:pt-[184px] lg:pb-24">
        <BoardBanner onCompose={onCompose} onSearchSunner={() => router.push("/kudos#spotlight")} />

        <HighlightCarousel
          items={highlights}
          hashtagOptions={hashtagOptions}
          departmentOptions={departmentOptions}
          selectedHashtag={selectedHashtag}
          selectedDepartment={selectedDepartment}
          onFilterChange={onFilterChange}
          onOpenProfile={openProfile}
          onToggleHeart={toggle}
          onCopyLink={handleCopyLink}
          pendingHeartIds={pendingHeartIds}
        />

        {/* mm:2940:13476 `B.6_Header Giải thưởng` */}
        <div id="spotlight" className="flex flex-col gap-8">
          <SectionHeader title={t("spotlight.title")} />
          <SpotlightSection
            totalKudos={totalKudos}
            names={spotlightNames}
            ticker={spotlightTicker}
            onSelectName={openProfile}
          />
        </div>

        {/* mm:2940:14221 `C.1_Header Giải thưởng` + mm:2940:13481 — kudos trái,
            sidebar phải; dưới `lg` sidebar xuống dưới. */}
        <SectionHeader title={t("allKudos.title")} />
        <div className="flex flex-col gap-8 lg:flex-row lg:items-start lg:gap-12">
          <div className="min-w-0 flex-1">
            <KudosFeed
              items={applyOverrides(allKudos)}
              newKudosQueue={newKudosQueue}
              onFlushQueue={onFlushQueue}
              onLoadMore={onLoadMore}
              hasMore={hasMore}
              loading={loading}
              pendingHeartIds={pendingHeartIds}
              onToggleHeart={toggle}
              onCopyLink={handleCopyLink}
              onOpenProfile={openProfile}
            />
          </div>
          <BoardSidebar
            stats={stats}
            recentGiftReceivers={recentGiftReceivers}
            onOpenBox={onOpenBox}
            onOpenProfile={openProfile}
          />
        </div>
      </main>

      <KudosFab onRules={onRules} onCompose={onCompose} />
      <HomeFooter onRules={onRules} />

      {toastNode}
    </div>
  );
}
