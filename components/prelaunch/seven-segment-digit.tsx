/**
 * Chữ số LCD 7 đoạn vẽ bằng SVG.
 *
 * **Vì sao vẽ chứ không dùng font.** Bản vẽ khai `font-family: "Digital Numbers"`
 * — font LCD 7 đoạn không có trên Google Fonts và không có sẵn trong hệ thống.
 * Bản trước thay bằng `Share Tech Mono` (monospace thường), ra chữ số bo tròn
 * bình thường, khác hẳn hình dáng gãy khúc của bản vẽ.
 *
 * Ba đường có thể đi: (1) xin file font thật, (2) kéo một font 7 đoạn nguồn mở
 * về repo, (3) vẽ thẳng. Chọn (3): không thêm phụ thuộc, không câu hỏi bản
 * quyền, không nhấp nháy khi font tải, và hình dáng khớp chính xác vì tự dựng
 * hình học. Soi ảnh thiết kế ở mức 4x cho thấy đúng 7 đoạn cổ điển, đầu nét vát
 * 45°, có khe giữa các đoạn — dựng lại được bằng đa giác đơn giản.
 *
 * `viewBox` 60×96 giữ đúng tỉ lệ ô số 76.8×122.88 của bản vẽ (0.625).
 */

const W = 60;
const H = 96;
/** Độ dày nét. */
const T = 9;
/** Khe hở giữa hai đoạn kề nhau. */
const GAP = 2;

const X_LEFT = 6;
const X_RIGHT = W - 6;
const Y_TOP = 6;
const Y_MID = H / 2;
const Y_BOTTOM = H - 6;

/** Đoạn NGANG: lục giác, hai đầu vát 45°. */
function horizontal(y: number): string {
  const l = X_LEFT + GAP;
  const r = X_RIGHT - GAP;
  const h = T / 2;
  return `${l},${y} ${l + h},${y - h} ${r - h},${y - h} ${r},${y} ${r - h},${y + h} ${l + h},${y + h}`;
}

/** Đoạn DỌC: lục giác, hai đầu vát 45°. */
function vertical(x: number, yTop: number, yBottom: number): string {
  const t = yTop + GAP;
  const b = yBottom - GAP;
  const h = T / 2;
  return `${x},${t} ${x + h},${t + h} ${x + h},${b - h} ${x},${b} ${x - h},${b - h} ${x - h},${t + h}`;
}

/** Bảy đoạn theo tên chuẩn A–G của đèn 7 đoạn. */
const SEGMENT_POINTS: Record<string, string> = {
  A: horizontal(Y_TOP),
  B: vertical(X_RIGHT, Y_TOP, Y_MID),
  C: vertical(X_RIGHT, Y_MID, Y_BOTTOM),
  D: horizontal(Y_BOTTOM),
  E: vertical(X_LEFT, Y_MID, Y_BOTTOM),
  F: vertical(X_LEFT, Y_TOP, Y_MID),
  G: horizontal(Y_MID),
};

/** Đoạn nào sáng ứng với chữ số nào — bảng chuẩn của đèn 7 đoạn. */
const DIGIT_SEGMENTS: Record<string, readonly string[]> = {
  "0": ["A", "B", "C", "D", "E", "F"],
  "1": ["B", "C"],
  "2": ["A", "B", "G", "E", "D"],
  "3": ["A", "B", "G", "C", "D"],
  "4": ["F", "G", "B", "C"],
  "5": ["A", "F", "G", "C", "D"],
  "6": ["A", "F", "G", "E", "C", "D"],
  "7": ["A", "B", "C"],
  "8": ["A", "B", "C", "D", "E", "F", "G"],
  "9": ["A", "B", "C", "D", "F", "G"],
};

export interface SevenSegmentDigitProps {
  /** Đúng MỘT ký tự '0'–'9'. Ký tự khác thì không vẽ đoạn nào (ô trống). */
  digit: string;
  className?: string;
}

export function SevenSegmentDigit({ digit, className }: SevenSegmentDigitProps) {
  const segments = DIGIT_SEGMENTS[digit] ?? [];
  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className={className}
      /* Viền tối mảnh quanh nét trắng — bản vẽ có, giúp chữ số tách khỏi nền
         hoạ tiết nhiều màu bên dưới. */
      style={{ filter: "drop-shadow(0 1px 1.5px rgba(0,0,0,0.55))" }}
    >
      {segments.map((name) => (
        <polygon key={name} points={SEGMENT_POINTS[name]} fill="currentColor" />
      ))}
    </svg>
  );
}
