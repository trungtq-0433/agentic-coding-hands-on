"use client";

import { useState } from "react";

import { CloseIcon, LightningIcon, PenIcon } from "./icons";
import { montserrat } from "./fonts";
import { useCommonUiT } from "./use-common-ui-text";

export interface KudosFabProps {
  onRules: () => void;
  onCompose: () => void;
}

/**
 * Nút nổi (FAB) — gộp 2 trạng thái Figma "FAB 1" (_hphd32jN2, thu gọn) và
 * "FAB 2" (Sv7DFwBw1h, mở rộng: "Thể lệ" + "Viết KUDOS" + nút đóng) thành 1
 * component, chuyển trạng thái bằng state cục bộ `expanded` (chốt trong
 * phase-06.md, không tách riêng 2 component).
 */
export function KudosFab({ onRules, onCompose }: KudosFabProps) {
  const t = useCommonUiT();
  const [expanded, setExpanded] = useState(false);

  if (!expanded) {
    return (
      <button
        type="button"
        onClick={() => setExpanded(true)}
        aria-label={t("kudosFab.toggleAria")}
        aria-expanded={false}
        className="fixed bottom-8 right-5 flex items-center gap-2 rounded-full bg-[#FFEA9E] px-4 py-4 shadow-[0_4px_4px_rgba(0,0,0,.25),0_0_6px_#FAE287]"
      >
        <PenIcon className="h-6 w-6 text-[#00101A]" />
        <span className={`${montserrat.className} w-[10px] text-2xl font-bold text-[#00101A]`}>/</span>
        <LightningIcon className="h-[18px] w-5 text-[#D4271D]" />
      </button>
    );
  }

  return (
    <div className={`${montserrat.className} fixed bottom-8 right-5 z-10 flex flex-col items-end gap-5`}>
      <button
        type="button"
        onClick={() => {
          onRules();
          setExpanded(false);
        }}
        className="flex items-center gap-2 rounded bg-[#FFEA9E] px-4 py-4 text-2xl font-bold leading-8 text-[#00101A]"
      >
        <LightningIcon className="h-[18px] w-5 text-[#D4271D]" />
        {t("kudosFab.rules")}
      </button>
      <button
        type="button"
        onClick={() => {
          onCompose();
          setExpanded(false);
        }}
        className="flex items-center gap-2 rounded bg-[#FFEA9E] px-4 py-4 text-2xl font-bold leading-8 text-[#00101A]"
      >
        <PenIcon className="h-6 w-6" />
        {t("kudosFab.compose")}
      </button>
      <button
        type="button"
        onClick={() => setExpanded(false)}
        aria-label={t("kudosFab.closeAria")}
        aria-expanded={true}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-[#D4271D]"
      >
        <CloseIcon className="h-6 w-6 text-white" />
      </button>
    </div>
  );
}
