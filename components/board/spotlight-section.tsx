"use client";

/**
 * Khối Spotlight màn `/kudos` — word-cloud tên Sunner nhận Kudos + tổng kudos +
 * ô tìm kiếm. Node Figma `2940:14174` (`B.7_Spotlight`, khung 1157×548) + con
 * `3007:17482` (tổng kudos), `2940:14833` (ô tìm), `3007:17479` (nút Pan/Zoom).
 *
 * **Dựng lại lần 2 (2026-08-06):** bản đầu đặt tổng-kudos/ô-tìm NGOÀI panel
 * với cỡ chữ/màu suy đoán sai (chưa tra được Figma). Số đo dưới quy về gốc
 * panel (142, 1658): vị trí dùng % (nhất quán `leftPct`/`topPct` word-cloud),
 * kích thước/kiểu chữ giữ px tuyệt đối như bản vẽ. Ba lớp nền hoạ tiết KHÔNG
 * lấy được — thiếu tiền tố `MM_MEDIA_` nên ngoài pipeline asset MoMorph (lỗi
 * 500, cùng lỗi phase-07) — giữ nền đặc, không bịa. Bố cục word-cloud +
 * ticker ở `./spotlight-layout.ts`, pan/zoom ở `./use-pan-zoom.ts`.
 */

import Image from "next/image";
import { useMemo, useState } from "react";
import type { ChangeEvent } from "react";

import { montserrat } from "@/components/ui/fonts";
import { ExpandIcon, SearchIcon } from "./board-icons";
import { useBoardT } from "./use-board-text";
import { computeLayout, computeTickerLayout } from "./spotlight-layout";
import { usePanZoom } from "./use-pan-zoom";

export interface SpotlightName {
  id: string;
  name: string;
  /** Trọng số để quyết cỡ chữ trong word-cloud (số kudos nhận được). */
  weight: number;
}

export interface SpotlightTicker {
  id: string;
  /** Câu đã dựng sẵn, vd "08:30PM ... đã nhận được một Kudos mới". */
  text: string;
}

export interface SpotlightSectionProps {
  totalKudos: number;
  names: SpotlightName[];
  ticker: SpotlightTicker[];
  onSelectName: (id: string) => void;
}

export function SpotlightSection({ totalKudos, names, ticker, onSelectName }: SpotlightSectionProps) {
  const t = useBoardT();
  const [query, setQuery] = useState("");
  const {
    canvasRef,
    transform,
    transitionClass,
    handlePointerDown,
    handlePointerMove,
    handlePointerUp,
    handleKeyDown,
    wasDragged,
    cycleZoom,
  } = usePanZoom();

  const layout = useMemo(() => computeLayout(names), [names]);
  const tickerLayout = useMemo(() => computeTickerLayout(ticker), [ticker]);

  const normalizedQuery = query.trim().toLowerCase();
  const matchedIds = useMemo(() => {
    if (!normalizedQuery) return null;
    const set = new Set<string>();
    for (const n of names) {
      if (n.name.toLowerCase().includes(normalizedQuery)) set.add(n.id);
    }
    return set;
  }, [normalizedQuery, names]);

  function handleSelectName(id: string) {
    // Vừa kéo pan xong thì bỏ qua click "dính theo" — tránh mở nhầm chi tiết.
    if (wasDragged()) return;
    onSelectName(id);
  }

  return (
    <section className={`${montserrat.className} mx-auto flex w-full max-w-[1152px] flex-col gap-4`}>
      <div
        ref={canvasRef}
        role="group"
        aria-label={t("spotlight.canvasAria")}
        tabIndex={0}
        /* Panel `B.7_Spotlight`: 1157×548, viền `1px #998C5F` ĐẶC, bo `47.14px`.
           `overflow-hidden` CẢ HAI trục — thiếu 1 trục thì trục kia hoá `auto`. */
        className="relative aspect-[1157/548] w-full touch-none select-none overflow-hidden rounded-[47.14px] border border-[#998C5F] bg-[#00101A]"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
        onKeyDown={handleKeyDown}
      >
        {/* Ba lớp nền của bản vẽ (`image 24`, `image 25`, `Root further mo rong
            1` — node `2940:14178/14181/14173`) KHÔNG tải được qua MoMorph: bản
            đồ media lọc theo tiền tố `MM_MEDIA_` nên chúng bị loại từ gốc, và
            `get_figma_image` trả 500, `get_media_file` trả 401.

            **Ảnh này TÁCH TỪ ẢNH RENDER CỦA BẢN VẼ, không phải asset gốc.**
            Cắt đúng khung panel (142,1658 → 1157×548, tỉ lệ 1:1 nên không nội
            suy), rồi xoá lớp chữ bằng cách mask nét sáng trong đúng bbox của
            111 node chữ + tiêu đề + ô tìm kiếm + icon pan-zoom, và lấp lại bằng
            khuếch tán Jacobi 4 lân cận. Kết quả sạch nhưng vẫn là bản dựng lại:
            **thay bằng file gốc khi thiết kế đổi tên 3 node thành `MM_MEDIA_*`
            rồi sync lại.** Giữ `bg-[#00101A]` làm nền lót để không loé sáng
            trước khi ảnh tải xong. */}
        <Image
          src="/board/spotlight-background.webp"
          alt=""
          aria-hidden="true"
          fill
          /* `unoptimized`: file đã là WebP 36K đúng bằng 1157×548 của panel.
             Để Next tối ưu thì nó tái mã hoá xuống 1110px rồi trình duyệt phóng
             ngược lên 1150 — vừa thừa một vòng xử lý vừa mất nét. */
          unoptimized
          sizes="(max-width: 1152px) 100vw, 1152px"
          className="pointer-events-none select-none object-cover"
        />
        {/* Tổng kudos (`3007:17482`): tâm chữ = tâm panel ngang → full-width + canh giữa.
            `z-10` để nổi trên lớp word-cloud — xem ghi chú z-index ở ô tìm kiếm. */}
        <p className="pointer-events-none absolute inset-x-0 top-[2.55%] z-10 text-center text-[36px] font-bold leading-[44px] text-white">
          {totalKudos} {t("spotlight.kudosUnit")}
        </p>

        {/* Ô tìm kiếm (`2940:14833`), góc trên-trái panel. `stopPropagation`
            tránh gõ/chọn chữ bị đọc nhầm thành kéo-pan. Padding suy ngược
            Figma khai `padding: 16.378px 10.919px` nhưng con số đó tự mâu thuẫn
            với chính chiều cao 39px của ô: nội dung cao 17px + 2×16.378 = 49.8px,
            tràn ra ngoài. Lấy padding THẬT từ toạ độ tuyệt đối thay vì tin thuộc
            tính — ô ở x167→386 y1684→1723, nội dung ở x177→257 y1695→1712:
            trái 10px, trên 11px, dưới 11px. Tức padding ≈ 10–11px đều, không
            phải 16.378. (Cùng kiểu Figma khai padding không khớp bố cục đã gặp ở
            `Frame 486` trang chủ phase-08.) */}
        {/* `z-20` là thứ làm ô này BẤM ĐƯỢC, không phải trang trí. Lớp word-cloud
            bên dưới cũng `absolute inset-0` và đứng SAU trong DOM, nên khi cả hai
            cùng `z-index: auto` thì nó phủ kín ô tìm kiếm và nuốt sạch sự kiện
            chuột — Playwright báo thẳng: "div.absolute.inset-0 … intercepts
            pointer events". Gõ được bằng bàn phím (lọc vẫn chạy) nhưng không thể
            click vào ô, nên nhìn ra là "không search được". */}
        <div
          onPointerDown={(e) => e.stopPropagation()}
          className="absolute left-[2.16%] top-[4.74%] z-20 flex h-[39px] w-[219px] items-center gap-[10.92px] rounded-[46.404px] border-[0.682px] border-[#998C5F] bg-[rgba(255,234,158,0.10)] px-[10px] py-[11px]"
        >
          <span className="sr-only">{t("spotlight.searchLabel")}</span>
          <SearchIcon focusable="false" className="h-4 w-4 shrink-0 text-white" />
          <input
            type="text"
            value={query}
            maxLength={100}
            placeholder={t("spotlight.searchPlaceholder")}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)}
            className="w-full bg-transparent text-center text-[10.918px] font-medium leading-[16.378px] tracking-[0.102px] text-white placeholder:text-white outline-none"
          />
        </div>

        {layout.length === 0 && tickerLayout.length === 0 ? (
          <p className="absolute inset-0 flex items-center justify-center px-4 text-center text-sm text-white/60">
            {t("spotlight.empty")}
          </p>
        ) : (
          <div
            className={`absolute inset-0 ${transitionClass}`}
            style={{
              transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
              transformOrigin: "center center",
            }}
          >
            {layout.map((n) => {
              const isMatch = matchedIds === null || matchedIds.has(n.id);
              return (
                <button
                  key={n.id}
                  type="button"
                  onClick={() => handleSelectName(n.id)}
                  style={{
                    left: `${n.leftPct}%`,
                    top: `${n.topPct}%`,
                    fontSize: `${n.fontSize}px`,
                    lineHeight: `${n.lineHeight}px`,
                  }}
                  /* Ba trạng thái màu, theo thứ tự ưu tiên: đang lọc và khớp →
                     vàng `#FFEA9E`; tên nhấn của bản vẽ → `#F17676` (xem
                     `LayoutName.accent`); còn lại → trắng. Khi đang lọc thì màu
                     nhấn nhường chỗ cho màu khớp, nếu không người dùng không
                     phân biệt được cái nào là kết quả tìm. */
                  className={`absolute -translate-x-1/2 -translate-y-1/2 whitespace-nowrap text-center font-bold tracking-[0.208px] outline-none transition-opacity focus-visible:ring-2 focus-visible:ring-[#FFEA9E] ${
                    matchedIds !== null && isMatch
                      ? "text-[#FFEA9E]"
                      : n.accent
                        ? "text-[#F17676]"
                        : "text-white"
                  } ${isMatch ? "opacity-100" : "opacity-30"}`}
                >
                  {n.name}
                </button>
              );
            })}
          </div>
        )}

        {/* Ticker Kudos-mới — CỘT dưới-trái, nhạt dần lên trên (toạ độ + dải mờ
            trong `computeTickerLayout`). Đặt NGOÀI lớp pan/zoom: đây là luồng
            thông báo, không phải một phần của word-cloud, nên nó phải đứng yên
            khi người dùng kéo bảng. Nội dung cho trình đọc màn hình ở `sr-only`
            bên dưới, nên ở đây `aria-hidden`. */}
        {tickerLayout.map((item) => (
          <span
            key={item.id}
            aria-hidden="true"
            style={{ left: `${item.leftPct}%`, top: `${item.topPct}%`, opacity: item.opacity }}
            className="pointer-events-none absolute z-10 whitespace-nowrap text-[14px] font-bold leading-[20px] tracking-[0.1px] text-white"
          >
            {item.text}
          </span>
        ))}

        {/* `B.7.2_Pan zoom` (`3007:17479`): ĐÚNG MỘT control 30×30 ở góc
            DƯỚI-phải (L 94.1%, T 85.9% quy về gốc panel). Bản trước tự đặt cặp
            nút tròn `+`/`−` ở góc TRÊN-phải — sai cả vị trí, số lượng lẫn hình.
            Zoom ra từng nấc không mất: cuộn chuột và phím `-` vẫn xử lý. */}
        <button
          type="button"
          onClick={cycleZoom}
          onPointerDown={(e) => e.stopPropagation()}
          aria-label={t("spotlight.panZoomAria")}
          className="absolute left-[94.1%] top-[85.9%] z-20 h-[30px] w-[30px] text-white outline-none transition-opacity duration-200 ease-out hover:opacity-70 focus-visible:ring-2 focus-visible:ring-[#FFEA9E] motion-reduce:transition-none"
        >
          <ExpandIcon className="h-[30px] w-[30px]" />
        </button>
      </div>

      {/* Hiển thị chỉ là chữ mờ 10% chìm trong cloud — giữ a11y qua `sr-only`
          (tái dùng key `spotlight.tickerAria` sẵn có) thay vì bỏ tính năng. */}
      {ticker.length > 0 && (
        <ul aria-label={t("spotlight.tickerAria")} className="sr-only">
          {ticker.map((item) => (
            <li key={item.id}>{item.text}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
