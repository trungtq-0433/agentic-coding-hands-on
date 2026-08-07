"use client";

import { useRef, useState } from "react";

import { AddLinkDialog } from "@/components/ui/add-link-dialog";
import { montserrat } from "@/components/ui/fonts";
import { MentionSuggestionList } from "./mention-suggestion-list";
import { RichTextToolbar } from "./rich-text-toolbar";
import { useComposeText } from "./use-compose-text";
import { useMentionSuggestions } from "./use-mention-suggestions";
import {
  insertMention,
  replaceRange,
  toggleBold,
  toggleItalic,
  toggleNumberedList,
  toggleQuote,
  toggleStroke,
  type FormatResult,
  type SelectionRange,
} from "./rich-text-formatting";
import type { Profile } from "./compose-kudo-types";

export interface MessageFieldProps {
  value: string;
  onChange: (value: string) => void;
  searchSunners: (query: string) => Promise<Profile[]>;
  errorMessage?: string;
}

/**
 * Trường "Trường nhập văn bản" (mms_D) — toolbar định dạng + textarea +
 * gợi ý mention + hint. Đọc/ghi selection trực tiếp trên DOM textarea (không
 * có state React nào cho vị trí con trỏ — `selectionStart/End` là nguồn thật
 * duy nhất), nên mọi thao tác định dạng phải diễn ra trong sự kiện đồng bộ
 * (click nút) để không mất selection.
 */
export function MessageField({ value, onChange, searchSunners, errorMessage }: MessageFieldProps) {
  const t = useComposeText();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [cursor, setCursor] = useState(0);
  const [linkDialogOpen, setLinkDialogOpen] = useState(false);
  /** Selection lưu lại NGAY TRƯỚC khi mở AddLinkDialog — dialog cướp focus khỏi textarea nên phải nhớ trước. */
  const savedSelectionRef = useRef<SelectionRange>({ start: 0, end: 0 });

  const { mention } = useMentionSuggestions(value, cursor, searchSunners);

  function currentSelection(): SelectionRange {
    const el = textareaRef.current;
    if (!el) return { start: value.length, end: value.length };
    return { start: el.selectionStart ?? value.length, end: el.selectionEnd ?? value.length };
  }

  /**
   * Áp kết quả format: cập nhật `value` rồi đặt lại selection đúng chỗ ở lần
   * render kế (textarea vừa nhận value mới). Cũng cập nhật NGAY state
   * `cursor` — thao tác trên DOM qua `setSelectionRange` không tự bắn sự kiện
   * `onClick`/`onKeyUp`, nên nếu không cập nhật ở đây, `cursor` state (dùng
   * để phát hiện mention đang gõ) sẽ giữ giá trị CŨ một nhịp và có thể vẫn
   * trỏ vào giữa đoạn "@Tên " vừa chèn, mở lại gợi ý mention sai chỗ.
   */
  function applyFormat(result: FormatResult) {
    onChange(result.value);
    setCursor(result.range.start);
    requestAnimationFrame(() => {
      textareaRef.current?.setSelectionRange(result.range.start, result.range.end);
      textareaRef.current?.focus();
    });
  }

  function handleLinkSave({ text, url }: { text: string; url: string }) {
    const label = text.trim().length > 0 ? text : url;
    applyFormat(replaceRange(value, savedSelectionRef.current, `[${label}](${url})`));
    setLinkDialogOpen(false);
  }

  function selectMention(profile: Profile) {
    if (!mention) return;
    applyFormat(insertMention(value, mention.mentionStart, mention.query.length, profile.name));
  }

  return (
    <div className={`${montserrat.className} flex flex-col gap-1`}>
      <div
        className={`rounded-lg border bg-white px-4 pt-2 pb-4 ${errorMessage ? "border-[#B3261E]" : "border-[#998C5F]"}`}
      >
        <RichTextToolbar
          onBold={() => applyFormat(toggleBold(value, currentSelection()))}
          onItalic={() => applyFormat(toggleItalic(value, currentSelection()))}
          onStroke={() => applyFormat(toggleStroke(value, currentSelection()))}
          onNumberedList={() => applyFormat(toggleNumberedList(value, currentSelection()))}
          onQuote={() => applyFormat(toggleQuote(value, currentSelection()))}
          onLink={() => {
            savedSelectionRef.current = currentSelection();
            setLinkDialogOpen(true);
          }}
        />
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(event) => {
              onChange(event.target.value);
              setCursor(event.target.selectionStart ?? event.target.value.length);
            }}
            onKeyUp={(event) => setCursor(event.currentTarget.selectionStart ?? 0)}
            onClick={(event) => setCursor(event.currentTarget.selectionStart ?? 0)}
            placeholder={t("message.placeholder")}
            aria-invalid={Boolean(errorMessage)}
            rows={4}
            className="mt-2 w-full resize-none text-base leading-6 text-[#00101A] outline-none"
          />
          {mention && <MentionSuggestionList results={mention.results} onSelect={selectMention} />}
        </div>
      </div>
      <p className="text-sm font-medium text-[#999999]">{t("message.mentionHint")}</p>
      {errorMessage && <span className="text-sm font-bold text-[#B3261E]">{errorMessage}</span>}
      <AddLinkDialog open={linkDialogOpen} onCancel={() => setLinkDialogOpen(false)} onSave={handleLinkSave} />
    </div>
  );
}
