import type { SVGProps } from "react";

/**
 * Icon huy hiệu dùng chung cho menu trái (`awards-nav.tsx`) và hàng tiêu đề
 * mỗi thẻ giải (`award-card.tsx`, hàng tiêu đề cao 32px theo số đo Figma qua
 * MCP của orchestrator). Tách ra file riêng để 2 nơi dùng chung 1 định nghĩa
 * thay vì khai trùng — cùng lý do `components/board/board-icons.tsx` đã gộp.
 *
 * Không tra được path SVG gốc của icon dẫn đầu trong CSV (agent implement
 * không có MCP khả dụng phiên này) — dùng huy hiệu ngôi sao đơn giản tự vẽ
 * làm biểu tượng chung cho cả 6 hạng mục, KHÔNG phải asset Figma thật.
 */
export function MedalIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" {...props}>
      <path
        d="M12 2l2.39 4.84 5.34.78-3.87 3.77.91 5.32L12 14.27l-4.77 2.44.91-5.32-3.87-3.77 5.34-.78L12 2z"
        fill="currentColor"
      />
    </svg>
  );
}
