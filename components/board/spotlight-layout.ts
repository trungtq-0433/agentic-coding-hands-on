/**
 * Bố cục word-cloud tất định cho Spotlight (`spotlight-section.tsx`) — chia
 * lưới theo đúng tỉ lệ khung panel Figma `B.7_Spotlight` (`2940:14174`,
 * 1157×548 ≈ 2.11:1) rồi jitter vị trí bằng hash tất định của `id` (KHÔNG
 * dùng `Math.random()`/`Date.now()` — tránh lệch hydration SSR/client).
 *
 * Cỡ chữ tên chia 4 BẬC theo thứ hạng `weight`, không phải một cỡ duy nhất —
 * xem `NAME_FONT_TIERS` để biết số đo và vì sao kết luận "đồng cỡ" trước đó là sai.
 *
 * Cũng chứa `computeTickerLayout` cho 6 dòng thông báo Kudos-mới. Chúng là một
 * CỘT xếp dọc ở góc dưới-trái với dải mờ nhạt dần lên trên (node `3004:15995`…
 * `15999` + `2940:14230`) — KHÔNG rải ngẫu nhiên trong word-cloud như bản trước.
 */

import type { SpotlightName, SpotlightTicker } from "./spotlight-section";

export interface LayoutName extends SpotlightName {
  leftPct: number;
  topPct: number;
  /**
   * Tên được tô màu nhấn `#F17676` thay vì trắng.
   *
   * Trong bản vẽ có ĐÚNG MỘT node như vậy trên tổng 106 (`Nguyễn Hoàng Linh`,
   * và nó nằm trong bậc chữ lớn nhất). Không có chú thích nào nói vì sao, nên
   * ở đây gán cho tên hạng nhất — cùng cơ chế thứ hạng đã dùng cho cỡ chữ.
   * **Cần người soạn spec xác nhận**: cũng có thể đó chỉ là trạng thái hover
   * được vẽ sẵn trong mockup chứ không phải một trạng thái thường trực.
   */
  accent: boolean;
  fontSize: number;
  /** Line-height (px) — tỉ lệ 6.358/6.656 đo từ node mẫu, scale theo fontSize. */
  lineHeight: number;
}

export interface LayoutTicker extends SpotlightTicker {
  leftPct: number;
  topPct: number;
  /** Độ mờ riêng từng dòng — bản vẽ dùng dải nhạt dần, không phải một trị chung. */
  opacity: number;
}

/**
 * Bậc cỡ chữ tên trong word-cloud — **4 bậc rời rạc**, không phải một dải liên
 * tục và cũng không phải một cỡ duy nhất.
 *
 * Lịch sử hai lần sai ở chỗ này, ghi lại để không đi lại:
 * 1. Bản đầu map `weight` vào dải liên tục 12–32px rồi 6.5–20px — bịa.
 * 2. Bản sau lấy mẫu 4 node, thấy cả bốn đều 6.656px, rồi chốt "mọi tên đều
 *    đồng cỡ". Sai vì mẫu quá nhỏ: đếm `fontSize` trên TOÀN BỘ 107 node trong
 *    panel cho ra 6.656×97, 7.937×3, 10.205×3, 11.339×3 (36px là tiêu đề "388
 *    KUDOS", không phải tên). Bản vẽ CÓ nhấn mạnh một nhóm nhỏ.
 *
 * Vì bản vẽ nhấn đúng 3 tên mỗi bậc trên, ánh xạ ở đây theo THỨ HẠNG chứ không
 * theo ngưỡng số tuyệt đối: xếp `weight` giảm dần rồi lấy 3 tên đầu vào bậc lớn
 * nhất, 3 tên kế bậc sau, 3 tên kế nữa bậc sau nữa, phần còn lại về cỡ nền.
 * Ngưỡng tuyệt đối thì không suy ra được — bản vẽ không ghi.
 */
const NAME_FONT_TIERS = [
  { size: 11.339, count: 3 },
  { size: 10.205, count: 3 },
  { size: 7.937, count: 3 },
] as const;
/** Cỡ nền cho mọi tên ngoài các bậc nhấn (97/106 node trong bản vẽ). */
const NAME_FONT_SIZE = 6.656;

// Tỉ lệ line-height/font-size đo ở node mẫu `2995:15926` (6.358 / 6.656).
const LINE_HEIGHT_RATIO = 6.358 / 6.656;

/**
 * Cỡ chữ theo thứ hạng `weight`. Trả về Map `id -> fontSize`.
 *
 * Sắp xếp có tie-break bằng `id`: hai tên cùng `weight` mà thứ tự phụ thuộc
 * thuật toán sort thì server và client có thể ra khác nhau → vỡ hydration.
 */
function buildFontSizeByRank(names: SpotlightName[]): { sizes: Map<string, number>; accentId?: string } {
  const ranked = [...names].sort((a, b) => b.weight - a.weight || a.id.localeCompare(b.id));
  const sizes = new Map<string, number>();
  let cursor = 0;
  for (const tier of NAME_FONT_TIERS) {
    for (let i = 0; i < tier.count && cursor < ranked.length; i += 1, cursor += 1) {
      sizes.set(ranked[cursor].id, tier.size);
    }
  }
  return { sizes, accentId: ranked[0]?.id };
}

// Tỉ lệ khung panel `B.7_Spotlight`: 1157×548 — dùng để chia lưới theo đúng
// hình chữ nhật bẹt của panel thay vì lưới vuông ⌈√n⌉×⌈√n⌉ cũ. Lưới vuông làm
// bố cục thưa/lệch tâm khi panel rộng gấp ~2.1 lần cao, đặc biệt rõ với danh
// sách tên ngắn (mock hiện có 7 tên → lưới vuông 3×3 chỉ lấp 7/9 ô, dồn hết
// vào giữa; lưới theo tỉ lệ panel trải rộng ra 4×2, sát bố cục thật hơn).
const PANEL_ASPECT_RATIO = 1157 / 548;

export function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

/** Hash chuỗi tất định (FNV-1a) → số trong [0,1). Thay cho `Math.random()`. */
export function hashToUnit(input: string): number {
  let hash = 0x811c9dc5;
  for (let i = 0; i < input.length; i += 1) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0) / 0xffffffff;
}

/**
 * Dải mà bản vẽ thật sự rải tên — KHÔNG phải toàn bộ panel.
 *
 * Đo hộp bao của cả 106 node tên: x 10.5%…97.7%, y 8.9%…109.5% (mép dưới tràn
 * ra ngoài panel rồi bị `overflow-hidden` cắt). Điều đáng nói là mép TRÁI: bản
 * vẽ chừa hẳn 10.5% đầu tiên, đúng chỗ ô tìm kiếm ngồi — nên ô tìm kiếm không
 * bao giờ có chữ chạy sau lưng. Lưới cũ trải 4%…96% nên tên đâm thẳng vào ô tìm
 * kiếm lẫn tiêu đề "388 KUDOS", góp phần vào cảm giác "hiển thị lộn xộn".
 *
 * Mép dưới lấy 100 thay vì 109.5: cắt mất tên thì tên đó thành vô hình, mà đây
 * là bảng để TÌM người.
 */
const BAND_LEFT_PCT = 10.5;
const BAND_RIGHT_PCT = 97.7;
const BAND_TOP_PCT = 8.9;
const BAND_BOTTOM_PCT = 100;

/** Sinh vị trí + cỡ chữ tất định cho word-cloud từ mảng tên đã cho. */
export function computeLayout(names: SpotlightName[]): LayoutName[] {
  const count = names.length;
  if (count === 0) return [];
  const columns = Math.max(1, Math.round(Math.sqrt(count * PANEL_ASPECT_RATIO)));
  const rows = Math.max(1, Math.ceil(count / columns));
  const cellW = (BAND_RIGHT_PCT - BAND_LEFT_PCT) / columns;
  const cellH = (BAND_BOTTOM_PCT - BAND_TOP_PCT) / rows;
  const { sizes: fontSizeById, accentId } = buildFontSizeByRank(names);
  return names.map((n, i) => {
    const col = i % columns;
    const row = Math.floor(i / columns);
    const jitterX = (hashToUnit(`${n.id}:x`) - 0.5) * cellW * 0.7;
    const jitterY = (hashToUnit(`${n.id}:y`) - 0.5) * cellH * 0.7;
    const leftPct = clamp(BAND_LEFT_PCT + col * cellW + cellW / 2 + jitterX, BAND_LEFT_PCT, BAND_RIGHT_PCT);
    const topPct = clamp(BAND_TOP_PCT + row * cellH + cellH / 2 + jitterY, BAND_TOP_PCT, BAND_BOTTOM_PCT);
    const fontSize = fontSizeById.get(n.id) ?? NAME_FONT_SIZE;
    return {
      ...n,
      leftPct,
      topPct,
      accent: n.id === accentId,
      fontSize,
      lineHeight: fontSize * LINE_HEIGHT_RATIO,
    };
  });
}

/**
 * Cột ticker — **KHÔNG rải ngẫu nhiên**.
 *
 * Bản dựng trước hash `id` ra toạ độ bất kỳ, ném 6 câu thông báo lẫn vào giữa
 * 130 cái tên; đó đúng là chỗ nhìn ra "nội dung lộn xộn". Toạ độ tuyệt đối của
 * 6 node (`3004:15995`…`15999` + `2940:14230`) cho thấy chúng là một CỘT XẾP
 * DỌC ở góc dưới-trái: cùng `x=191`, y = 2068/2087/2106/2125/2144/2163 (cách
 * đều 19px), và opacity đi thành dải 0.1 → 0.3 → 0.5 → 0.7 → 1 → 1 từ trên
 * xuống. Tức một luồng thông báo trôi LÊN rồi nhạt dần, không phải chữ nền.
 *
 * Quy về gốc panel `B.7_Spotlight` (142, 1658), khung 1157×548.
 */
const TICKER_LEFT_PCT = ((191 - 142) / 1157) * 100;
/** Dòng MỚI NHẤT — nằm dưới cùng, rõ nhất. */
const TICKER_BOTTOM_TOP_PCT = ((2163 - 1658) / 548) * 100;
const TICKER_STEP_PCT = (19 / 548) * 100;
/** Dải mờ tính TỪ DƯỚI LÊN. Độ dài mảng cũng là số dòng tối đa bản vẽ dành chỗ. */
const TICKER_OPACITY_FROM_BOTTOM = [1, 1, 0.7, 0.5, 0.3, 0.1] as const;

export function computeTickerLayout(ticker: SpotlightTicker[]): LayoutTicker[] {
  // Lấy các mục CUỐI mảng: mới nhất nằm dưới cùng, cũ hơn thì trôi lên và nhạt đi.
  const visible = ticker.slice(-TICKER_OPACITY_FROM_BOTTOM.length);
  const lastIndex = visible.length - 1;
  return visible.map((item, i) => {
    const fromBottom = lastIndex - i;
    return {
      ...item,
      leftPct: TICKER_LEFT_PCT,
      topPct: TICKER_BOTTOM_TOP_PCT - fromBottom * TICKER_STEP_PCT,
      opacity: TICKER_OPACITY_FROM_BOTTOM[fromBottom],
    };
  });
}
