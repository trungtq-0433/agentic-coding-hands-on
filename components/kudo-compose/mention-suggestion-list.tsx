"use client";

import { useComposeText } from "./use-compose-text";
import type { Profile } from "./compose-kudo-types";

export interface MentionSuggestionListProps {
  results: Profile[];
  onSelect: (profile: Profile) => void;
}

/**
 * Danh sách gợi ý mention, neo dưới textarea.
 *
 * **Đơn giản hoá có chủ đích:** Figma không cho vị trí popup theo toạ độ con
 * trỏ (mention là ký hiệu "@"+tên trong text thuần, không phải rich-text
 * editor có API đo vị trí caret). `<textarea>` chuẩn không có cách nào lấy
 * toạ độ pixel của con trỏ — cần đo bằng div ẩn giả lập (mirror), một kỹ
 * thuật phức tạp ngoài phạm vi MVP. Neo cố định dưới textarea vẫn thoả đúng
 * yêu cầu Acceptance ("hiển thị danh sách gợi ý", "có thể chọn để mention").
 */
export function MentionSuggestionList({ results, onSelect }: MentionSuggestionListProps) {
  const t = useComposeText();

  if (results.length === 0) return null;

  return (
    <ul
      role="listbox"
      aria-label={t("message.mentionAria")}
      className="absolute z-20 mt-1 max-h-48 w-64 overflow-auto rounded-lg border border-[#998C5F] bg-[#00070C] p-1.5"
    >
      {results.map((profile) => (
        <li key={profile.id}>
          <button
            type="button"
            role="option"
            aria-selected={false}
            onClick={() => onSelect(profile)}
            className="w-full rounded px-4 py-2 text-left text-base font-bold text-white hover:bg-[#FFEA9E]/10"
          >
            {profile.name}
          </button>
        </li>
      ))}
    </ul>
  );
}
