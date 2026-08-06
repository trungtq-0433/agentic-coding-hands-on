import type { KudoCard } from "@/lib/kudos/kudo-card-mapper";

/**
 * Kiểu callback dùng chung cho `useKudosStream` — phase-16 cắm vào Live board
 * sẽ import từ đây, không định nghĩa lại (phase-05 Related Code Files).
 *
 * `onError` là tuỳ chọn: lỗi refetch/kết nối không được nuốt im lặng, nhưng
 * hook không tự quyết cách hiển thị lỗi (đó là việc của phase-16/component).
 */
export interface KudosBoardHandlers {
  /** Tín hiệu `insert` đã refetch thành công → card mới để prepend/queue. */
  onInsert(card: KudoCard): void;
  /** Tín hiệu `update` đã refetch thành công → số tim mới nhất từ server. */
  onHeartCountChange(kudosId: number, heartCount: number): void;
  onError?(error: Error): void;
}

/** Kiểu callback cho `useMyHeartsStream` — đồng bộ trạng thái đã-tim của CHÍNH user giữa các tab. */
export interface MyHeartsHandlers {
  onMyHeartChange(kudosId: number, hearted: boolean): void;
  onError?(error: Error): void;
}
