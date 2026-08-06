import type { SVGProps } from "react";

/**
 * Icon của màn Live board — path chép NGUYÊN VĂN từ các file SVG tải về ở
 * `public/board/`, chỉ đổi `fill` cứng thành `currentColor`.
 *
 * **Vì sao nội tuyến thay vì `<img src="/board/icon-*.svg">`:** icon ở đây phải
 * đổi màu theo ngữ cảnh (tim đã thả/chưa thả, nút bật/tắt, hover). `<img>` không
 * cho CSS chạm vào bên trong SVG.
 *
 * **Vì sao gom về một file:** trước đó mỗi component tự nội tuyến icon của mình
 * — icon kính lúp bị chép trùng ở 2 nơi, và tệ hơn, `kudo-card` dùng một path
 * bút chì TỰ ĐƠN GIẢN HOÁ chứ không phải path thật trong `icon-pen.svg`. Trùng
 * lặp thì còn sửa được; vẽ sai so với bản thiết kế thì không ai phát hiện ra
 * cho tới lúc soi bằng mắt.
 *
 * `icon-heart.svg` gốc tô sẵn `#D4271D`. Ở đây để `currentColor` để component
 * cha quyết màu qua class `text-*` — trạng thái chưa thả tim cần màu khác.
 */
type IconProps = SVGProps<SVGSVGElement>;

function Icon({ children, ...props }: IconProps & { children: React.ReactNode }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" {...props}>
      {children}
    </svg>
  );
}

/**
 * Ngọn lửa nền huy hiệu "x2" ở hàng Số tim (`3241:14932` `image 35`, 34×40,
 * tỉ lệ 17:20).
 *
 * **Đây là hình VẼ LẠI, không phải asset gốc.** `image 35` là RECTANGLE tô nền
 * ảnh raster và node không mang tiền tố `MM_MEDIA_` nên nằm ngoài pipeline
 * asset MoMorph; `get_figma_image` trả 500 (cùng cái bẫy với ảnh hero phase-07
 * và 3 lớp nền Spotlight). Hai tông màu lấy bằng cách đếm pixel trong đúng ô
 * 34×40 của ảnh thiết kế: `#FFA721` thân lửa (358px) và `#FF700D` lưỡi trong
 * (48px). Thay cho hình chữ nhật bo góc đỏ `#D4271D` mà bản dựng trước tự đặt.
 */
export function FlameIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 34 40" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" {...props}>
      <path
        d="M17 0c1.7 5.2 4.6 8.4 7.2 11.2 1.1-1.5 1.7-3 2-4.6 3.9 4.6 6.2 9.6 6.2 15.1C32.4 32.2 25.5 40 17 40S1.6 32.2 1.6 21.7c0-4.6 1.7-8.5 4.3-12.1.3 2 1 3.8 2.2 5.4C10.9 11 14.6 6.4 17 0z"
        fill="#FFA721"
      />
      <path
        d="M17 12.4c1.4 3.4 3.6 5.6 5.3 7.9 1.4 1.9 2.2 3.9 2.2 6.1 0 4.9-3.4 8.6-7.5 8.6s-7.5-3.7-7.5-8.6c0-2.6 1.1-4.9 2.9-7 1.9-2.2 3.6-4.3 4.6-7z"
        fill="#FF700D"
      />
    </svg>
  );
}

/**
 * Mũi tên chéo mở rộng của `B.7.2_Pan zoom` (`3007:17479`, khung 30×30 đặc,
 * không có node con lộ ra qua MCP nên nét vẽ dựng lại từ ảnh thiết kế): hai mũi
 * tên trắng đặc trỏ ra hai góc đối nhau — ↗ trên-phải và ↙ dưới-trái.
 *
 * Mỗi mũi tên chỉ dài ~10/30 và nằm GỌN trong góc của nó, chừa khoảng trống ở
 * giữa: vẽ dài hơn thì hai cái chập lại thành một mũi tên hai đầu liền mạch,
 * khác hẳn bản vẽ (đã dính đúng lỗi này ở lần dựng đầu).
 */
export function ExpandIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" {...props}>
      <path d="M27 3v8.5l-3-3-4.5 4.5-2.5-2.5 4.5-4.5-3-3z" fill="currentColor" />
      <path d="M3 27v-8.5l3 3 4.5-4.5 2.5 2.5-4.5 4.5 3 3z" fill="currentColor" />
    </svg>
  );
}

export function PenIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path
        d="M20.8067 6.72951C21.1967 6.33951 21.1967 5.68951 20.8067 5.31951L18.4667 2.97951C18.0967 2.58951 17.4467 2.58951 17.0567 2.97951L15.2167 4.80951L18.9667 8.55951M3.09668 16.9395V20.6895H6.84668L17.9067 9.61951L14.1567 5.86951L3.09668 16.9395Z"
        fill="currentColor"
      />
    </Icon>
  );
}

export function HeartIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path
        d="M12.3364 21.1076L10.8864 19.7876C5.73643 15.1176 2.33643 12.0276 2.33643 8.25757C2.33643 5.16757 4.75643 2.75757 7.83643 2.75757C9.57643 2.75757 11.2464 3.56757 12.3364 4.83757C13.4264 3.56757 15.0964 2.75757 16.8364 2.75757C19.9164 2.75757 22.3364 5.16757 22.3364 8.25757C22.3364 12.0276 18.9364 15.1176 13.7864 19.7876L12.3364 21.1076Z"
        fill="currentColor"
      />
    </Icon>
  );
}

export function LinkIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path
        d="M10.9619 13.1547C11.3719 13.5447 11.3719 14.1847 10.9619 14.5747C10.5719 14.9647 9.93189 14.9647 9.54189 14.5747C7.5919 12.6247 7.5919 9.4547 9.54189 7.5047L13.0819 3.9647C15.0319 2.0147 18.2019 2.0147 20.1519 3.9647C22.1019 5.9147 22.1019 9.0847 20.1519 11.0347L18.6619 12.5247C18.6719 11.7047 18.5419 10.8847 18.2619 10.1047L18.7319 9.6247C19.9119 8.4547 19.9119 6.5547 18.7319 5.3847C17.5619 4.2047 15.6619 4.2047 14.4919 5.3847L10.9619 8.9147C9.7819 10.0847 9.7819 11.9847 10.9619 13.1547ZM13.7819 8.9147C14.1719 8.5247 14.8119 8.5247 15.2019 8.9147C17.1519 10.8647 17.1519 14.0347 15.2019 15.9847L11.6619 19.5247C9.71189 21.4747 6.54189 21.4747 4.59189 19.5247C2.64189 17.5747 2.64189 14.4047 4.59189 12.4547L6.08189 10.9647C6.07189 11.7847 6.20189 12.6047 6.48189 13.3947L6.01189 13.8647C4.83189 15.0347 4.83189 16.9347 6.01189 18.1047C7.18189 19.2847 9.08189 19.2847 10.2519 18.1047L13.7819 14.5747C14.9619 13.4047 14.9619 11.5047 13.7819 10.3347C13.3719 9.9447 13.3719 9.3047 13.7819 8.9147Z"
        fill="currentColor"
      />
    </Icon>
  );
}

export function SendIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path
        d="M2.9043 20.4797V4.47974L21.9043 12.4797M4.9043 17.4797L16.7543 12.4797L4.9043 7.47974V10.9797L10.9043 12.4797L4.9043 13.9797M4.9043 17.4797V7.47974V13.9797V17.4797Z"
        fill="currentColor"
      />
    </Icon>
  );
}

export function SearchIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path
        d="M9.5 3C11.2239 3 12.8772 3.68482 14.0962 4.90381C15.3152 6.12279 16 7.77609 16 9.5C16 11.11 15.41 12.59 14.44 13.73L14.71 14H15.5L20.5 19L19 20.5L14 15.5V14.71L13.73 14.44C12.59 15.41 11.11 16 9.5 16C7.77609 16 6.12279 15.3152 4.90381 14.0962C3.68482 12.8772 3 11.2239 3 9.5C3 7.77609 3.68482 6.12279 4.90381 4.90381C6.12279 3.68482 7.77609 3 9.5 3ZM9.5 5C7 5 5 7 5 9.5C5 12 7 14 9.5 14C12 14 14 12 14 9.5C14 7 12 5 9.5 5Z"
        fill="currentColor"
      />
    </Icon>
  );
}

export function ArrowLeftIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M15.41 16.58L10.83 12L15.41 7.41L14 6L8 12L14 18L15.41 16.58Z" fill="currentColor" />
    </Icon>
  );
}

export function ArrowRightIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path
        d="M8.57959 16.4777L13.1596 11.8977L8.57959 7.3077L9.98959 5.89771L15.9896 11.8977L9.98959 17.8977L8.57959 16.4777Z"
        fill="currentColor"
      />
    </Icon>
  );
}

/**
 * Icon quà — chuyển từ `board-sidebar.tsx` về đây. Chỉ dùng ở một nơi
 * (`BoardSidebar`) nhưng vẫn gom vào file này để icon của màn Live board có
 * đúng một chỗ ở, thay vì nằm rải rác hai nơi.
 */
export function GiftIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path
        d="M22.5 10.3698L19.76 8.77984C20 8.56984 20.23 8.29984 20.4 7.99984C21.23 6.56984 20.74 4.72984 19.3 3.89984C18.44 3.39984 17.43 3.39984 16.58 3.75984L16.59 3.74984L15.71 4.13984L15.6 3.17984L15.59 3.18984C15.5 2.27984 14.97 1.39984 14.11 0.899841C12.67 0.0748415 10.84 0.569842 10 1.99984C9.83 2.29984 9.72 2.62984 9.66 2.94984L6.91 1.36984C5.95 0.819842 4.73 1.13984 4.18 2.09984L2.68 4.69984C2.4 5.17984 2.57 5.78984 3.05 6.05984L4.78 7.05984L9 9.49984H2.5V19.4998C2.5 20.6098 3.4 21.4998 4.5 21.4998H20.5C21.61 21.4998 22.5 20.6098 22.5 19.4998V14.3698L23.23 13.0998C23.78 12.1398 23.46 10.9198 22.5 10.3698ZM16.94 5.99984C17.21 5.49984 17.83 5.35984 18.3 5.62984C18.78 5.90984 18.95 6.49984 18.67 6.99984C18.39 7.49984 17.78 7.63984 17.3 7.36984C16.83 7.08984 16.66 6.49984 16.94 5.99984ZM14.57 8.09984L21.5 12.0998L20.5 13.8298L13.57 9.82984L14.57 8.09984ZM11.5 19.4998H4.5V11.4998H11.5V19.4998ZM11.84 8.82984L4.91 4.82984L5.91 3.09984L12.84 7.09984L11.84 8.82984ZM12.11 4.36984C11.63 4.08984 11.47 3.49984 11.74 2.99984C12 2.49984 12.63 2.35984 13.11 2.62984C13.59 2.90984 13.75 3.49984 13.47 3.99984C13.2 4.49984 12.59 4.63984 12.11 4.36984ZM13.5 19.4998V12.0998L20.5 16.1398V19.4998H13.5Z"
        fill="currentColor"
      />
    </Icon>
  );
}
