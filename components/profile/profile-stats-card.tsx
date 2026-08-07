"use client";

import { montserrat } from "@/components/ui/fonts";
import { useProfileT } from "./use-profile-text";
import type { ProfileStats } from "./profile-types";

export interface ProfileStatsCardProps {
  stats: ProfileStats;
  onOpenBox: () => void;
}

/**
 * Một hàng chỉ số: nhãn trắng 22px/700 trái, giá trị vàng 32px/700 phải — bản
 * sao có chủ đích của `StatRow` trong `components/board/board-sidebar.tsx`
 * (Track B chưa nối nên khối 5 chỉ số ở đây gần như GIỐNG HỆT sidebar Live
 * board). Không import được: `StatRow` là hàm nội bộ không export của file
 * `board-sidebar.tsx` (ownership phase-09), và `components/board/**` không phải
 * chỗ tôi được sửa để export nó ra. Trùng lặp nhỏ, có ghi chú, chấp nhận theo
 * đúng tiền lệ đã ghi trong `clarifications.md` ("Deviations" của phase-04→06).
 */
function StatRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="min-w-0 truncate text-[22px] leading-7 font-bold text-white">{label}</span>
      <span className="text-[32px] leading-[40px] font-bold text-[#FFEA9E]">{value}</span>
    </div>
  );
}

/**
 * Thẻ thống kê (`mms_B_Thống kê`, node `362:5073`) — CHỈ hiện trên profile của
 * chính mình (TC_WEB_PROFILE_GUI_004). Trên profile người khác, slot này được
 * `WriteKudoBar` thay thế toàn bộ (`profile-page.tsx` quyết định theo
 * `stats !== null`, xem `profile-types.ts`).
 *
 * Thứ tự đúng bản vẽ: nhận → gửi → tim → [đường kẻ] → đã mở → chưa mở → nút.
 * Hai dòng Secret Box LUÔN đọc 0 và nút LUÔN disabled — "Hero tier bỏ khỏi MVP"
 * không áp dụng ở đây, đây là quy tắc riêng "Secret Box đọc 0" (clarifications
 * gap #9, "Điểm riêng của màn này"). Bấm nút disabled không làm gì
 * (TC_WEB_PROFILE_GUI_005) — `disabled` trên `<button>` đã tự chặn `onClick`,
 * không cần logic thêm.
 */
export function ProfileStatsCard({ stats, onOpenBox }: ProfileStatsCardProps) {
  const t = useProfileT();
  const canOpenBox = stats.unopenedBoxes > 0;

  return (
    <div
      className={`${montserrat.className} flex w-full max-w-[422px] flex-col gap-4 rounded-[17px] border border-[#998C5F] bg-[#00070C] p-6`}
    >
      <StatRow label={t("stats.received")} value={stats.receivedKudos} />
      <StatRow label={t("stats.sent")} value={stats.sentKudos} />
      <StatRow label={t("stats.hearts")} value={stats.hearts} />
      <div className="h-px w-full bg-[#2E3940]" aria-hidden="true" />
      <StatRow label={t("stats.openedBoxes")} value={stats.openedBoxes} />
      <StatRow label={t("stats.unopenedBoxes")} value={stats.unopenedBoxes} />
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
        {t("stats.openBox")}
      </button>
    </div>
  );
}
