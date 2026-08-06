"use client";

import type { ReactNode } from "react";

import { montserrat } from "@/components/ui/fonts";
import { FlameIcon, GiftIcon } from "./board-icons";
import { useBoardT } from "./use-board-text";
import { LeaderboardList, type LeaderboardEntry } from "./leaderboard-list";

export type { LeaderboardEntry };

/** 5 chỉ số tổng quan — khối `D.1_Thống kê tổng quat`, node `2940:13489`. */
export interface SidebarStats {
  receivedKudos: number;
  sentKudos: number;
  hearts: number;
  openedBoxes: number;
  unopenedBoxes: number;
}

export interface BoardSidebarProps {
  stats: SidebarStats;
  /**
   * Leaderboard "10 SUNNER NHẬN QUÀ MỚI NHẤT" (`D.3_`). Rỗng thì ẩn cả khối.
   *
   * **Chỉ có MỘT leaderboard.** Chữ ký ban đầu của tôi có thêm `topReceivers`
   * cho một khối thứ hai vì Acceptance phase-09 ghi "2 leaderboard" — nhưng
   * kiểm `2940:13488` thì sidebar chỉ có 2 con: khối thống kê `D.1_` và khối
   * này `D.3_`. Đánh số nhảy `D.1` → `D.3` cho thấy `D.2_` từng có rồi bị xoá.
   * Bỏ prop đó đi thay vì để một prop vĩnh viễn rỗng: giữ lại là code chết,
   * và dựng khối thứ hai từ hư không thì phải bịa cả tiêu đề lẫn dữ liệu.
   * Đã ghi vào clarifications cho người soạn spec chốt.
   */
  recentGiftReceivers: LeaderboardEntry[];
  onOpenBox: () => void;
  onOpenProfile: (userId: string) => void;
}

/**
 * Huy hiệu "x2" ở hàng Số tim (`3241:14931`, 34×40) — đánh dấu ngày đặc biệt
 * nhân đôi tim (`hearts.is_special_day_bonus`, clarifications gap #8).
 *
 * Nền huy hiệu trong bản vẽ là `image 35` — một NGỌN LỬA, không phải khối chữ
 * nhật đỏ như bản dựng trước tự đặt. Node không tải được nên hình được vẽ lại
 * ở `FlameIcon` (xem ghi chú màu ở đó).
 *
 * Chữ "x2" KHÔNG canh giữa hộp: node `3241:14933` nằm ở x1161→1188 y2685→2702
 * trong hộp x1158→1192 y2666→2706, tức lệch hẳn xuống nửa dưới (nằm trong bụng
 * ngọn lửa). Đặt tuyệt đối theo đúng toạ độ đó thay vì `items-center`, kèm kiểu
 * chữ đo được: 17.538px/23.385px, weight 700, trắng, viền đen 1.04px.
 */
function HeartBonusBadge({ label }: { label: string }) {
  return (
    <span aria-label={label} role="img" className="relative block h-10 w-[34px] shrink-0">
      <FlameIcon className="absolute inset-0 h-10 w-[34px]" />
      <span
        aria-hidden="true"
        className="absolute left-[3px] top-[19px] flex h-[17.654px] w-[27px] items-center justify-center text-[17.538px] leading-[23.385px] font-bold text-white"
        /* `paintOrder` là bắt buộc, không phải tinh chỉnh: mặc định
           `-webkit-text-stroke` vẽ viền ĐÈ LÊN phần tô, nên viền 1.04px ăn mất
           quá nửa nét chữ 17.5px và "x2" hiện ra xám nhợt thay vì trắng đặc như
           bản vẽ. Đảo thứ tự cho viền xuống dưới, chữ trắng nằm trên. */
        style={{ WebkitTextStroke: "1.04px #000", paintOrder: "stroke fill" }}
      >
        x2
      </span>
    </span>
  );
}

/**
 * Một hàng chỉ số: nhãn trái, con số Montserrat 700 32/40 vàng canh phải.
 *
 * `badge` DÍNH NGAY SAU NHÃN, không phải cạnh con số — chỉ hàng "Số tim" có
 * (`D.1.4_`). Số đo bản vẽ: hàng 898→1272, hộp nhãn kết thúc đúng 1158, huy
 * hiệu 1158→1192 (không hở), rồi cách 42px mới tới glyph "25" ở 1234→1270. Bản
 * trước gói huy hiệu chung nhóm với con số và cách nó `gap-2`, nên ngọn lửa bị
 * đẩy sang tận mép phải — lệch hẳn ~26px so với chỗ của nó.
 */
function StatRow({ label, value, badge }: { label: string; value: number; badge?: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4">
      {/* Nhãn 22px/28px theo bản vẽ (`3241:14885` và các node cùng cấp), KHÔNG
          phải `text-base` 16px như bản trước. Cỡ sai kéo theo hệ quả: hộp nhãn
          co lại còn 189px thay vì 260px, nên huy hiệu dính sau nó cũng đứng sai chỗ. */}
      <span className="flex min-w-0 items-center text-[22px] leading-7 font-bold text-white">
        <span className="truncate">{label}</span>
        {badge}
      </span>
      <span className="text-[32px] leading-[40px] font-bold text-[#FFEA9E]">{value}</span>
    </div>
  );
}

/**
 * Sidebar phải màn Live board — node `2940:13488` (`D_Thống menu phải`).
 *
 * Gồm khung "Thống kê tổng quát" (5 chỉ số + nút mở Secret Box) và leaderboard
 * "10 SUNNER NHẬN QUÀ MỚI NHẤT". Con số hiển thị ĐÚNG giá trị từ `stats`,
 * không tự cộng/trừ gì thêm — dữ liệu thật do phase-16 nối vào.
 *
 * **Chỉ một leaderboard trong bản vẽ:** query `2940:13488` chỉ ra 2 con —
 * `2940:13489` (khối thống kê) và `2940:13510` (`D.3_` leaderboard). Không có
 * `D.2_`. Acceptance phase-09 ghi "2 leaderboard" là sai so với bản vẽ; xem
 * ghi chú ở `leaderboard-list.tsx` và mục tương ứng trong `clarifications.md`.
 */
export function BoardSidebar({
  stats,
  recentGiftReceivers,
  onOpenBox,
  onOpenProfile,
}: BoardSidebarProps) {
  const t = useBoardT();
  const canOpenBox = stats.unopenedBoxes > 0;

  return (
    <aside className={`${montserrat.className} flex w-full max-w-[422px] flex-col gap-6`}>
      <div className="flex w-full flex-col gap-4 rounded-[17px] border border-[#998C5F] bg-[#00070C] p-6">
        <StatRow label={t("sidebar.receivedKudos")} value={stats.receivedKudos} />
        <StatRow label={t("sidebar.sentKudos")} value={stats.sentKudos} />
        <StatRow label={t("sidebar.hearts")} value={stats.hearts} badge={<HeartBonusBadge label={t("sidebar.heartBonusAria")} />} />
        <div className="h-px w-full bg-[#2E3940]" aria-hidden="true" />
        <StatRow label={t("sidebar.openedBoxes")} value={stats.openedBoxes} />
        <StatRow label={t("sidebar.unopenedBoxes")} value={stats.unopenedBoxes} />
        <button
          type="button"
          onClick={onOpenBox}
          disabled={!canOpenBox}
          aria-disabled={!canOpenBox}
          className={`flex h-[60px] w-full items-center justify-center gap-2 rounded-lg p-4 text-[22px] leading-7 font-bold transition-colors duration-200 ease-out motion-reduce:transition-none ${
            canOpenBox
              ? "bg-[#FFEA9E] text-black hover:bg-[#FAE287] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFEA9E]"
              : "cursor-not-allowed bg-[#2E3940] text-[#998C5F]"
          }`}
        >
          {/* Chữ TRƯỚC, icon SAU — `D.1.8_` xếp chữ ở 986→1152 rồi icon 24×24 ở
              1160→1184, cách 8px. Bản trước để icon đứng trước chữ. */}
          <span>{t("sidebar.openBox")}</span>
          <GiftIcon aria-hidden="true" className="h-6 w-6 shrink-0" />
        </button>
      </div>

      <LeaderboardList
        title={t("sidebar.recentReceiversTitle")}
        entries={recentGiftReceivers}
        onSelect={onOpenProfile}
      />
    </aside>
  );
}
