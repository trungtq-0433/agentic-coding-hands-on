import type { SVGProps } from "react";

/**
 * Icon inline SVG dùng chung cho các component dropdown/FAB/dialog.
 * Chọn inline SVG thay vì ảnh asset tải từ Figma vì: (1) hầu hết icon trong 9
 * màn là hình đơn giản (chevron, dấu X, dấu +, ...) tái tạo được chính xác
 * bằng path chuẩn; (2) `currentColor` cho phép component cha đổi màu qua
 * class Tailwind (`text-*`) mà không cần biến thể ảnh khác màu; (3) không cần
 * đụng vào thư mục `public/**` (ngoài ownership phase-06: chỉ
 * `components/ui/**`, `components/layout/**`, `locales/*\/common-ui.json`).
 *
 * Icon cờ VN/EN (FlagVNIcon/FlagENIcon) là bản đơn giản hoá, KHÔNG phải vector
 * chính xác từ Figma (Figma chỉ cho biết đây là icon cờ quốc gia qua ảnh chụp,
 * không trả path SVG gốc) — xem phần "chưa khớp Figma" trong báo cáo cuối.
 */
type IconProps = SVGProps<SVGSVGElement>;

export function ChevronDownIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} {...props}>
      <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function ChevronRightIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} {...props}>
      <path d="M9 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function CloseIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} {...props}>
      <path d="M6 6l12 12M18 6L6 18" strokeLinecap="round" />
    </svg>
  );
}

export function PlusIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} {...props}>
      <path d="M12 5v14M5 12h14" strokeLinecap="round" />
    </svg>
  );
}

export function CheckCircleIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <circle cx="12" cy="12" r="10" fill="white" />
      <path d="M8 12.5l2.5 2.5L16 9.5" stroke="black" strokeWidth={2} fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function PenIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} {...props}>
      <path
        d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function GridIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <rect x="4" y="4" width="7" height="7" rx="1.5" />
      <rect x="13" y="4" width="7" height="7" rx="1.5" />
      <rect x="4" y="13" width="7" height="7" rx="1.5" />
      <rect x="13" y="13" width="7" height="7" rx="1.5" />
    </svg>
  );
}

export function UserIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 20c0-4.4 3.6-8 8-8s8 3.6 8 8" />
    </svg>
  );
}

export function LinkIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} {...props}>
      <path
        d="M9.5 14.5l5-5M8 16l-2 2a3 3 0 01-4.2-4.2l3-3A3 3 0 019 10m6 4a3 3 0 004.2.2l3-3a3 3 0 00-4.2-4.2l-2 2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** Icon tia sét — logo rút gọn dùng ở KudosFab (2 trạng thái thu gọn/mở rộng). */
export function LightningIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 20 18" fill="currentColor" {...props}>
      <path d="M11 0L2 10h6l-2 8 9-10h-6l2-8z" />
    </svg>
  );
}

export function FlagVNIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" {...props}>
      <rect width="24" height="24" rx="4" fill="#DA251D" />
      <path d="M12 6l1.8 5.5h5.8l-4.7 3.4 1.8 5.5-4.7-3.4-4.7 3.4 1.8-5.5-4.7-3.4h5.8z" fill="#FFCD00" />
    </svg>
  );
}

export function FlagENIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" {...props}>
      <rect width="24" height="24" rx="4" fill="#00247D" />
      <path d="M0 0l24 24M24 0L0 24" stroke="#FFFFFF" strokeWidth={4} />
      <path d="M0 0l24 24M24 0L0 24" stroke="#CF142B" strokeWidth={1.6} />
      <path d="M12 0v24M0 12h24" stroke="#FFFFFF" strokeWidth={6} />
      <path d="M12 0v24M0 12h24" stroke="#CF142B" strokeWidth={2.4} />
    </svg>
  );
}
