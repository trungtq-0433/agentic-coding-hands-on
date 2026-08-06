"use client";

import { useEffect, useRef, useState, type KeyboardEvent } from "react";

import { FilterDropdown } from "@/components/ui/filter-dropdown";
import { montserrat } from "@/components/ui/fonts";

import { ArrowLeftIcon, ArrowRightIcon } from "./board-icons";
import { KudoCard } from "./kudo-card";
import type { KudoCardData } from "./kudo-card-types";
import { NavOverlay } from "./carousel-nav";
import { SectionHeader } from "./section-header";
import { useBoardT } from "./use-board-text";

export interface FilterOption {
  value: string;
  label: string;
}


export interface HighlightCarouselProps {
  /** Danh sách thẻ Highlight (mm:2940:13461 `B.2_HIGHLIGHT KUDOS`). */
  items: KudoCardData[];
  hashtagOptions: FilterOption[];
  departmentOptions: FilterOption[];
  selectedHashtag: string | null;
  selectedDepartment: string | null;
  onFilterChange: (kind: "hashtag" | "department", value: string | null) => void;
  onOpenProfile: (userId: string) => void;
  onToggleHeart: (kudosId: number) => void;
  onCopyLink: (kudosId: number) => void;
  /** Id các kudo đang chờ server xác nhận thả tim — disable nút tim thẻ đó. */
  pendingHeartIds: ReadonlySet<number>;
}

/**
 * Carousel Highlight Kudos (mm:2940:13451, header mm:13452, track mm:13461).
 * Track đặt THẺ KUDO ĐẦY ĐỦ (`KudoCard variant="highlight"`), không phải thẻ
 * rút gọn như bản trước (đã xoá `highlight-slide.tsx`). Chiều cao track KHÔNG
 * ép cứng 525px — nội dung thẻ biến thiên thật, để `flex` tự giãn theo thẻ
 * cao nhất. Bung hết 1440 (không thụt lề) bằng margin âm khớp padding
 * `<main>` (`px-6 md:px-16 lg:px-36`); header/chỉ số trang đệm lại y hệt.
 */
export function HighlightCarousel({
  items,
  hashtagOptions,
  departmentOptions,
  selectedHashtag,
  selectedDepartment,
  onFilterChange,
  onOpenProfile,
  onToggleHeart,
  onCopyLink,
  pendingHeartIds,
}: HighlightCarouselProps) {
  const t = useBoardT();
  const trackRef = useRef<HTMLDivElement>(null);
  const [index, setIndex] = useState(0);
  const total = items.length;
  /**
   * Thẻ cuối cùng CÓ điểm dừng cuộn riêng. Bình thường bằng `total - 1` nhờ
   * khoảng đệm đuôi bên dưới; giữ là state để nếu trình duyệt không tính
   * `padding-inline-end` vào vùng cuộn thì nút vẫn tắt đúng lúc thay vì bấm
   * mãi không nhúc nhích.
   */
  const [maxIndex, setMaxIndex] = useState(() => Math.max(total - 1, 0));
  const isFirst = index <= 0;
  const isLast = index >= maxIndex;

  /**
   * Cả 5 thẻ phải tới được — bản vẽ ghi rõ "2/5" ở `B.5.2_số trang`.
   *
   * Không có khoảng đệm đuôi thì `maxScroll` chỉ tới 1296 trong khi thẻ 4 và 5
   * nằm ở 1656 và 2208: bấm "tiếp" lần 3 bị chặn ở 1296, `handleScroll` thấy
   * 1296 gần thẻ 1104 nhất nên kéo `index` ngược về 2, và từ đó nút "tiếp"
   * quay vòng vô ích — đúng cái "next không chính xác". Đệm đuôi đúng bằng
   * phần khung thừa ra sau một thẻ để thẻ cuối cũng lùi được về sát mép trái.
   */
  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;
    const sync = () => {
      const first = track.children[0] as HTMLElement | undefined;
      if (first) track.style.paddingInlineEnd = `${Math.max(0, track.clientWidth - first.offsetWidth)}px`;
      const maxScroll = track.scrollWidth - track.clientWidth;
      const cards = Array.from(track.children) as HTMLElement[];
      let last = 0;
      cards.forEach((card, i) => {
        if (card.offsetLeft <= maxScroll + 1) last = i;
      });
      setMaxIndex(last);
      setIndex((current) => Math.min(current, last));
    };
    sync();
    const observer = new ResizeObserver(sync);
    observer.observe(track);
    return () => observer.disconnect();
  }, [total]);

  function scrollToIndex(next: number) {
    const track = trackRef.current;
    const card = track?.children[next] as HTMLElement | undefined;
    if (!track || !card) return;
    // Chặn trên bằng `maxScroll`: nhắm quá mức thì trình duyệt tự cắt, và
    // `handleScroll` sau đó lại suy ra một `index` khác với ý định — vòng lặp.
    const maxScroll = track.scrollWidth - track.clientWidth;
    track.scrollTo({ left: Math.min(card.offsetLeft, maxScroll), behavior: "smooth" });
    setIndex(next);
  }

  const goPrev = () => !isFirst && scrollToIndex(index - 1);
  const goNext = () => !isLast && scrollToIndex(index + 1);

  /** Cuộn tay đồng bộ lại `index` để chỉ số trang + disable đúng thẻ đang xem. */
  function handleScroll() {
    const track = trackRef.current;
    if (!track) return;
    // Chỉ xét các thẻ thật sự có điểm dừng — thẻ ngoài tầm không bao giờ là
    // đáp án đúng, mà lại kéo `index` về sai chỗ.
    const cards = (Array.from(track.children) as HTMLElement[]).slice(0, maxIndex + 1);
    const distanceOf = (el: HTMLElement) => Math.abs(el.offsetLeft - track.scrollLeft);
    setIndex(cards.reduce((best, el, i) => (distanceOf(el) < distanceOf(cards[best]) ? i : best), 0));
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    if (event.key === "ArrowLeft") goPrev();
    else goNext();
  }

  const filters = (
    <>
      <FilterDropdown
        items={hashtagOptions}
        value={selectedHashtag}
        onChange={(value) => onFilterChange("hashtag", value)}
        placeholder={t("filter.hashtagPlaceholder")}
      />
      <FilterDropdown
        items={departmentOptions}
        value={selectedDepartment}
        onChange={(value) => onFilterChange("department", value)}
        placeholder={t("filter.departmentPlaceholder")}
      />
    </>
  );

  return (
    /* KHÔNG có `w-full` ở đây. `w-full` ghim bề rộng = 100% khung nội dung của
        `main` (1152px), nên `-mx-*` chỉ ĐẨY hộp sang trái 144px chứ không nới nó
        ra — đo được: section nằm ở 233→1385 trong khi phải là 233→1673. Bỏ
        `w-full` thì `width:auto` tự tính = 1152 + 144 + 144 = 1440, đúng bề ngang
        tràn lề mà bản vẽ yêu cầu cho carousel. */
      <section className="flex flex-col gap-4 -mx-6 md:-mx-16 lg:-mx-36">
      <div className="px-6 md:px-16 lg:px-36">
        <SectionHeader title={t("highlight.title")} slot={filters} />
      </div>

      <div
        role="group"
        aria-roledescription="carousel"
        aria-label={t("highlight.carouselAria")}
        tabIndex={0}
        onKeyDown={handleKeyDown}
        className="relative w-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFEA9E]"
      >
        <div
          ref={trackRef}
          onScroll={handleScroll}
          /* `snap-start` chứ KHÔNG `snap-center`: bản vẽ đặt thẻ đầu sát mép trái
             (x=0) và để thẻ thứ ba bị cắt ở mép phải — căn giữa thì thẻ đầu bị
             đẩy vào trong, chỉ còn thấy đúng một thẻ giữa hai lớp phủ 400px. */
          className="flex snap-x snap-mandatory gap-6 overflow-x-auto scroll-smooth [&::-webkit-scrollbar]:hidden"
          style={{ scrollbarWidth: "none" }}
        >
          {items.map((item) => (
            <div key={item.id} className="shrink-0 snap-start">
              <KudoCard
                variant="highlight"
                kudo={item}
                pending={pendingHeartIds.has(item.id)}
                onToggleHeart={onToggleHeart}
                onCopyLink={onCopyLink}
                onOpenProfile={onOpenProfile}
              />
            </div>
          ))}
        </div>
        <NavOverlay side="left" onClick={goPrev} disabled={isFirst} label={t("highlight.prevAria")}>
          <ArrowLeftIcon className="h-[60px] w-[60px]" />
        </NavOverlay>
        <NavOverlay side="right" onClick={goNext} disabled={isLast} label={t("highlight.nextAria")}>
          <ArrowRightIcon className="h-[60px] w-[60px]" />
        </NavOverlay>
      </div>

      {/* mm:2940:13471 `B.5_slide` — hàng chỉ số trang CÓ nút lùi/tiến RIÊNG
          (48×48, icon 28×28), tách khỏi cặp nút 80×80 nằm trên lớp phủ gradient.
          Bản trước chỉ render mỗi chữ nên thiếu hẳn `‹ ›`, và cỡ chữ dùng
          `text-sm` trong khi bản vẽ là 28px/36px màu `#999`. */}
      {total > 0 && (
        <div className="flex items-center justify-center gap-8 px-6 md:px-16 lg:px-36">
          <button
            type="button"
            onClick={goPrev}
            disabled={isFirst}
            aria-disabled={isFirst}
            aria-label={t("highlight.prevAria")}
            className="flex h-12 w-12 items-center justify-center rounded p-2.5 text-white transition-opacity duration-200 ease-out enabled:hover:text-[#FFEA9E] disabled:opacity-30 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFEA9E] motion-reduce:transition-none"
          >
            <ArrowLeftIcon className="h-7 w-7" />
          </button>
          <p
            aria-label={t("highlight.pageAria").replace("{current}", String(index + 1)).replace("{total}", String(total))}
            className={`${montserrat.className} text-[28px] leading-9 font-bold text-[#999999]`}
          >
            {index + 1}/{total}
          </p>
          <button
            type="button"
            onClick={goNext}
            disabled={isLast}
            aria-disabled={isLast}
            aria-label={t("highlight.nextAria")}
            className="flex h-12 w-12 items-center justify-center rounded p-2.5 text-white transition-opacity duration-200 ease-out enabled:hover:text-[#FFEA9E] disabled:opacity-30 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFEA9E] motion-reduce:transition-none"
          >
            <ArrowRightIcon className="h-7 w-7" />
          </button>
        </div>
      )}

    </section>
  );
}
