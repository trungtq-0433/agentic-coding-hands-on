"use client";

import { useEffect, useRef } from "react";

import { createClient } from "@/lib/supabase/client";
import { createBoardChannel } from "@/lib/realtime/kudos-channel";
import type { KudosBoardHandlers } from "@/lib/realtime/types";

export interface UseKudosStreamOptions {
  /** `false` để tắt kết nối realtime — tab ẩn, hoặc lúc test. Mặc định `true`. */
  enabled?: boolean;
}

/**
 * Lắng nghe topic công khai `kudos-board`. Guest (anon, chưa đăng nhập) vẫn
 * subscribe được — board là public, channel không yêu cầu phiên đăng nhập
 * (4 điều không được sai #2).
 *
 * Handler giữ trong `useRef` để KHÔNG resubscribe mỗi khi callback đổi
 * identity qua các lần render — effect subscribe chỉ phụ thuộc `enabled`.
 * Ghi `handlersRef.current` trong một effect riêng (không deps, chạy mỗi
 * commit) chứ không ghi thẳng lúc render — React 19 cấm mutate ref trong
 * render (`react-hooks/refs`, bắt bởi `eslint`).
 *
 * Cleanup gọi `supabase.removeChannel(channel)` — bắt buộc để React 19
 * StrictMode double-invoke effect không rò channel (4 điều không được sai #3).
 */
export function useKudosStream(handlers: KudosBoardHandlers, options: UseKudosStreamOptions = {}): void {
  const enabled = options.enabled ?? true;
  const handlersRef = useRef(handlers);

  useEffect(() => {
    handlersRef.current = handlers;
  });

  useEffect(() => {
    if (!enabled) return;

    const supabase = createClient();
    const channel = createBoardChannel(supabase, handlersRef);

    return () => {
      void supabase.removeChannel(channel);
    };
  }, [enabled]);
}
