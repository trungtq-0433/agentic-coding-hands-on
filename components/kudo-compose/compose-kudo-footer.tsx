"use client";

import { CloseIcon } from "@/components/ui/icons";
import { montserrat } from "@/components/ui/fonts";
import { useComposeText } from "./use-compose-text";

export interface ComposeKudoFooterProps {
  onCancel: () => void;
  onSubmit: () => void;
  /**
   * Chỉ là TRẠNG THÁI HIỂN THỊ (mờ + `aria-disabled`) — nút KHÔNG dùng thuộc
   * tính `disabled` gốc. Lý do: TC_7/50/51/52/56 đòi hỏi bấm "Gửi" khi thiếu
   * trường vẫn phải hiện lỗi từng trường ("Form không được submit" + lỗi
   * hiển thị), nhưng nút HTML `disabled` chặn sự kiện click hoàn toàn — nếu
   * dùng `disabled` thật thì không có click nào lọt tới để chạy validate và
   * hiện lỗi. Việc "chặn submit thật" nằm trong `handleSubmit` (luôn validate
   * trước khi gọi `onSubmit`), không nằm ở thuộc tính `disabled` của nút.
   */
  visuallyDisabled: boolean;
  submitting: boolean;
}

/** Footer (mms_H) — "Hủy" đóng modal không gửi gì; "Gửi" validate rồi mới gọi `onSubmit`. */
export function ComposeKudoFooter({ onCancel, onSubmit, visuallyDisabled, submitting }: ComposeKudoFooterProps) {
  const t = useComposeText();

  return (
    <div className={`${montserrat.className} flex justify-end gap-2`}>
      <button
        type="button"
        onClick={onCancel}
        className="flex items-center gap-2 rounded border border-[#998C5F] bg-[#FFEA9E]/10 px-10 py-4 text-base font-bold text-[#00101A]"
      >
        <CloseIcon className="h-6 w-6" />
        {t("footer.cancel")}
      </button>
      <button
        type="button"
        onClick={onSubmit}
        aria-disabled={visuallyDisabled}
        className={`flex items-center justify-center gap-2 rounded-lg px-10 py-4 text-[22px] font-bold text-[#00101A] ${
          visuallyDisabled || submitting ? "bg-[#FFEA9E]/50" : "bg-[#FFEA9E]"
        }`}
      >
        {t("footer.submit")}
      </button>
    </div>
  );
}
