import { Montserrat, Montserrat_Alternates } from "next/font/google";

/**
 * Font Montserrat. `next/font/google` có thể gọi ở bất kỳ module nào, không bắt
 * buộc phải khai báo ở `app/layout.tsx` — tránh phải sửa file ngoài ownership
 * (`app/**` thuộc phase khác). Import `montserrat.className` ở nơi cần áp
 * đúng font thiết kế thay vì font mặc định Geist của root layout.
 *
 * **Bàn giao kiểm soát phase-06 → phase-08 (2026-08-06):** trước đây chỉ khai
 * `["700"]` với ghi chú "trọng số DUY NHẤT xuất hiện trong 9 màn Figma của
 * phase-06" — đúng với 9 màn đó, nhưng màn Homepage (`i87tDx10uM`) dùng thêm
 * **400** (tiêu đề + mô tả thẻ giải, node `I2167:9075;214:1021`/`;214:1022`) và
 * **500** (nút "Chi tiết", node `;214:1023;186:1439`).
 *
 * Đây không phải chuyện thẩm mỹ: `next/font/google` CHỈ sinh `@font-face` cho
 * những weight được liệt kê ở đây. Thiếu 400/500 thì `font-normal`/`font-medium`
 * trong CSS vẫn đúng nhưng trình duyệt không có file font tương ứng, phải tự
 * suy ra từ 700 (synthetic) hoặc rơi về font hệ thống — chữ dày sai so với bản
 * vẽ mà không có lỗi nào báo ra.
 */
export const montserrat = Montserrat({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "700"],
  display: "swap",
});

/**
 * Montserrat **Alternates** — chỉ dòng bản quyền ở footer dùng font này
 * (`mms_D_Footer` → node `I662:14447;342:1413`, đo trên màn Login). Phần còn lại
 * của thiết kế dùng Montserrat thường, nên hai font cùng tồn tại là đúng bản vẽ,
 * không phải nhầm lẫn.
 */
export const montserratAlternates = Montserrat_Alternates({
  subsets: ["latin", "vietnamese"],
  weight: ["700"],
  display: "swap",
});
