"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";

export interface ModalShellProps {
  open: boolean;
  onClose: () => void;
  labelledBy: string;
  children: ReactNode;
}

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

/**
 * Bộ đếm tham chiếu khoá scroll + stack modal đang mở — Ở CẤP MODULE (dùng
 * chung cho MỌI instance của ModalShell trong toàn ứng dụng), KHÔNG phải
 * state cục bộ của từng component.
 *
 * Lý do: phase-10/13/15 chạy song song, mỗi phase compose nội dung riêng bên
 * trong ModalShell nhưng đều lấy chrome (backdrop/Esc/focus-trap/scroll-lock)
 * từ ĐÂY. Nếu mỗi phase tự khoá/mở scroll độc lập, kịch bản "mở A → mở B →
 * đóng B" sẽ mở khoá scroll ngay cả khi A vẫn còn mở — sai. Bộ đếm tham chiếu
 * đảm bảo scroll chỉ mở khoá khi KHÔNG còn modal nào đang mở (đếm về 0).
 */
let scrollLockCount = 0;
let previousBodyOverflow: string | null = null;
const openModalStack: string[] = [];

function lockScroll() {
  if (scrollLockCount === 0) {
    previousBodyOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
  }
  scrollLockCount += 1;
}

function unlockScroll() {
  scrollLockCount = Math.max(0, scrollLockCount - 1);
  if (scrollLockCount === 0) {
    document.body.style.overflow = previousBodyOverflow ?? "";
    previousBodyOverflow = null;
  }
}

export function ModalShell({ open, onClose, labelledBy, children }: ModalShellProps) {
  const id = useId();
  const containerRef = useRef<HTMLDivElement>(null);

  // `onClose` giữ trong ref để effect focus-trap KHÔNG phụ thuộc identity của nó.
  // Caller gần như luôn truyền arrow inline (`onClose={() => setOpen(false)}`), nên
  // mỗi lần component cha re-render là một hàm mới → effect chạy lại → nó focus lại
  // phần tử đầu tiên và cướp con trỏ khỏi ô input người dùng đang gõ dở.
  // Cùng bài toán mà lib/realtime/use-kudos-stream.ts đã giải bằng handlersRef.
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onCloseRef.current = onClose;
  });

  // Đăng ký/gỡ khỏi stack toàn cục + khoá/mở scroll theo bộ đếm tham chiếu.
  useEffect(() => {
    if (!open) return undefined;

    openModalStack.push(id);
    lockScroll();

    return () => {
      unlockScroll();
      const index = openModalStack.indexOf(id);
      if (index !== -1) openModalStack.splice(index, 1);
    };
  }, [open, id]);

  // Focus trap (Tab không thoát khỏi modal) + Esc chỉ đóng modal TRÊN CÙNG
  // của stack — gộp chung 1 listener keydown để không nhân đôi.
  useEffect(() => {
    if (!open) return undefined;
    const container = containerRef.current;
    if (!container) return undefined;

    const previouslyFocused = document.activeElement as HTMLElement | null;

    const getFocusable = (): HTMLElement[] =>
      Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)).filter(
        (el) => el.offsetParent !== null,
      );

    const initialFocusables = getFocusable();
    (initialFocusables[0] ?? container).focus();

    function isTopmost() {
      return openModalStack[openModalStack.length - 1] === id;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (!isTopmost()) return; // không phải modal trên cùng — để modal trên xử lý

      if (event.key === "Escape") {
        onCloseRef.current();
        return;
      }

      if (event.key !== "Tab") return;

      const items = getFocusable();
      if (items.length === 0) {
        event.preventDefault();
        return;
      }
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      previouslyFocused?.focus();
    };
  }, [open, id]);

  if (!open) return null;

  // Không dùng createPortal: component luôn render ở gốc cây trang (page/
  // layout gọi trực tiếp), `fixed inset-0` đủ để phủ toàn màn hình mà không
  // cần thoát ra document.body. Lưu ý: nếu một ancestor có `transform`/
  // `filter` CSS, nó tạo containing block mới khiến `fixed` bị giới hạn
  // trong ancestor đó thay vì viewport — tránh đặt ModalShell bên trong such
  // ancestor.
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60" aria-hidden="true" onClick={() => onCloseRef.current()} />
      <div
        ref={containerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        tabIndex={-1}
        className="relative z-10 max-h-[90vh] overflow-auto outline-none"
      >
        {children}
      </div>
    </div>
  );
}
