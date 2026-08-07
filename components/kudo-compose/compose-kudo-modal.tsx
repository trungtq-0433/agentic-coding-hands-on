"use client";

import { useId } from "react";

import { ModalShell } from "@/components/ui/modal-shell";
import { montserrat } from "@/components/ui/fonts";
import { AnonymousCheckbox } from "./anonymous-checkbox";
import { ComposeKudoFooter } from "./compose-kudo-footer";
import { HashtagField } from "./hashtag-field";
import { ImageUploadField } from "./image-upload-field";
import { MessageField } from "./message-field";
import { RecipientField } from "./recipient-field";
import { useComposeKudoForm } from "./use-compose-kudo-form";
import { useComposeText } from "./use-compose-text";
import type { ComposeKudoModalProps } from "./compose-kudo-types";

/**
 * Modal "Viết Kudo" (mms_A → mms_H, ihQ26W78P2) — 26 spec item / 57 test case,
 * bọc trong `ModalShell` (phase-06) để thừa hưởng backdrop/Esc/focus-trap/
 * scroll-lock dùng chung, không tự dựng chrome.
 *
 * Không có route riêng — modal thuần, mọi dữ liệu (autocomplete người nhận,
 * upload ảnh thật, gửi thật) đến qua props; phase-16 nối `searchSunners` +
 * `onSubmit` thật. Track A: không import `lib/data|actions|supabase|realtime`.
 *
 * Thứ tự trường đúng ID-3: Người nhận → Textarea → Hashtag → Image →
 * Checkbox ẩn danh → footer Hủy/Gửi.
 */
export function ComposeKudoModal({
  open,
  onClose,
  onSubmit,
  searchSunners,
  hashtags,
  presetRecipient = null,
  submitting,
  errors,
}: ComposeKudoModalProps) {
  const t = useComposeText();
  const titleId = useId();
  const form = useComposeKudoForm({ open, presetRecipient, onSubmit, onClose });

  const recipientError = form.requiredErrors.recipient
    ? t("recipient.required")
    : (form.serverErrors.recipientId ?? errors.recipientId);
  const bodyError = form.requiredErrors.body ? t("message.required") : (form.serverErrors.body ?? errors.body);
  const hashtagError = form.requiredErrors.hashtag
    ? t("hashtag.required")
    : (form.serverErrors.hashtagIds ?? errors.hashtagIds);
  const imageError = form.serverErrors.images ?? errors.images;

  const isBusy = submitting || form.isSubmitting;

  return (
    <ModalShell open={open} onClose={onClose} labelledBy={titleId}>
      <div className={`${montserrat.className} flex w-[752px] max-w-[90vw] flex-col gap-6 rounded-3xl bg-[#FFF8E1] p-10`}>
        <h2 id={titleId} className="text-3xl leading-10 font-bold text-center text-[#00101A]">
          {t("modal.title")}
        </h2>

        <RecipientField value={form.recipient} onChange={form.setRecipient} searchSunners={searchSunners} errorMessage={recipientError} />

        <MessageField value={form.body} onChange={form.setBody} searchSunners={searchSunners} errorMessage={bodyError} />

        <HashtagField items={hashtags} value={form.hashtagIds} onChange={form.setHashtagIds} errorMessage={hashtagError} />

        <ImageUploadField value={form.images} onChange={form.setImages} errorMessage={imageError} />

        <AnonymousCheckbox checked={form.isAnonymous} onChange={form.setIsAnonymous} />

        {form.submitError && <p className="text-sm font-bold text-[#B3261E]">{t(form.submitError)}</p>}

        <ComposeKudoFooter
          onCancel={onClose}
          onSubmit={form.handleSubmit}
          visuallyDisabled={!form.canSubmit}
          submitting={isBusy}
        />
      </div>
    </ModalShell>
  );
}
