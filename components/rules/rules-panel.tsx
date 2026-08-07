"use client";

import { useId } from "react";

import { ModalShell } from "@/components/ui/modal-shell";
import { CloseIcon, PenIcon } from "@/components/ui/icons";
import { montserrat } from "@/components/ui/fonts";
import { buildRulesContent, type RulesContent } from "@/lib/content/rules";
import { useRulesT } from "./use-rules-text";
import { HeroTierCard } from "./hero-tier-card";
import { SecretBoxBadge } from "./secret-box-badge";

export interface RulesPanelProps {
  open: boolean;
  onClose: () => void;
  /** Mở form Viết KUDOS — phase-16 nối modal thật (phase-10). Panel chỉ gọi callback rồi tự đóng. */
  onCompose: () => void;
  /** Mặc định lấy từ `lib/content/rules.ts`; cho phép override để test hoặc để phase-16 tái dùng. */
  content?: RulesContent;
}

/**
 * Panel "Thể lệ" (Figma `3204:6051`, frame "Thể lệ UPDATE") — bọc `ModalShell`
 * dùng chung của phase-06, KHÔNG tự dựng backdrop/Esc/scroll-lock (đã có sẵn ở
 * đó, `containerRef` của `ModalShell` tự `max-h-[90vh] overflow-auto` nên panel
 * cuộn được bên trong mà không cần thêm wrapper cuộn riêng — đúng yêu cầu
 * TC_THELE_FUN_001/002 "cuộn trong panel, không cuộn nền").
 *
 * Không dùng vị trí "docked bên phải" 553×1410 tuyệt đối như Figma (x887-1440
 * trên khung 1440): `ModalShell` luôn canh giữa modal, và một panel docked cứng
 * sẽ không hoạt động cùng chrome dùng chung của 3 phase modal song song
 * (10/13/15). Giữ width 553px (giới hạn `max-w-[90vw]` cho mobile), bỏ height
 * cố định — nội dung dài bao nhiêu thì panel cao bấy nhiêu, quá `90vh` thì
 * `ModalShell` tự cho cuộn.
 *
 * `border-radius: 0` và `background: #00070C` lấy đúng theo `get_node` (không
 * suy đoán) — panel này không bo góc, khác với các dialog sáng màu khác trong
 * codebase (`AddLinkDialog` dùng `#FFF8E1` bo `rounded-3xl`).
 */
export function RulesPanel({ open, onClose, onCompose, content }: RulesPanelProps) {
  const t = useRulesT();
  const titleId = useId();
  const resolved = content ?? buildRulesContent(t);

  function handleCompose() {
    onCompose();
    onClose();
  }

  return (
    <ModalShell open={open} onClose={onClose} labelledBy={titleId}>
      <div
        className={`${montserrat.className} flex w-[553px] max-w-[90vw] flex-col gap-6 bg-[#00070C] px-10 pt-6 pb-10`}
      >
        <h2 id={titleId} className="text-[45px] leading-[52px] font-bold text-[#FFEA9E]">
          {resolved.title}
        </h2>

        <section className="flex flex-col gap-4">
          <h3 className="text-[22px] leading-7 font-bold text-[#FFEA9E]">{resolved.heroSection.heading}</h3>
          <p className="text-base leading-6 font-bold tracking-[0.5px] text-white">
            {resolved.heroSection.description}
          </p>
          <div className="flex flex-col gap-6">
            {resolved.heroSection.tiers.map((tier) => (
              <HeroTierCard key={tier.key} tier={tier} />
            ))}
          </div>
        </section>

        <section className="flex flex-col gap-4">
          <h3 className="text-[22px] leading-7 font-bold text-[#FFEA9E]">{resolved.secretBoxSection.heading}</h3>
          <p className="text-base leading-6 font-bold tracking-[0.5px] text-white">
            {resolved.secretBoxSection.description}
          </p>
          {/* Figma dùng `justify-content: space-between` trong 1 hàng 377px rộng
              (xem clarifications.md — gap 16 khai báo không áp dụng thật). Grid 3
              cột co giãn theo bề ngang content thật (473px) đạt hiệu ứng tương
              đương mà không hard-code một bề ngang hàng cố định. */}
          <div className="grid grid-cols-3 justify-items-center gap-x-4 gap-y-6">
            {resolved.secretBoxSection.badges.map((badge) => (
              <SecretBoxBadge key={badge.code} badge={badge} />
            ))}
          </div>
          <p className="text-base leading-6 font-bold tracking-[0.5px] text-white">
            {resolved.secretBoxSection.closingText}
          </p>
          <h3 className="text-2xl leading-8 font-bold text-[#FFEA9E]">{resolved.secretBoxSection.nationalHeading}</h3>
          <p className="text-base leading-6 font-bold tracking-[0.5px] text-white">
            {resolved.secretBoxSection.nationalDescription}
          </p>
        </section>

        <div className="mt-2 flex gap-4">
          <button
            type="button"
            onClick={onClose}
            className="flex items-center gap-2 rounded border border-[#998C5F] bg-[#FFEA9E]/10 px-4 py-4 text-base font-bold whitespace-nowrap text-white transition-colors duration-200 ease-out hover:bg-[#FFEA9E]/20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFEA9E] motion-reduce:transition-none"
          >
            <CloseIcon className="h-6 w-6" />
            {resolved.closeLabel}
          </button>
          <button
            type="button"
            onClick={handleCompose}
            className="flex flex-1 items-center justify-center gap-2 rounded bg-[#FFEA9E] px-4 py-4 text-base font-bold text-[#00101A] transition-colors duration-200 ease-out hover:bg-[#FFF3C4] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#00101A] motion-reduce:transition-none"
          >
            <PenIcon className="h-6 w-6" />
            {resolved.composeLabel}
          </button>
        </div>
      </div>
    </ModalShell>
  );
}
