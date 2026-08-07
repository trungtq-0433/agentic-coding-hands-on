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

/**
 * Mũi tên xuống — path chép NGUYÊN VĂN từ `MM_MEDIA_Down`
 * (`public/board/icon-chevron-down.svg`), chỉ đổi `fill` cứng thành `currentColor`.
 *
 * Bản trước vẽ tay một nét gạch `M6 9l6 6 6-6` kiểu chevron viền. Icon thật là
 * **TAM GIÁC TÔ ĐẶC** — khác hẳn về hình, không phải lệch vài pixel. Dùng ở
 * `filter-dropdown` (bộ lọc Hashtag/Phòng ban ở Live board) và
 * `profile-direction-dropdown`.
 */
export function ChevronDownIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path d="M7 10L12 15L17 10H7Z" fill="currentColor" />
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

/**
 * Dấu đóng — path chép NGUYÊN VĂN từ `MM_MEDIA_Close` (`I3204:6093;186:2759`,
 * bản gốc ở `public/board/icon-close.svg`), chỉ đổi `fill` cứng thành
 * `currentColor`.
 *
 * Bản trước là hình TỰ CHẾ: hai nét gạch chéo `strokeWidth=2` đầu tròn. Icon
 * thật là một path TÔ ĐẶC, đầu nét vát vuông — dày hơn và sắc hơn hẳn. Đây đúng
 * cùng loại lỗi với icon bút ở phase-09 (`kudo-card` từng dùng path bút tự đơn
 * giản hoá): nhìn thoáng thì "cũng là dấu X" nên không ai phát hiện cho tới lúc
 * đặt cạnh bản vẽ. 8 component đang dùng icon này.
 */
export function CloseIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        d="M13.4759 12.0972L19.0159 17.6372V19.0972H17.5559L12.0159 13.5572L6.47587 19.0972H5.01587V17.6372L10.5559 12.0972L5.01587 6.55717V5.09717H6.47587L12.0159 10.6372L17.5559 5.09717H19.0159V6.55717L13.4759 12.0972Z"
        fill="currentColor"
      />
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

/**
 * Bút — path NGUYÊN VĂN từ `MM_MEDIA_Pen` (`public/board/icon-pen.svg`).
 *
 * Bản trước vẽ tay. Đây là lần THỨ HAI icon bút bị tự chế trong dự án: phase-09
 * đã bắt được một bản giả trong `kudo-card` và thay bằng path thật, nhưng bản
 * giả trong file DÙNG CHUNG này thì còn nguyên — nên `kudo-card`/`board-banner`
 * hiện bút thật, còn `kudos-fab`/`rules-panel` hiện bút giả. Cùng một icon, hai
 * hình khác nhau tuỳ màn. Đây giờ là nguồn DUY NHẤT; `board-icons.tsx` tái xuất.
 */
export function PenIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path d="M20.8067 6.72951C21.1967 6.33951 21.1967 5.68951 20.8067 5.31951L18.4667 2.97951C18.0967 2.58951 17.4467 2.58951 17.0567 2.97951L15.2167 4.80951L18.9667 8.55951M3.09668 16.9395V20.6895H6.84668L17.9067 9.61951L14.1567 5.86951L3.09668 16.9395Z" fill="currentColor" />
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

/**
 * Mắt xích — path NGUYÊN VĂN từ `MM_MEDIA_Link` (`public/board/icon-link.svg`).
 * Cùng câu chuyện với `PenIcon`: bản thật nằm ở `board-icons`, bản giả nằm ở
 * đây, nên `kudo-card` và `rich-text-toolbar` hiện hai hình khác nhau.
 */
export function LinkIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path d="M10.9619 13.1547C11.3719 13.5447 11.3719 14.1847 10.9619 14.5747C10.5719 14.9647 9.93189 14.9647 9.54189 14.5747C7.5919 12.6247 7.5919 9.4547 9.54189 7.5047L13.0819 3.9647C15.0319 2.0147 18.2019 2.0147 20.1519 3.9647C22.1019 5.9147 22.1019 9.0847 20.1519 11.0347L18.6619 12.5247C18.6719 11.7047 18.5419 10.8847 18.2619 10.1047L18.7319 9.6247C19.9119 8.4547 19.9119 6.5547 18.7319 5.3847C17.5619 4.2047 15.6619 4.2047 14.4919 5.3847L10.9619 8.9147C9.7819 10.0847 9.7819 11.9847 10.9619 13.1547ZM13.7819 8.9147C14.1719 8.5247 14.8119 8.5247 15.2019 8.9147C17.1519 10.8647 17.1519 14.0347 15.2019 15.9847L11.6619 19.5247C9.71189 21.4747 6.54189 21.4747 4.59189 19.5247C2.64189 17.5747 2.64189 14.4047 4.59189 12.4547L6.08189 10.9647C6.07189 11.7847 6.20189 12.6047 6.48189 13.3947L6.01189 13.8647C4.83189 15.0347 4.83189 16.9347 6.01189 18.1047C7.18189 19.2847 9.08189 19.2847 10.2519 18.1047L13.7819 14.5747C14.9619 13.4047 14.9619 11.5047 13.7819 10.3347C13.3719 9.9447 13.3719 9.3047 13.7819 8.9147Z" fill="currentColor" />
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
