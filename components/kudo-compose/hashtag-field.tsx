"use client";

import { CloseIcon } from "@/components/ui/icons";
import { montserrat } from "@/components/ui/fonts";
import { MultiHashtagPicker, type HashtagItem } from "@/components/ui/multi-hashtag-picker";
import { useComposeText } from "./use-compose-text";

const MAX_HASHTAGS = 5;

export interface HashtagFieldProps {
  items: HashtagItem[];
  value: string[];
  onChange: (value: string[]) => void;
  errorMessage?: string;
}

/**
 * Trường "Hashtag" (mms_E) — dùng lại `MultiHashtagPicker` (phase-06) cho
 * dropdown chọn, tự vẽ THÊM hàng chip bên dưới vì picker chỉ đánh dấu "đã
 * chọn" bên trong danh sách, không tự hiện chip rời (TC_34-36 cần xoá từng
 * hashtag bằng nút "x" trên chip, không phải mở lại dropdown).
 *
 * Hint "Tối đa 5" chuyển màu đỏ khi đã chọn đủ 5 — thay cho việc bắt sự kiện
 * click vào item đã bị disable (nút disable thì không bắn `onClick`, nên
 * không thể chỉ hiện lỗi "lúc bấm thử item thứ 6").
 *
 * **Không tự thêm "#" ở đây.** `hashtagIds`/`value` (ID lưu trữ) luôn TRẦN,
 * nhưng `item.label` (chuỗi HIỂN THỊ do trang cha truyền vào) đã có sẵn "#"
 * theo đúng quy ước đang dùng ở `board-page-client.tsx`
 * (`{ value: "dedicated", label: "#Dedicated" }`) — `MultiHashtagPicker` render
 * `item.label` y nguyên. Tự thêm "#" ở component này sẽ tái diễn đúng lỗi
 * `##Dedicated` đã ghi trong clarifications (lưu kèm "#" ở TẦNG DỮ LIỆU mới
 * là lỗi; đây chỉ là hiển thị lại `label` đã có sẵn "#", không phải lưu trữ).
 */
export function HashtagField({ items, value, onChange, errorMessage }: HashtagFieldProps) {
  const t = useComposeText();
  const reachedMax = value.length >= MAX_HASHTAGS;
  const labelByValue = new Map(items.map((item) => [item.value, item.label] as const));

  function remove(tagValue: string) {
    onChange(value.filter((v) => v !== tagValue));
  }

  return (
    <div className={`${montserrat.className} flex flex-col gap-2`}>
      <div className="flex items-center gap-4">
        <span className="text-[22px] font-bold text-[#00101A]">
          {t("hashtag.label")} <span className="text-[#B3261E]">*</span>
        </span>
        <MultiHashtagPicker items={items} value={value} onChange={onChange} max={MAX_HASHTAGS} />
        <span className={`text-sm font-bold ${reachedMax ? "text-[#B3261E]" : "text-[#999999]"}`}>
          {reachedMax ? t("hashtag.maxReached") : t("hashtag.maxHint")}
        </span>
      </div>
      {value.length > 0 && (
        <ul className="flex flex-wrap gap-2">
          {value.map((tagValue) => (
            <li
              key={tagValue}
              className="flex items-center gap-2 rounded-full border border-[#998C5F] bg-[#FFEA9E]/40 px-3 py-1 text-sm font-bold text-[#00101A]"
            >
              {labelByValue.get(tagValue) ?? tagValue}
              <button
                type="button"
                onClick={() => remove(tagValue)}
                aria-label={t("hashtag.removeAria").replace("{label}", labelByValue.get(tagValue) ?? tagValue)}
              >
                <CloseIcon className="h-3.5 w-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}
      {errorMessage && <span className="text-sm font-bold text-[#B3261E]">{errorMessage}</span>}
    </div>
  );
}
