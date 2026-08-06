"use client";

import Image from "next/image";

import { montserrat } from "@/components/ui/fonts";
import { UserIcon } from "@/components/ui/icons";

/** Một dòng leaderboard "10 SUNNER NHẬN QUÀ MỚI NHẤT" (`D.3_`, node `2940:13510`). */
export interface LeaderboardEntry {
  id: string;
  name: string;
  avatarUrl: string | null;
  /**
   * Dòng phụ dưới tên — **chuỗi mô tả, KHÔNG phải con số**.
   *
   * Bản vẽ ghi nguyên văn `"Nhận được 1 áo phông SAA"` (node
   * `I2940:13516;256:7472`): nó nêu TÊN món quà chứ không chỉ số lượng, nên
   * không dựng lại được từ một `number` ghép vào mẫu câu cố định. Track B phải
   * trả về câu đã dựng sẵn. Bỏ trống thì ẩn dòng này.
   */
  note?: string;
}

export interface LeaderboardListProps {
  title: string;
  entries: LeaderboardEntry[];
  onSelect: (userId: string) => void;
}

/**
 * Danh sách leaderboard trong sidebar phải.
 *
 * Số đo Figma (`2940:13516` `D.3.2_Thông tin Sunner nhận quà`, 364×64): hàng
 * ngang `gap 8px` — avatar 64×64 bo tròn viền `1.869px #FFF`, rồi một cột
 * `gap 2px` gồm TÊN (Montserrat 700 `22px/28px`, `#FFEA9E`, canh trái) và GHI
 * CHÚ ngay dưới (`16px/24px` `ls .15`, trắng, **cũng canh trái** — xem ghi chú
 * tại chỗ). Hai dòng xếp CHỒNG — không phải tên-trái/giá-trị-phải cùng hàng.
 *
 * Tiêu đề thì CANH GIỮA và đúng như vậy trong bản vẽ (ảnh thiết kế cho hai
 * dòng "10 SUNNER NHẬN QUÀ" / "MỚI NHẤT" đều căn giữa) — không đổi.
 *
 * Khung ngoài: viền `#998C5F`, nền `#00070C`, `border-radius 17px`,
 * `padding 24px 16px 24px 24px`, tiêu đề canh giữa `22px/28px` `#FFEA9E`.
 *
 * **Bản vẽ chỉ có MỘT leaderboard.** Acceptance của phase-09 ghi "2 leaderboard"
 * — đã kiểm `2940:13488` và nó chỉ có 2 con: khối thống kê `D.1_` và khối này
 * `D.3_`. Đánh số nhảy `D.1` → `D.3` cho thấy từng có `D.2_` rồi bị xoá. Không
 * dựng khối thứ hai từ hư không; đã ghi vào clarifications để người soạn spec chốt.
 */
export function LeaderboardList({ title, entries, onSelect }: LeaderboardListProps) {
  if (entries.length === 0) return null;

  return (
    <div
      className={`${montserrat.className} flex w-full flex-col gap-4 rounded-[17px] border border-[#998C5F] bg-[#00070C] py-6 pl-6 pr-4`}
    >
      <h2 className="whitespace-pre-line text-center text-[22px] leading-[28px] font-bold text-[#FFEA9E]">
        {title}
      </h2>
      <ul className="flex flex-col divide-y divide-[#2E3940]">
        {/* Key ghép id + vị trí, KHÔNG dùng `entry.id` trần: đây là danh sách
            SỰ KIỆN nhận quà, mà một người hoàn toàn có thể nhận hai lần — id
            người sẽ lặp và React báo trùng key rồi bỏ bớt hàng. Cùng lớp lỗi đã
            gặp với `key={image.url}` ở `kudo-card.tsx`. */}
        {entries.map((entry, index) => (
          <li key={`${entry.id}-${index}`} className="py-4 first:pt-0 last:pb-0">
            <button
              type="button"
              onClick={() => onSelect(entry.id)}
              className="flex w-full items-center gap-2 rounded-lg text-left transition-colors duration-200 ease-out hover:bg-[#FFEA9E]/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFEA9E] motion-reduce:transition-none"
            >
              {entry.avatarUrl ? (
                <Image
                  src={entry.avatarUrl}
                  alt=""
                  width={64}
                  height={64}
                  className="h-16 w-16 shrink-0 rounded-full border-[1.869px] border-white object-cover"
                />
              ) : (
                <UserIcon
                  aria-hidden="true"
                  className="h-16 w-16 shrink-0 rounded-full border-[1.869px] border-white bg-[#2E3940] p-3 text-[#FFEA9E]"
                />
              )}
              <span className="flex min-w-0 flex-1 flex-col gap-0.5">
                <span className="truncate text-[22px] leading-7 font-bold text-[#FFEA9E]">
                  {entry.name}
                </span>
                {/* Canh TRÁI, cùng mép với tên. Figma khai `textAlign: right` ở
                    node `I2940:13516;256:7472` nhưng chính bản render của nó lại
                    cho hai dòng chung một mép trái — lại một lần thuộc tính khai
                    báo mâu thuẫn với hình vẽ, như `padding` của ô tìm kiếm
                    Spotlight và `gap` của carousel. */}
                {entry.note && (
                  <span className="truncate text-left text-base leading-6 font-bold tracking-[0.15px] text-white">
                    {entry.note}
                  </span>
                )}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
