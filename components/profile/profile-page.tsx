"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";

import type { AccountMenuProfile } from "@/components/ui/account-menu";
import { KudosFab } from "@/components/ui/kudos-fab";
import { HomeFooter } from "@/components/home/home-footer";
import { HomeHeader } from "@/components/home/home-header";
import { useHomeT } from "@/components/home/use-home-text";
import { buildSiteNav } from "@/components/layout/site-nav";
import type { KudoCardData, ToggleHeartResult } from "@/components/board/kudo-card-types";
import { useHeartToggle } from "@/components/board/use-heart-toggle";
import { useBoardToast } from "@/components/board/use-board-toast";
import { LOCALE_COOKIE, type Locale } from "@/lib/i18n/config";
import { useLocale } from "@/lib/i18n/locale-provider";

import { BadgeCollection } from "./badge-collection";
import { ProfileDirectionDropdown } from "./profile-direction-dropdown";
import { ProfileHero } from "./profile-hero";
import { ProfileKudosFeed } from "./profile-kudos-feed";
import { ProfileStatsCard } from "./profile-stats-card";
import { montserrat } from "@/components/ui/fonts";
import { useProfileT } from "./use-profile-text";
import { WriteKudoBar } from "./write-kudo-bar";
import type { ProfileDirection, ProfileStats, ProfileSummary } from "./profile-types";

export interface ProfilePageProps {
  /** Danh tính người ĐANG ĐĂNG NHẬP để vẽ header (khác `profile` khi xem người khác). */
  headerProfile: AccountMenuProfile | null;
  isAdmin: boolean;
  onSignOut: () => void;

  /** Chủ nhân của trang — chính người xem hoặc Sunner khác. */
  profile: ProfileSummary;
  /**
   * `null` là TÍN HIỆU DUY NHẤT quyết định self/other (contract phase-11):
   * `null` → thay thẻ thống kê bằng `WriteKudoBar`, ẩn mục "Đã gửi" khỏi dropdown.
   * Không nhận thêm prop `isSelf` riêng — hai nguồn sự thật cho cùng một quyết
   * định là tự tạo chỗ cho chúng lệch nhau.
   */
  stats: ProfileStats | null;
  direction: ProfileDirection;
  items: KudoCardData[];
  hasMore: boolean;
  loading: boolean;
  onDirectionChange: (direction: ProfileDirection) => void;
  onLoadMore: () => void;
  onToggleHeart: (kudosId: number) => Promise<ToggleHeartResult>;
  /** Mở modal Viết Kudo — nhận `recipientId` khi bấm từ `WriteKudoBar` (TC_WEB_PROFILE_FUN_007). */
  onCompose: (recipientId?: string) => void;
  onRules: () => void;
}

/**
 * Màn `/profile` — hai mặt của cùng một route (TC_WEB_PROFILE_FUN_001/002/006).
 * Header/Footer dùng lại `HomeHeader`/`HomeFooter` (phase-08) đúng như `BoardPage`
 * (phase-09) đã làm — ba màn cùng chrome Figma, dựng lại là chép cùng một thứ 3 lần.
 */
export function ProfilePage({
  headerProfile,
  isAdmin,
  onSignOut,
  profile,
  stats,
  direction,
  items,
  hasMore,
  loading,
  onDirectionChange,
  onLoadMore,
  onToggleHeart,
  onCompose,
  onRules,
}: ProfilePageProps) {
  const locale = useLocale();
  const t = useProfileT();
  const homeT = useHomeT();
  const router = useRouter();
  const { toastNode, showToast } = useBoardToast();

  const isSelf = stats !== null;

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

  // Link trỏ VỀ BOARD (`/kudos#kudo-{id}`), không phải `/profile#kudo-{id}`:
  // thẻ trên profile là CÙNG một Kudo với thẻ trên board (TC_WEB_PROFILE_GUI_006,
  // "same mapper and same column list"), và chỉ `/kudos` có anchor cuộn tới đúng
  // thẻ — profile không tự lọc theo hashtag/id nên không có đích tương đương.
  const handleCopyLink = useCallback(
    (kudosId: number) => {
      const url = `${window.location.origin}/kudos#kudo-${kudosId}`;
      void navigator.clipboard
        .writeText(url)
        .then(() => showToast(t("card.copied")))
        .catch(() => showToast(t("card.heartFailed")));
    },
    [showToast, t],
  );

  const openProfile = useCallback((userId: string) => router.push(`/profile?id=${userId}`), [router]);

  const emptyMessage = direction === "received" ? t("empty.received") : t("empty.sent");

  return (
    <div className="relative isolate flex min-h-full flex-1 flex-col bg-[#00101A]">
      <div className="relative z-20 lg:absolute lg:inset-x-0 lg:top-0">
        <HomeHeader
          locale={locale}
          nav={buildSiteNav(homeT)}
          profile={headerProfile}
          isAdmin={isAdmin}
          onLocaleChange={handleLocaleChange}
          onProfile={() => router.push("/profile")}
          onAdmin={() => router.push("/admin")}
          onSignOut={onSignOut}
        />
      </div>

      <main className="mx-auto flex w-full max-w-[1440px] flex-col gap-12 px-6 pt-24 pb-16 md:px-16 lg:gap-16 lg:px-36 lg:pt-[200px] lg:pb-24">
        <ProfileHero profile={profile} />
        <BadgeCollection isSelf={isSelf} />

        <div className="mx-auto flex w-full max-w-[422px] flex-col items-center">
          {/* Điều kiện thẳng vào `stats !== null` (không dùng biến `isSelf`) để
              TypeScript tự thu hẹp kiểu `ProfileStats | null` → `ProfileStats`
              ngay tại nhánh này — qua một biến `boolean` trung gian, control-flow
              analysis không đảm bảo bám theo được. */}
          {stats !== null ? (
            <ProfileStatsCard stats={stats} onOpenBox={() => undefined} />
          ) : (
            <WriteKudoBar recipientName={profile.fullName} onClick={() => onCompose(profile.id)} />
          )}
        </div>

        <div className="flex flex-col gap-8">
          <div className={`${montserrat.className} flex w-full flex-col gap-4`}>
            <p className="text-2xl leading-8 font-bold text-white">{t("section.eyebrow")}</p>
            <div className="h-px w-full bg-[#2E3940]" aria-hidden="true" />
            <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
              <h2 className="text-[clamp(2rem,1rem+4vw,3.5625rem)] leading-[1.12] font-bold tracking-[-0.25px] text-[#FFEA9E]">
                {t("section.title")}
              </h2>
              <ProfileDirectionDropdown
                direction={direction}
                receivedCount={profile.receivedKudosCount}
                sentCount={stats?.sentKudos ?? null}
                onChange={onDirectionChange}
              />
            </div>
          </div>

          <ProfileKudosFeed
            items={applyOverrides(items)}
            emptyMessage={emptyMessage}
            onLoadMore={onLoadMore}
            hasMore={hasMore}
            loading={loading}
            pendingHeartIds={pendingHeartIds}
            onToggleHeart={toggle}
            onCopyLink={handleCopyLink}
            onOpenProfile={openProfile}
          />
        </div>
      </main>

      <KudosFab onRules={onRules} onCompose={() => onCompose()} />
      <HomeFooter onRules={onRules} />

      {toastNode}
    </div>
  );
}
