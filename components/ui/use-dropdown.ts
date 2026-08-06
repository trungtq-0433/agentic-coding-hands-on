"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Hook dùng chung cho các popover nhỏ đóng vai trò dropdown gắn với 1 nút
 * trigger: FilterDropdown, MultiHashtagPicker, LanguageSwitcher, AccountMenu.
 *
 * Cố ý KHÔNG dùng chung cơ chế stack/scroll-lock của `ModalShell` — đây là
 * popover nhỏ, không che toàn màn hình, không cần khoá scroll nền, và nhiều
 * popover có thể mở đồng thời mà không xung đột (khác với modal toàn màn nơi
 * 3 phase song song sẽ đá nhau nếu tự dựng riêng).
 */
export function useDropdown<T extends HTMLElement>() {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<T>(null);

  useEffect(() => {
    if (!open) return undefined;

    function handlePointerDown(event: MouseEvent) {
      if (!rootRef.current) return;
      if (!rootRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  return { open, setOpen, rootRef };
}
