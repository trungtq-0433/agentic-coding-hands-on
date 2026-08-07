"use client";

import { useEffect, useRef } from "react";

import { KudoCard } from "@/components/board/kudo-card";
import type { KudoCardData } from "@/components/board/kudo-card-types";
import { montserrat } from "@/components/ui/fonts";
import { useProfileT } from "./use-profile-text";

export interface ProfileKudosFeedProps {
  items: KudoCardData[];
  /** Thông báo trống RIÊNG theo hướng đang xem (TC_WEB_PROFILE_FUN_012) — khác `KudosFeed` của board vốn chỉ có một chuỗi trống chung. */
  emptyMessage: string;
  onLoadMore: () => void;
  hasMore: boolean;
  loading: boolean;
  pendingHeartIds: ReadonlySet<number>;
  onToggleHeart: (kudosId: number) => void;
  onCopyLink: (kudosId: number) => void;
  onOpenProfile: (userId: string) => void;
}

/**
 * Cuộn vô hạn cho feed KUDOS của Profile — **dựng riêng, không import
 * `components/board/kudos-feed.tsx`**: file đó gọi cứng `t("feed.empty")` từ
 * namespace `board` (một chuỗi trống DUY NHẤT cho mọi hướng), trong khi
 * TC_WEB_PROFILE_FUN_012 đòi hai thông báo trống KHÁC NHAU cho "Đã nhận" và
 * "Đã gửi" — không có prop nào để override, và sửa file đó là ra ngoài ownership
 * phase này (`components/board/**`). Thẻ bên trong vẫn dùng lại NGUYÊN `KudoCard`
 * (TC_WEB_PROFILE_GUI_006) — chỉ phần khung cuộn/trống là bản riêng.
 *
 * Cơ chế `IntersectionObserver` + ref hoá `loading`/`onLoadMore` chép lại đúng
 * kỹ thuật của `kudos-feed.tsx` (đã kiểm ở phase-09): tránh huỷ/dựng lại
 * observer mỗi khi `loading` đổi, tránh gọi `onLoadMore` chồng lấp lúc cuộn nhanh.
 */
export function ProfileKudosFeed({
  items,
  emptyMessage,
  onLoadMore,
  hasMore,
  loading,
  pendingHeartIds,
  onToggleHeart,
  onCopyLink,
  onOpenProfile,
}: ProfileKudosFeedProps) {
  const t = useProfileT();
  const sentinelRef = useRef<HTMLDivElement | null>(null);

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
      {isEmpty ? (
        <p className="py-10 text-center text-base text-[#00101A]">{emptyMessage}</p>
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
