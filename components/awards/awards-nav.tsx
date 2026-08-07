"use client";

import { montserrat } from "@/components/ui/fonts";
import type { AwardContent } from "@/lib/content/awards";

import { MedalIcon } from "./award-icons";
import { useAwardsT } from "./use-awards-text";

export interface AwardsNavProps {
  awards: AwardContent[];
  activeSlug: string;
  onSelect: (slug: string) => void;
}

/**
 * Menu điều hướng trái — `mms_C_Menu list` (CSV item C, C.1–C.6). Mục đang
 * chọn tô màu vàng + gạch chân (CSV: "Active item shown with gold color and
 * underline indicator"). Bấm mục → cuộn tới thẻ tương ứng, KHÔNG đổi route —
 * `AwardsPage` tự quản lý cuộn + active state (xem `use-awards-scrollspy.ts`),
 * component này chỉ hiển thị + phát sự kiện chọn.
 *
 * **Sửa lỗi 3 (đo bằng MCP + browser thật của orchestrator):** menu trước đó
 * dính cuối luồng vì đứng trong `flex-row items-start` — về lý thuyết CSS
 * `sticky` + `items-start` đã đúng khuôn (item ngắn giữ kích thước tự nhiên,
 * containing block là cả hàng cao bằng cột thẻ dài), nhưng đo thật cho thấy
 * lệch. Chuyển hẳn sang CSS Grid (`grid-cols-[240px_1fr]`, cột cha đặt ở
 * `awards-page.tsx`) — khuôn "sticky sidebar cạnh nội dung dài" phổ biến và
 * chắc chắn hơn flex trong trường hợp này. `lg:self-start` thay `lg:shrink-0`:
 * grid item mặc định `stretch` theo chiều dọc, phải ép về kích thước tự nhiên
 * thì `sticky` mới có "quãng đường" để trôi theo khi cuộn.
 *
 * `top-6`: header không phải `fixed` (chỉ `absolute` phủ lên keyvisual lúc
 * đầu trang, cuộn xuống là trôi theo — xem `home-page.tsx`), nên không cần
 * chừa khoảng lớn để né header như những chỗ khác dùng `scroll-mt-28`.
 */
export function AwardsNav({ awards, activeSlug, onSelect }: AwardsNavProps) {
  const t = useAwardsT();

  return (
    <nav aria-label={t("nav.categoriesAria")} className={`${montserrat.className} flex flex-row gap-2 overflow-x-auto lg:sticky lg:top-6 lg:self-start lg:flex-col lg:gap-1 lg:overflow-visible`}>
      {awards.map((award) => {
        const active = award.slug === activeSlug;
        return (
          <button
            key={award.slug}
            type="button"
            onClick={() => onSelect(award.slug)}
            aria-current={active ? "true" : undefined}
            className={`flex shrink-0 items-center gap-3 border-b-2 px-2 py-3 text-left text-base leading-6 font-bold tracking-[0.15px] whitespace-nowrap transition-colors duration-200 ease-out lg:whitespace-normal ${
              active
                ? "border-[#FFEA9E] text-[#FFEA9E]"
                : "border-transparent text-white hover:text-[#FFEA9E]"
            }`}
          >
            <MedalIcon className="h-5 w-5 shrink-0" />
            {award.title}
          </button>
        );
      })}
    </nav>
  );
}
