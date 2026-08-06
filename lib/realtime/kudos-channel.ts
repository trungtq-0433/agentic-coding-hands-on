import type { RealtimeChannel } from "@supabase/supabase-js";

import { fetchKudoCardById, type SupabaseBrowserClient } from "@/lib/realtime/fetch-kudo-card";
import type { KudosBoardHandlers, MyHeartsHandlers } from "@/lib/realtime/types";

/**
 * Tạo/huỷ channel Broadcast, KHÔNG giữ state module-level (Todo List phase-05).
 * Caller (hook) chịu trách nhiệm subscribe/unsubscribe qua vòng đời effect và
 * gọi `supabase.removeChannel()` lúc cleanup.
 *
 * Topic + event khớp đúng tham số `realtime.send(payload, event, topic, private)`
 * trong trigger `0006b` (đã kiểm bằng `\df+ realtime.send` trên DB local):
 * - kudos-board:  event='kudos-board', topic='kudos-board', private=false
 * - user-hearts:  event='user-hearts', topic='user-hearts:<recipient_id>', private=false
 * `private=false` ở cả hai nghĩa là Realtime Authorization không áp dụng —
 * không cần policy trên `realtime.messages` để anon nghe được `kudos-board`.
 */
const BOARD_TOPIC = "kudos-board";
const BOARD_EVENT = "kudos-board";
const HEARTS_EVENT = "user-hearts";

interface KudosBoardBroadcastPayload {
  kudos_id: number;
  event: "insert" | "update";
}

interface HeartsBroadcastPayload {
  kudos_id: number;
  hearted: boolean;
}

/** Ref khả biến để hook truyền handler mới nhất mà không phải resubscribe (handler đổi identity mỗi render). */
export interface HandlersRef<T> {
  current: T;
}

export function createBoardChannel(
  supabase: SupabaseBrowserClient,
  handlersRef: HandlersRef<KudosBoardHandlers>,
): RealtimeChannel {
  return supabase
    .channel(BOARD_TOPIC)
    .on("broadcast", { event: BOARD_EVENT }, ({ payload }) => {
      void handleBoardSignal(supabase, payload as unknown, handlersRef.current);
    })
    .subscribe((status, err) => {
      if (status === "CHANNEL_ERROR" || status === "TIMED_OUT") {
        handlersRef.current.onError?.(err ?? new Error(`kudos-board channel: ${status}`));
      }
    });
}

export function createMyHeartsChannel(
  supabase: SupabaseBrowserClient,
  userId: string,
  handlersRef: HandlersRef<MyHeartsHandlers>,
): RealtimeChannel {
  const topic = `user-hearts:${userId}`;
  return supabase
    .channel(topic)
    .on("broadcast", { event: HEARTS_EVENT }, ({ payload }) => {
      handleHeartsSignal(payload as unknown, handlersRef.current);
    })
    .subscribe((status, err) => {
      if (status === "CHANNEL_ERROR" || status === "TIMED_OUT") {
        handlersRef.current.onError?.(err ?? new Error(`user-hearts channel: ${status}`));
      }
    });
}

/** Payload đến từ ngoài hệ thống (WebSocket) — validate hình dạng trước khi tin, rồi refetch-on-signal (4 điều không được sai #1). */
function isKudosBoardPayload(value: unknown): value is KudosBoardBroadcastPayload {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.kudos_id === "number" &&
    (record.event === "insert" || record.event === "update")
  );
}

function isHeartsPayload(value: unknown): value is HeartsBroadcastPayload {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return typeof record.kudos_id === "number" && typeof record.hearted === "boolean";
}

async function handleBoardSignal(
  supabase: SupabaseBrowserClient,
  rawPayload: unknown,
  handlers: KudosBoardHandlers,
): Promise<void> {
  if (!isKudosBoardPayload(rawPayload)) return; // payload không hợp lệ — bỏ qua, không đoán mò

  try {
    const card = await fetchKudoCardById(supabase, rawPayload.kudos_id);
    if (!card) return; // bị lọc/không đủ quyền/đã xoá — BỎ QUA, không hiện gì

    if (rawPayload.event === "insert") {
      handlers.onInsert(card);
    } else {
      handlers.onHeartCountChange(card.id, card.heartCount);
    }
  } catch (error) {
    handlers.onError?.(error instanceof Error ? error : new Error(String(error)));
  }
}

function handleHeartsSignal(rawPayload: unknown, handlers: MyHeartsHandlers): void {
  if (!isHeartsPayload(rawPayload)) return;
  handlers.onMyHeartChange(rawPayload.kudos_id, rawPayload.hearted);
}
