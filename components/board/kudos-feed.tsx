"use client";

/**
 * Feed cuộn vô hạn — danh sách thẻ KUDO (All Kudos). Cuộn vô hạn bằng
 * `IntersectionObserver` trên sentinel cuối danh sách, chỉ gọi `onLoadMore`
 * khi còn trang kế (`hasMore`) và không đang tải (`loading`) — chặn bắn liên
 * tục lúc cuộn nhanh. Không tự fetch dữ liệu, mọi trạng thái qua props (Track A).
 */

import { useEffect, useRef } from "react";

import { montserrat } from "@/components/ui/fonts";
import { KudoCard } from "./kudo-card";
import { useBoardT } from "./use-board-text";
import type { KudoCardData } from "./kudo-card-types";

export interface KudosFeedProps {
  items: KudoCardData[];
  /** Số kudo mới đang chờ → hiện dải "Có N kudo mới". 0 thì ẩn. */
  newKudosQueue: number;
  onFlushQueue: () => void;
  /** Trả về trang kế; `nextCursor === null` là hết. */
  onLoadMore: () => void;
  hasMore: boolean;
  loading: boolean;
  pendingHeartIds: ReadonlySet<number>;
  onToggleHeart: (kudosId: number) => void;
  onCopyLink: (kudosId: number) => void;
  onOpenProfile: (userId: string) => void;
}

export function KudosFeed({
  items,
  newKudosQueue,
  onFlushQueue,
  onLoadMore,
  hasMore,
  loading,
  pendingHeartIds,
  onToggleHeart,
  onCopyLink,
  onOpenProfile,
}: KudosFeedProps) {
  const t = useBoardT();
  const sentinelRef = useRef<HTMLDivElement | null>(null);

  // Ref hoá giá trị đọc bên trong callback observer để không phải huỷ/dựng
  // lại observer mỗi khi `loading` đổi (chỉ cần đổi khi `hasMore` đổi). Gán
  // ref trong `useEffect`, không phải lúc render — React 19 cấm ghi ref khi render.
  const loadingRef = useRef(loading);
  const onLoadMoreRef = useRef(onLoadMore);
  useEffect(() => {
    loadingRef.current = loading;
    onLoadMoreRef.current = onLoadMore;
  });

  useEffect(() => {
    if (!hasMore) return;
    const node = sentinelRef.current;
    if (!node) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting && !loadingRef.current) {
          onLoadMoreRef.current();
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [hasMore]);

  const isEmpty = items.length === 0 && !loading;

  return (
    <div className={`${montserrat.className} flex w-full flex-col items-center gap-6`}>
      {newKudosQueue > 0 && (
        <button
          type="button"
          onClick={onFlushQueue}
          // `boxShadow` inline chứ không `shadow-[...]`: dấu phẩy bên trong
          // `rgba()` bị lớp arbitrary của Tailwind v4 dựng sai (xem award-card.tsx).
          style={{ boxShadow: "0 4px 10px 0 rgba(0, 0, 0, 0.2)" }}
          className="sticky top-0 z-10 rounded-full bg-[#D4271D] px-6 py-3 text-base font-bold text-white transition-colors duration-200 ease-out hover:bg-[#B31F17] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white motion-reduce:transition-none"
        >
          {t("feed.newKudos").replace("{count}", String(newKudosQueue))}
        </button>
      )}

      {isEmpty ? (
        <p className="py-10 text-center text-base text-[#00101A]">{t("feed.empty")}</p>
      ) : (
        <>
          {items.map((item) => (
            <KudoCard
              key={item.id}
              kudo={item}
              pending={pendingHeartIds.has(item.id)}
              onToggleHeart={onToggleHeart}
              onCopyLink={onCopyLink}
              onOpenProfile={onOpenProfile}
            />
          ))}

          {hasMore && <div ref={sentinelRef} aria-hidden="true" className="h-px w-full" />}

          {loading && <p className="text-center text-sm text-[#999999]">{t("feed.loadingMore")}</p>}

          {!hasMore && !loading && items.length > 0 && (
            <p className="text-center text-sm text-[#999999]">{t("feed.end")}</p>
          )}
        </>
      )}
    </div>
  );
}
