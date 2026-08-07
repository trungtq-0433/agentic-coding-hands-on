import type { SVGProps } from "react";

/**
 * Icon riêng của toolbar rich-text trong modal Viết Kudo — 2 icon KHÔNG có sẵn
 * ở `components/ui/icons.tsx` (danh sách đánh số, trích dẫn).
 *
 * Hai node này không mang tiền tố `MM_MEDIA_` (chỉ là icon trang trí trong
 * toolbar, không phải asset ảnh) nên nằm ngoài pipeline tải asset MoMorph —
 * đúng cái bẫy đã ghi nhận ở phase-07/08/09 (3 lớp nền Spotlight, badge Hero
 * "New"). Dựng lại bằng path chuẩn thông dụng, không bịa chi tiết cầu kỳ.
 * Các nút toolbar còn lại KHÔNG cần icon riêng:
 * - Bold/Italic/Stroke: spec ghi rõ là chữ cái "B"/"I"/"S" (mms_C.1/C.2/C.3),
 *   không phải icon hình vẽ.
 * - Link: dùng lại `LinkIcon` từ `components/ui/icons.tsx` (đã có).
 */
type IconProps = SVGProps<SVGSVGElement>;

/** Danh sách đánh số — 3 gạch ngang + 2 chữ số gợi thứ tự. */
export function NumberedListIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} {...props}>
      <path d="M9 6h11M9 12h11M9 18h11" strokeLinecap="round" />
      <path d="M4.5 4.5h1v3M4.5 7.5h2" strokeLinecap="round" strokeLinejoin="round" />
      <path
        d="M4 12.2c0-.7.6-1.2 1.3-1.2.7 0 1.2.5 1.2 1.1 0 .4-.2.7-.5 1l-1.7 1.6h2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** Trích dẫn — hai dấu ngoặc kép cách điệu. */
export function QuoteIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M7 6c-2.8 0-5 2.2-5 5v7h7v-7H6c0-1.7 1.3-3 3-3V6H7zm10 0c-2.8 0-5 2.2-5 5v7h7v-7h-3c0-1.7 1.3-3 3-3V6h-2z" />
    </svg>
  );
}
