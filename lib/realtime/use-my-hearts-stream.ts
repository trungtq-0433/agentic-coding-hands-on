"use client";

import { useEffect, useRef } from "react";

import { createClient } from "@/lib/supabase/client";
import { createMyHeartsChannel } from "@/lib/realtime/kudos-channel";
import type { MyHeartsHandlers } from "@/lib/realtime/types";

export interface UseMyHeartsStreamOptions {
  /** `false` để tắt kết nối realtime. Mặc định `true`. */
  enabled?: boolean;
}

/**
 * Lắng nghe topic riêng `user-hearts:<userId>` — đồng bộ trạng thái đã-tim
 * giữa nhiều tab của CÙNG một user. Guest (`userId` rỗng/null) không có trạng
 * thái tim riêng nên không mở channel — tránh subscribe một topic vô nghĩa.
 *
 * Cleanup gọi `supabase.removeChannel(channel)` giống `useKudosStream`.
 * Ghi `handlersRef.current` trong effect riêng (không deps) — cùng lý do
 * `react-hooks/refs` như `useKudosStream`, không ghi thẳng lúc render.
 */
export function useMyHeartsStream(
  userId: string | null | undefined,
  handlers: MyHeartsHandlers,
  options: UseMyHeartsStreamOptions = {},
): void {
  const enabled = (options.enabled ?? true) && Boolean(userId);
  const handlersRef = useRef(handlers);

  useEffect(() => {
    handlersRef.current = handlers;
  });

  useEffect(() => {
    if (!enabled || !userId) return;

    const supabase = createClient();
    const channel = createMyHeartsChannel(supabase, userId, handlersRef);

    return () => {
      void supabase.removeChannel(channel);
    };
  }, [enabled, userId]);
}
