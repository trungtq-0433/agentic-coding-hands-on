"use client";

import { LinkIcon } from "@/components/ui/icons";
import { NumberedListIcon, QuoteIcon } from "./compose-icons";
import { useComposeText } from "./use-compose-text";

export interface RichTextToolbarProps {
  onBold: () => void;
  onItalic: () => void;
  onStroke: () => void;
  onNumberedList: () => void;
  onQuote: () => void;
  onLink: () => void;
}

/** Nút toolbar dùng chung — cùng kích thước/hover cho cả 6 nút (mms_C.1 → C.6). */
function ToolbarButton({ label, onClick, children }: { label: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      className="flex h-9 w-9 items-center justify-center rounded text-[#00101A] hover:bg-[#FFEA9E]/40"
    >
      {children}
    </button>
  );
}

/**
 * Toolbar định dạng (mms_C) — bold/italic/stroke là CHỮ CÁI "B"/"I"/"S" theo
 * đúng spec (không phải icon hình vẽ), 3 nút còn lại là icon. Mỗi click áp
 * định dạng lên vùng đang chọn trong textarea (xử lý ở `message-field.tsx`,
 * component này chỉ phát sự kiện — không giữ state, không biết vị trí con trỏ).
 */
export function RichTextToolbar({ onBold, onItalic, onStroke, onNumberedList, onQuote, onLink }: RichTextToolbarProps) {
  const t = useComposeText();

  return (
    <div className="flex items-center gap-1 border-b border-[#FFEA9E] pb-2">
      <ToolbarButton label={t("toolbar.boldAria")} onClick={onBold}>
        <span className="text-base font-bold">{t("toolbar.boldLabel")}</span>
      </ToolbarButton>
      <ToolbarButton label={t("toolbar.italicAria")} onClick={onItalic}>
        <span className="text-base font-bold italic">{t("toolbar.italicLabel")}</span>
      </ToolbarButton>
      <ToolbarButton label={t("toolbar.strokeAria")} onClick={onStroke}>
        <span className="text-base font-bold line-through">{t("toolbar.strokeLabel")}</span>
      </ToolbarButton>
      <ToolbarButton label={t("toolbar.numberAria")} onClick={onNumberedList}>
        <NumberedListIcon className="h-5 w-5" />
      </ToolbarButton>
      <ToolbarButton label={t("toolbar.linkAria")} onClick={onLink}>
        <LinkIcon className="h-5 w-5" />
      </ToolbarButton>
      <ToolbarButton label={t("toolbar.quoteAria")} onClick={onQuote}>
        <QuoteIcon className="h-5 w-5" />
      </ToolbarButton>
    </div>
  );
}
