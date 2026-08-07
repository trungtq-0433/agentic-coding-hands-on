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
 * **Lệch giữa nội dung Figma sống và spec/test case/tiêu đề nhiệm vụ — đã chốt
 * dùng nguồn nào:** truy vấn MCP trực tiếp cho thấy node `1466:7678` hiện chữ
 * "KHÁM PHÁ SECRET BOX CỦA BẠN" (không phải "MỞ SECRET BOX THÀNH CÔNG"), node
 * `1466:7683` hiện "Click vào box để mở" (không phải "...để tiếp tục mở"), và
 * hộp minh họa tên `MM_MEDIA_box quà chưa mở` (= hộp CHƯA mở) — tức khung Figma
 * này thực chất là trạng thái TRƯỚC khi mở, không phải modal thành công. Ba
 * nguồn độc lập khác đều đồng nhất với trạng thái THÀNH CÔNG: spec CSV
 * (`spec-open-secret-box-J3-4YFIpMM`, mô tả rõ "'MỞ SECRET BOX THÀNH CÔNG'"),
 * 19 test case (`tc-open-secret-box-J3-4YFIpMM`, TC `a0cd2f27-…` khẳng định
 * "exact static text: 'MỞ SECRET BOX THÀNH CÔNG'"), và chính tiêu đề nhiệm vụ
 * được giao. Vì TC là hợp đồng hành vi bắt buộc (sai chữ tĩnh này = fail TC
 * `a0cd2f27`), đã chọn dùng CHỮ theo spec+TC+nhiệm vụ, còn HÌNH HỌC/MÀU/PHÔNG
 * (kích thước modal, bo góc, khoảng cách, font-size, màu vàng/trắng) lấy
 * nguyên từ node Figma sống — hai phần này không mâu thuẫn nhau. Cần người
 * soạn thiết kế xác nhận lại nội dung khung `J3-4YFIpMM` (đổi tên/nội dung để
 * khớp trạng thái "đã mở", hoặc bổ sung khung riêng cho trạng thái này).
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
