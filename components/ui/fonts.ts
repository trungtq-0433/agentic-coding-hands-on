import { Montserrat } from "next/font/google";

/**
 * Font Montserrat (weight 700 — trọng số DUY NHẤT xuất hiện trong 9 màn Figma
 * của phase-06). `next/font/google` có thể gọi ở bất kỳ module nào, không bắt
 * buộc phải khai báo ở `app/layout.tsx` — tránh phải sửa file ngoài ownership
 * (`app/**` thuộc phase khác). Import `montserrat.className` ở nơi cần áp
 * đúng font thiết kế thay vì font mặc định Geist của root layout.
 */
export const montserrat = Montserrat({
  subsets: ["latin", "vietnamese"],
  weight: ["700"],
  display: "swap",
});
