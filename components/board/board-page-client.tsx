"use client";

import { useCallback, useState } from "react";

import { AppModalHost, type AppModal } from "@/components/modals/app-modal-host";
import type { AccountMenuProfile } from "@/components/ui/account-menu";

import { BoardPage } from "./board-page";
import {
  buildFigmaGiftReceivers,
  buildFigmaKudoMock,
  buildFigmaSpotlightNames,
  buildFigmaTicker,
  FIGMA_TOTAL_KUDOS,
} from "./figma-board-mock";
import type { KudoCardData, ToggleHeartResult } from "./kudo-card-types";

/** Số thẻ nạp thêm mỗi lần cuộn tới đáy. */
const PAGE_SIZE = 5;
/** Tổng số thẻ mock — giả lập "hết dữ liệu" để kiểm được trạng thái cuối danh sách. */
const MOCK_TOTAL = 23;

export interface BoardPageClientProps {
  profile: AccountMenuProfile | null;
  isAdmin: boolean;
  signOut: () => Promise<void>;
}

/**
 * Boundary Client Component giữa `app/kudos/page.tsx` (Server Component) và
 * `BoardPage`. Cùng lý do như `home-page-client.tsx`: Next không cho truyền
 * function thường từ Server sang Client Component, trừ Server Action.
 *
 * **Đây là chỗ phase-16 thay dữ liệu thật.** Hiện tại toàn bộ đến từ
 * `figma-board-mock.ts`:
 * - `onLoadMore` cắt trang từ mảng mock thay vì gọi keyset cursor thật
 *   (`lib/kudos/cursor.ts` của phase-04).
 * - `onToggleHeart` **giả lập** độ trễ mạng rồi lật trạng thái. Nó tồn tại để
 *   kiểm được đúng một thứ mà Acceptance đòi: bấm tim 5 lần thật nhanh chỉ sinh
 *   MỘT lời gọi (nhờ `pending` trong `use-heart-toggle.ts`). Phase-16 thay bằng
 *   RPC `toggle_heart` thật — chữ ký `Promise<ToggleHeartResult>` giữ nguyên.
 * - `newKudosQueue` luôn 0: dải "Có N kudo mới" chạy bằng tín hiệu Broadcast của
 *   phase-05, chưa nối. Không giả lập số đếm nhảy loạn để trông có vẻ sống động.
 * - `onCompose`/`onRules`/`onOpenBox` mở modal của phase-10/13/15 — chưa tồn tại.
 */
export function BoardPageClient({ profile, isAdmin, signOut }: BoardPageClientProps) {
  const [items, setItems] = useState<KudoCardData[]>(() => buildFigmaKudoMock(PAGE_SIZE));
  const [loading, setLoading] = useState(false);
  const [selectedHashtag, setSelectedHashtag] = useState<string | null>(null);
  const [selectedDepartment, setSelectedDepartment] = useState<string | null>(null);
  const [modal, setModal] = useState<AppModal>(null);

  const hasMore = items.length < MOCK_TOTAL;

  const handleLoadMore = useCallback(() => {
    if (loading || items.length >= MOCK_TOTAL) return;
    setLoading(true);
    // `setTimeout` để thấy được trạng thái "đang tải" — dữ liệu thật sẽ có độ trễ mạng.
    window.setTimeout(() => {
      setItems(buildFigmaKudoMock(Math.min(items.length + PAGE_SIZE, MOCK_TOTAL)));
      setLoading(false);
    }, 400);
  }, [loading, items.length]);

  const handleToggleHeart = useCallback(
    (kudosId: number): Promise<ToggleHeartResult> =>
      new Promise((resolve) => {
        window.setTimeout(() => {
          const target = items.find((item) => item.id === kudosId);
          if (!target) {
            resolve({ ok: false, code: "not_found" });
            return;
          }
          const hearted = !target.hearted;
          resolve({
            ok: true,
            hearted,
            heartCount: target.heartCount + (hearted ? 1 : -1),
          });
        }, 500);
      }),
    [items],
  );

  const handleFilterChange = useCallback((kind: "hashtag" | "department", value: string | null) => {
    if (kind === "hashtag") setSelectedHashtag(value);
    else setSelectedDepartment(value);
    // phase-16: lọc thật chạy ở server (`listKudos` của phase-04), không lọc ở client.
  }, []);

  function handleSignOut() {
    void signOut().catch((error: unknown) => {
      console.error("[board] đăng xuất thất bại:", error);
    });
  }

  return (
    <>
    <BoardPage
      profile={profile}
      isAdmin={isAdmin}
      highlights={items.slice(0, 5)}
      allKudos={items}
      hashtagOptions={[
        { value: "dedicated", label: "#Dedicated" },
        { value: "inspring", label: "#Inspring" },
      ]}
      departmentOptions={[{ value: "unassigned", label: "Chưa phân loại" }]}
      selectedHashtag={selectedHashtag}
      selectedDepartment={selectedDepartment}
      totalKudos={FIGMA_TOTAL_KUDOS}
      spotlightNames={buildFigmaSpotlightNames()}
      spotlightTicker={buildFigmaTicker()}
      /* `unopenedBoxes: 25` khớp bản vẽ (`D.1.7_` ghi "25") nên nút "Mở Secret
         Box" hiện màu vàng như thiết kế. Luật "0 hộp chưa mở → nút disabled"
         vẫn nằm nguyên trong `BoardSidebar`; đổi số ở mock không nới lỏng nó.
         Trước đó tôi để 0 theo mục "Ngoài phạm vi" của phase file, nhưng như
         vậy toàn bộ sidebar luôn hiện trạng thái tắt, lệch hẳn bản vẽ. */
      stats={{ receivedKudos: 25, sentKudos: 25, hearts: 25, openedBoxes: 25, unopenedBoxes: 25 }}
      recentGiftReceivers={buildFigmaGiftReceivers()}
      newKudosQueue={0}
      hasMore={hasMore}
      loading={loading}
      onFilterChange={handleFilterChange}
      onLoadMore={handleLoadMore}
      onFlushQueue={() => undefined}
      onToggleHeart={handleToggleHeart}
      onCompose={() => setModal("compose")}
      onRules={() => setModal("rules")}
      onOpenBox={() => setModal("secretBox")}
      onSignOut={handleSignOut}
    />
    <AppModalHost active={modal} onChange={setModal} unopenedBoxes={25} />
    </>
  );
}
