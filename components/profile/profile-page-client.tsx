"use client";

import { useCallback, useMemo, useState } from "react";

import { AppModalHost, type AppModal } from "@/components/modals/app-modal-host";
import type { AccountMenuProfile } from "@/components/ui/account-menu";
import type { ToggleHeartResult } from "@/components/board/kudo-card-types";

import { buildMockReceivedFeed, buildMockSentFeed } from "./figma-profile-mock";
import { ProfilePage } from "./profile-page";
import type { ProfileDirection, ProfileStats, ProfileSummary } from "./profile-types";

/** "10 cards at a time" — TC_WEB_PROFILE_FUN_013. */
const PAGE_SIZE = 10;
/** Trần sinh mock: đếm thật (`receivedKudosCount`/`sentKudos`) có thể lớn hơn nhiều so với
 * số thẻ mock cần để kiểm cuộn vô hạn — chặn trên tránh sinh hàng chục nghìn object vô ích. */
const MAX_MOCK_POOL = 40;

function poolTotal(count: number): number {
  return Math.min(Math.max(count, 0), MAX_MOCK_POOL);
}

export interface ProfilePageClientProps {
  /** Danh tính người ĐANG ĐĂNG NHẬP (cho header) — luôn là chính chủ, khác `profile` khi xem người khác. */
  headerProfile: AccountMenuProfile | null;
  isAdmin: boolean;
  signOut: () => Promise<void>;
  /** Chủ nhân trang (chính mình hoặc Sunner khác) — Server Component đã quyết định xong. */
  profile: ProfileSummary;
  /** `null` = đang xem người khác (contract phase-11, xem `profile-types.ts`). */
  stats: ProfileStats | null;
}

/**
 * Boundary Client Component giữa `app/profile/page.tsx` (Server) và `ProfilePage`
 * (thuần trình bày) — cùng vai trò `BoardPageClient` (phase-09): giữ toàn bộ
 * state tương tác (hướng xem, phân trang, thả tim) và dữ liệu MOCK cho tới khi
 * phase-16 nối Track B thật (`public_kudos_feed`, `my_sent_kudos`, RPC `toggle_heart`).
 *
 * **Số lượng mock KHÔNG bịa tách rời stats**: pool "Đã nhận" sinh đúng
 * `profile.receivedKudosCount` thẻ (số THẬT của chính chủ, hoặc số mock đã gán
 * sẵn cho profile người khác trong `figma-profile-mock.ts`), pool "Đã gửi" sinh
 * đúng `stats.sentKudos` — nhờ vậy số đếm trên dropdown LUÔN khớp số thẻ hiện ra
 * (TC_WEB_PROFILE_SEC_002: "card count matches the dropdown label"), không có
 * hai nguồn số lệch nhau.
 */
export function ProfilePageClient({
  headerProfile,
  isAdmin,
  signOut,
  profile,
  stats,
}: ProfilePageClientProps) {
  const [direction, setDirection] = useState<ProfileDirection>("received");
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const [loading, setLoading] = useState(false);
  const [modal, setModal] = useState<AppModal>(null);

  const receivedPool = useMemo(
    () => buildMockReceivedFeed(profile, poolTotal(profile.receivedKudosCount)),
    [profile],
  );
  const sentPool = useMemo(
    () => (stats ? buildMockSentFeed(profile, poolTotal(stats.sentKudos)) : []),
    [profile, stats],
  );
  const pool = direction === "received" ? receivedPool : sentPool;
  const items = pool.slice(0, Math.min(visibleCount, pool.length));
  const hasMore = visibleCount < pool.length;

  const handleDirectionChange = useCallback(
    (next: ProfileDirection) => {
      // Chọn lại đúng hướng đang xem là no-op (TC_WEB_PROFILE_FUN_011) — dropdown
      // đã tự chặn ở `profile-direction-dropdown.tsx`, chặn lại ở đây là phòng
      // hờ (defense in depth) nếu sau này có nơi khác gọi thẳng callback này.
      if (next === direction) return;
      setLoading(true);
      // `setTimeout` để trạng thái "đang tải" thấy được — dữ liệu thật (phase-16)
      // sẽ có độ trễ mạng tương tự. Nhãn hướng trên trigger chỉ đổi SAU khi trang
      // 1 của hướng mới đã "tải" xong, không đổi ngay khi bấm (TC_WEB_PROFILE_FUN_010).
      window.setTimeout(() => {
        setDirection(next);
        setVisibleCount(PAGE_SIZE);
        setLoading(false);
      }, 300);
    },
    [direction],
  );

  const handleLoadMore = useCallback(() => {
    if (loading || visibleCount >= pool.length) return;
    setLoading(true);
    window.setTimeout(() => {
      setVisibleCount((prev) => Math.min(prev + PAGE_SIZE, pool.length));
      setLoading(false);
    }, 400);
  }, [loading, visibleCount, pool.length]);

  const handleToggleHeart = useCallback(
    (kudosId: number): Promise<ToggleHeartResult> =>
      new Promise((resolve) => {
        window.setTimeout(() => {
          const target = pool.find((item) => item.id === kudosId);
          if (!target) {
            resolve({ ok: false, code: "not_found" });
            return;
          }
          const hearted = !target.hearted;
          resolve({ ok: true, hearted, heartCount: target.heartCount + (hearted ? 1 : -1) });
        }, 500);
      }),
    [pool],
  );

  // Tham số `recipientId` chưa dùng tới (modal Viết Kudo của phase-10 chưa tồn
  // tại) nhưng vẫn phải khai trong chữ ký để khớp `ProfilePageProps.onCompose`
  // — bỏ tên tham số thay vì đặt `_recipientId` để không vướng
  // `@typescript-eslint/no-unused-vars` (repo này không bật `argsIgnorePattern`).
  function handleSignOut() {
    void signOut().catch((error: unknown) => {
      console.error("[profile] đăng xuất thất bại:", error);
    });
  }

  return (
    <>
    <ProfilePage
      headerProfile={headerProfile}
      isAdmin={isAdmin}
      onSignOut={handleSignOut}
      profile={profile}
      stats={stats}
      direction={direction}
      items={items}
      hasMore={hasMore}
      loading={loading}
      onDirectionChange={handleDirectionChange}
      onLoadMore={handleLoadMore}
      onToggleHeart={handleToggleHeart}
      onCompose={() => setModal("compose")}
      onRules={() => setModal("rules")}
    />
    <AppModalHost active={modal} onChange={setModal} />
    </>
  );
}
