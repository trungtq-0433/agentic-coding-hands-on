"use client";

import { useId, useState } from "react";

import { CloseIcon, LinkIcon } from "./icons";
import { montserrat } from "./fonts";
import { ModalShell } from "./modal-shell";
import { useCommonUiT } from "./use-common-ui-text";

export interface AddLinkDialogErrors {
  text?: string;
  url?: string;
}

export interface AddLinkDialogProps {
  open: boolean;
  onCancel: () => void;
  onSave: (value: { text: string; url: string }) => void;
  errors?: AddLinkDialogErrors;
}

/**
 * Dialog "Thêm đường dẫn" (OyDLDuSGEa), dựng trên `ModalShell` để thừa
 * hưởng backdrop/Esc/focus-trap/scroll-lock dùng chung.
 *
 * Lỗi validate nhận NGUYÊN VĂN qua prop `errors` — component không tự kiểm
 * tra định dạng URL hay nội dung rỗng (Figma cũng không có trạng thái lỗi
 * để tham chiếu; logic validate thật thuộc phase-16).
 */
export function AddLinkDialog({ open, onCancel, onSave, errors }: AddLinkDialogProps) {
  const t = useCommonUiT();
  const titleId = useId();
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  // Theo dõi giá trị `open` của lần render trước để phát hiện thời điểm
  // CHUYỂN từ đóng → mở, rồi reset field NGAY TRONG RENDER (không phải trong
  // effect — đây là kỹ thuật React khuyến nghị cho "adjust state khi prop đổi",
  // tránh cascading render mà rule `react-hooks/set-state-in-effect` cảnh báo).
  // Không reset khi vẫn đang mở, để giữ dữ liệu người dùng gõ lúc bị lỗi
  // validate và cần sửa lại.
  const [prevOpen, setPrevOpen] = useState(open);
  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open) {
      setText("");
      setUrl("");
    }
  }

  return (
    <ModalShell open={open} onClose={onCancel} labelledBy={titleId}>
      <div className={`${montserrat.className} w-[752px] max-w-[90vw] rounded-3xl bg-[#FFF8E1] p-10`}>
        <h2 id={titleId} className="text-3xl font-bold leading-10 text-[#00101A]">
          {t("addLinkDialog.title")}
        </h2>
        <div className="mt-8 flex flex-col gap-4">
          <label className="flex flex-col gap-2">
            <span className="text-[22px] font-bold leading-7 text-[#00101A]">
              {t("addLinkDialog.contentLabel")}
            </span>
            <input
              value={text}
              onChange={(event) => setText(event.target.value)}
              aria-invalid={Boolean(errors?.text)}
              className="h-14 rounded-lg border border-[#998C5F] bg-white px-6 py-4"
            />
            {errors?.text && <span className="text-sm font-bold text-[#B3261E]">{errors.text}</span>}
          </label>
          <label className="flex flex-col gap-2">
            <span className="text-[22px] font-bold leading-7 text-[#00101A]">
              {t("addLinkDialog.urlLabel")}
            </span>
            <input
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              aria-invalid={Boolean(errors?.url)}
              className="h-14 rounded-lg border border-[#998C5F] bg-white px-6 py-4"
            />
            {errors?.url && <span className="text-sm font-bold text-[#B3261E]">{errors.url}</span>}
          </label>
        </div>
        <div className="mt-8 flex gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="flex items-center gap-2 rounded border border-[#998C5F] bg-[#FFEA9E]/10 px-10 py-4 text-base font-bold text-[#00101A]"
          >
            <CloseIcon className="h-6 w-6" />
            {t("addLinkDialog.cancel")}
          </button>
          <button
            type="button"
            onClick={() => onSave({ text, url })}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-[#FFEA9E] px-4 py-4 text-[22px] font-bold text-[#00101A]"
          >
            <LinkIcon className="h-6 w-6" />
            {t("addLinkDialog.save")}
          </button>
        </div>
      </div>
    </ModalShell>
  );
}
