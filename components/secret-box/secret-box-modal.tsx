"use client";

import { useId } from "react";

import { ModalShell } from "@/components/ui/modal-shell";
import { CloseIcon } from "@/components/ui/icons";

import { SecretBoxIllustration } from "./secret-box-illustration";
import type { SecretBoxModalProps } from "./secret-box-types";
import { useSecretBoxT } from "./use-secret-box-text";

/**
 * Modal "Mở Secret Box" (phase-15), node gốc `1466:7676` (fileKey
 * `9ypp4enmFmdK3YAFJLIu6C`, screenId `J3-4YFIpMM`). Bọc trong `ModalShell`
 * dùng chung của phase-06 — không tự dựng backdrop/Esc/scroll-lock (đã có ở đó).
 *
 * **Đã chốt (2026-08-07): FIGMA là nguồn đúng, spec phải sửa theo.**
 *
 * Spec CSV và 19 test case mô tả trạng thái "MỞ SECRET BOX THÀNH CÔNG", nhưng
 * chính node mà spec trỏ tới lại mang nội dung khác. Truy vấn thẳng:
 *   `1466:7678` → character "KHÁM PHÁ SECRET BOX CỦA BẠN"
 *   `1466:7683` → character "Click vào box để mở"
 * và node ảnh tên `MM_MEDIA_box quà chưa mở`. Cả khung là trạng thái TRƯỚC khi
 * mở. Người chủ sản phẩm đã chốt lấy Figma; chữ trong `locales/{vi,en}/secret-box.json`
 * đã đổi theo đúng hai chuỗi trên.
 *
 * **Việc còn lại KHÔNG nằm ở code:** spec CSV và 19 test case vẫn đang mô tả
 * trạng thái thành công, nên chúng SAI so với quyết định này và cần người soạn
 * spec sửa — đáng chú ý là TC `a0cd2f27-…` ép cứng chuỗi tiêu đề cũ, nên nó sẽ
 * fail cho tới khi được cập nhật. Ngoài ra Figma còn 8 khung
 * `Open secret box- trạng thái Standby sau khi đã bấm` chưa được sync/spec —
 * nhiều khả năng đó mới là modal kết quả, và sẽ là một màn riêng.
 *
 * Không có node huy hiệu nào trong Figma của màn này (xem
 * `secret-box-illustration.tsx`) — huy hiệu nhận được hoàn toàn đến từ prop
 * `lastBadge` do server cấp.
 */
export function SecretBoxModal({
  open,
  onClose,
  onOpenBox,
  remaining,
  lastBadge,
  opening,
  errorCode,
}: SecretBoxModalProps) {
  const t = useSecretBoxT();
  const titleId = useId();

  return (
    <ModalShell open={open} onClose={onClose} labelledBy={titleId}>
      <div className="flex w-[min(92vw,651.55px)] flex-col items-center gap-4 rounded-[12.73px] bg-[#00101A] px-[12.73px] py-4 sm:gap-[22.28px] sm:py-[23.87px]">
        <div className="relative flex w-full items-center justify-center">
          <h2
            id={titleId}
            className="text-center text-[18px] font-bold text-[#FFEA9E] sm:text-[25.46px] sm:leading-[31.82px]"
          >
            {t("modal.title")}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label={t("modal.closeAria")}
            className="absolute right-0 text-white/70 transition-colors hover:text-white"
          >
            <CloseIcon className="h-[19px] w-[19px]" />
          </button>
        </div>

        <div className="h-px w-full bg-[#2E3940]" aria-hidden="true" />

        {errorCode === "NO_UNOPENED_BOX" ? (
          <p role="alert" className="text-center text-[11px] font-bold text-[#FFEA9E] sm:text-[12.73px]">
            {t("modal.outOfBoxes")}
          </p>
        ) : (
          remaining > 0 && (
            <p className="text-center text-[11px] font-bold text-white sm:text-[12.73px]">{t("modal.instruction")}</p>
          )
        )}

        <SecretBoxIllustration
          lastBadge={lastBadge}
          remaining={remaining}
          opening={opening}
          errorCode={errorCode}
          onOpenBox={onOpenBox}
        />

        <div className="h-px w-full bg-[#2E3940]" aria-hidden="true" />

        <div className="flex items-center gap-[6.36px]">
          <span className="text-[11px] font-bold text-white sm:text-[12.73px]">{t("modal.remainingLabel")}</span>
          <span className="text-[22px] font-bold text-[#FFEA9E] sm:text-[28.64px]">
            {String(Math.max(remaining, 0)).padStart(2, "0")}
          </span>
        </div>
      </div>
    </ModalShell>
  );
}
