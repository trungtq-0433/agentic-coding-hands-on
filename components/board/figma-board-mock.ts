import type { KudoCardData, KudoParticipant } from "./kudo-card-types";

/**
 * Dữ liệu mock cho màn Live board — **lấy nguyên văn từ Figma**, dùng tạm cho
 * tới phase-16.
 *
 * Phase-09 KHÔNG sở hữu nguồn dữ liệu này: feed thật đọc qua `public_kudos_feed`
 * (phase-02/04), realtime qua Broadcast (phase-05). File này chỉ để trang render
 * được ngay khi Track B chưa nối, và để phase-16 biết chính xác chỗ cần thay:
 * xoá file, trỏ `BoardPageClient` sang tầng dữ liệu thật. Không nơi nào khác đọc nó.
 *
 * Tên người, danh hiệu, hashtag, số tim, mốc thời gian đều là chuỗi có thật
 * trong bản vẽ (`MaZUn5xHXZ`) — không bịa thêm.
 */

/** Tên Sunner xuất hiện trong word-cloud Spotlight của bản vẽ. */
const FIGMA_NAMES = [
  "Đỗ hoàng Hiệp",
  "Dương thúy An",
  "Mai phương Thúy",
  "Lê Kiều Trang",
  "Nguyễn Văn Quy",
  "Nguyễn Bá Chức",
  "Nguyễn Hoàng Linh",
] as const;

/** Hai ảnh avatar mẫu tải từ Figma; xoay vòng cho đủ số người. */
const AVATARS = ["/board/avatar-a.png", "/board/avatar-b.png", "/board/avatar-c.png"] as const;

function participant(index: number, starCount: number): KudoParticipant {
  return {
    id: `mock-user-${index}`,
    name: FIGMA_NAMES[index % FIGMA_NAMES.length],
    avatarUrl: AVATARS[index % AVATARS.length],
    starCount,
    // Hạng Hero: bản vẽ có 4 hạng nhưng KHÔNG có ngưỡng. Mock gán tay để thấy
    // được huy hiệu trên UI; luật suy ra hạng vẫn là việc của phase-16/PO.
    // `new` cố tình không dùng vì thiếu file ảnh (xem `kudo-card-types.ts`).
    heroTier: index % 3 === 0 ? "legend" : index % 3 === 1 ? "super" : "rising",
  };
}

/** Người gửi ẩn danh — nhãn cố định, không có tên tự nhập (clarifications gap #4). */
const ANONYMOUS: KudoParticipant = {
  id: null,
  name: null,
  avatarUrl: null,
  starCount: 0,
};

/**
 * Mốc thời gian cố định thay vì `Date.now()`: giá trị đổi mỗi lần render sẽ làm
 * server và client dựng ra HTML khác nhau → hydration mismatch. Bản vẽ ghi
 * "10:00 - 10/30/2025".
 */
const BASE_ISO = "2025-10-30T10:00:00+07:00";

function isoMinus(hours: number): string {
  return new Date(new Date(BASE_ISO).getTime() - hours * 3_600_000).toISOString();
}

export function buildFigmaKudoMock(count: number): KudoCardData[] {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    // Cứ 4 thẻ có 1 thẻ ẩn danh để trạng thái đó luôn nhìn thấy được khi kiểm.
    sender: i % 4 === 3 ? ANONYMOUS : participant(i, (i % 3) + 1),
    recipient: participant(i + 1, ((i + 1) % 3) + 1),
    createdAtIso: isoMinus(i * 3),
    title: i % 2 === 0 ? "IDOL GIỚI TRẺ" : null,
    body:
      "Cảm ơn bạn đã luôn sẵn sàng hỗ trợ cả nhóm những lúc gấp gáp nhất, " +
      "và vẫn giữ được tinh thần tích cực khiến mọi người xung quanh cùng vững tâm.",
    images:
      i % 3 === 0
        ? Array.from({ length: (i % 5) + 1 }, () => ({
            url: "/board/kudo-sample-image.png",
            width: 88,
            height: 88,
          }))
        : [],
    // Lưu TÊN TRẦN, không kèm `#` — thẻ tự thêm dấu khi render. Để `#` ở đây
    // là ra `##Dedicated`. Tầng dữ liệu thật (bảng `hashtags` phase-02) cũng
    // lưu tên trần.
    hashtags: ["Dedicated", "Inspring"],
    heartCount: 1000 - i * 37,
    hearted: i % 5 === 0,
  }));
}

/** Tổng kudos hiển thị ở Spotlight — bản vẽ ghi "388 KUDOS". */
export const FIGMA_TOTAL_KUDOS = 388;

/**
 * Tên + trọng số cho word-cloud Spotlight.
 *
 * Bản vẽ rải **~130 node tên** kín panel — 7 tên gốc thì cloud trông thưa hoác,
 * không ra hình dạng thiết kế. Nhân lên `count` mục bằng cách xoay vòng danh
 * sách tên thật của Figma; `id` KHÔNG lặp (ghép thêm chỉ số) vì trùng `id` là
 * trùng React key — lỗi đã dính hai lần trong phase này.
 *
 * Trọng số sinh tất định từ chỉ số, KHÔNG `Math.random()`: server và client
 * phải dựng ra cùng một layout, lệch là vỡ hydration.
 */
export function buildFigmaSpotlightNames(count = 130) {
  return Array.from({ length: count }, (_, i) => ({
    id: `mock-name-${i}`,
    name: FIGMA_NAMES[i % FIGMA_NAMES.length],
    weight: 1 + ((i * 37) % 100),
  }));
}

/** Quà mẫu — chuỗi lấy nguyên văn từ `I2940:13516;256:7472` của bản vẽ. */
const FIGMA_GIFTS = [
  "Nhận được 1 áo phông SAA",
  "Nhận được 1 bình giữ nhiệt SAA",
  "Nhận được 1 sổ tay SAA",
] as const;

/**
 * 10 Sunner nhận quà mới nhất (`D.3_`, node `2940:13510`).
 *
 * Trước đó `board-page-client` truyền mảng RỖNG nên `LeaderboardList` tự ẩn cả
 * khối — nhìn ra là "thiếu mục 10 Sunner" so với bản vẽ. Dữ liệu thật đến từ
 * `secret_box_grants` (phase-02) và sẽ nối ở phase-16; mock này chỉ để khối
 * hiển thị đúng hình dạng.
 */
export function buildFigmaGiftReceivers() {
  return Array.from({ length: 10 }, (_, i) => ({
    id: `mock-user-${i % FIGMA_NAMES.length}`,
    name: FIGMA_NAMES[i % FIGMA_NAMES.length],
    avatarUrl: AVATARS[i % AVATARS.length],
    note: FIGMA_GIFTS[i % FIGMA_GIFTS.length],
  }));
}

/**
 * Dòng thông báo chìm trong Spotlight (`3004:15995`…`15999`, 6 dòng).
 *
 * Chuỗi lấy nguyên văn bản vẽ. Chúng hiển thị rất mờ (opacity 0.1) như lớp nền
 * chìm cùng tầng với tên người, không phải một danh sách thông báo riêng.
 *
 * Giờ trong chuỗi là **cố định**, không sinh từ `Date.now()`: giờ đổi mỗi lần
 * render sẽ khiến server và client dựng ra HTML khác nhau → vỡ hydration.
 * Dữ liệu thật đến từ tín hiệu Broadcast (phase-05), nối ở phase-16.
 */
export function buildFigmaTicker() {
  return FIGMA_NAMES.slice(0, 6).map((name, i) => ({
    id: `mock-ticker-${i}`,
    text: `0${(i % 9) + 1}:30PM ${name} đã nhận được một Kudos mới`,
  }));
}
