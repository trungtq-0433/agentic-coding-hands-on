"use client";

import { useRef, useState } from "react";

import type { ComposeKudoDraft, ComposeKudoFieldErrors, ComposeKudoSubmitResult, Profile } from "./compose-kudo-types";

export interface UseComposeKudoFormOptions {
  open: boolean;
  presetRecipient?: Profile | null;
  onSubmit: (draft: ComposeKudoDraft) => Promise<ComposeKudoSubmitResult>;
  onClose: () => void;
}

interface RequiredErrors {
  recipient: boolean;
  body: boolean;
  hashtag: boolean;
}

const EMPTY_REQUIRED_ERRORS: RequiredErrors = { recipient: false, body: false, hashtag: false };

/**
 * State + luật submit của modal Viết Kudo — tách khỏi `compose-kudo-modal.tsx`
 * để file component không phình quá 200 dòng, và để logic validate/submit
 * test được độc lập với việc render.
 *
 * **Chốt chặn double-submit dùng `useRef`, KHÔNG dùng state** — cùng lý do đã
 * trả giá ở `use-heart-toggle.ts` (phase-09): 5 cú bấm trong cùng một tick
 * đều đọc closure cũ nếu chỉ kiểm bằng state, vì state chỉ cập nhật ở lần
 * render sau. Ref cập nhật đồng bộ nên cú bấm thứ 2 trở đi thấy ngay dấu vết
 * cú đầu.
 */
export function useComposeKudoForm({ open, presetRecipient, onSubmit, onClose }: UseComposeKudoFormOptions) {
  const [recipient, setRecipient] = useState<Profile | null>(presetRecipient ?? null);
  const [body, setBody] = useState("");
  const [hashtagIds, setHashtagIds] = useState<string[]>([]);
  const [images, setImages] = useState<File[]>([]);
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [requiredErrors, setRequiredErrors] = useState<RequiredErrors>(EMPTY_REQUIRED_ERRORS);
  const [serverErrors, setServerErrors] = useState<ComposeKudoFieldErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const submittingRef = useRef(false);

  // Đóng rồi mở lại modal → reset sạch form (đúng cách "adjust state khi prop
  // đổi" React khuyến nghị: điều chỉnh NGAY TRONG RENDER thay vì effect, cùng
  // kỹ thuật `AddLinkDialog` đã dùng — tránh cascading render).
  const [prevOpen, setPrevOpen] = useState(open);
  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open) {
      setRecipient(presetRecipient ?? null);
      setBody("");
      setHashtagIds([]);
      setImages([]);
      setIsAnonymous(false);
      setRequiredErrors(EMPTY_REQUIRED_ERRORS);
      setServerErrors({});
      setSubmitError(null);
    }
  }

  function validate(): RequiredErrors {
    return {
      recipient: recipient === null,
      body: body.trim().length === 0,
      hashtag: hashtagIds.length === 0,
    };
  }

  const canSubmit = recipient !== null && body.trim().length > 0 && hashtagIds.length > 0;

  /**
   * Luôn chạy validate trước, bất kể `canSubmit` — xem lý do ở
   * `compose-kudo-footer.tsx` (nút "Gửi" không dùng `disabled` gốc nên vẫn
   * nhận được click khi thiếu trường, và phải tự chặn tại đây).
   */
  function handleSubmit() {
    if (submittingRef.current) return; // đang có lời gọi bay — bỏ qua click thừa
    const errors = validate();
    setRequiredErrors(errors);
    if (errors.recipient || errors.body || errors.hashtag) return;

    submittingRef.current = true;
    setIsSubmitting(true);
    setSubmitError(null);

    const draft: ComposeKudoDraft = {
      recipientId: recipient!.id,
      body,
      hashtagIds,
      images,
      isAnonymous,
    };

    onSubmit(draft)
      .then((result) => {
        if (result.ok) {
          onClose();
          return;
        }
        setServerErrors(result.fieldErrors ?? {});
      })
      .catch((error: unknown) => {
        console.error("[kudo-compose] gửi kudo thất bại:", error);
        setSubmitError("footer.submitError");
      })
      .finally(() => {
        submittingRef.current = false;
        setIsSubmitting(false);
      });
  }

  return {
    recipient,
    setRecipient,
    body,
    setBody,
    hashtagIds,
    setHashtagIds,
    images,
    setImages,
    isAnonymous,
    setIsAnonymous,
    requiredErrors,
    serverErrors,
    submitError,
    canSubmit,
    isSubmitting,
    handleSubmit,
  };
}
