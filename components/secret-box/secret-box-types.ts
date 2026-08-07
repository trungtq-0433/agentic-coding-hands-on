/**
 * Kiểu dữ liệu cho modal "Mở Secret Box" (phase-15). Tách khỏi component vì
 * phase-16 (nối RPC thật) và phase-09 (nút "Mở Secret Box" ở sidebar Live
 * board, `components/board/board-sidebar.tsx`) đều cần import kiểu này mà
 * không kéo theo runtime component. File này KHÔNG có `"use client"` — thuần
 * kiểu, không runtime.
 *
 * Track A: mọi giá trị đến từ props. Không import các module tầng server
 * (data / actions / supabase / realtime dưới `lib/`).
 *
 * **Vì sao `remaining` / `lastBadge` / `errorCode` là prop, không phải state:**
 * test case bảo mật của màn này (`5cc072ad-…` và `2e7bec78-…`, spec
 * `spec-open-secret-box-J3-4YFIpMM`) cấm client tự tính hoặc lưu số hộp chưa mở
 * và huy hiệu nhận được — "unopened box count always resets to the correct
 * backend value; client-side changes are ignored". Modal chỉ VẼ LẠI đúng những
 * gì props đưa xuống ở lần render hiện tại, không có bản sao cục bộ nào có thể
 * lệch khỏi server (không `useState` đếm, không tự cộng/trừ sau khi mở).
 */

export interface SecretBoxBadge {
  /**
   * Tên huy hiệu hiển thị — 1 trong 6 loại cố định theo spec item C
   * (Stay Gold 30% / Flow to Horizon 25% / Beyond the Boundary 10% /
   * Root Further 5% / Touch of Light 20% / Revival 10%). Tỉ lệ ngẫu nhiên là
   * việc của RPC phía server (phase-16) — UI không biết và không cần biết.
   * Đây là tên riêng (proper noun) của giải thưởng nên giữ nguyên, không dịch
   * — cùng quy ước với tên giải ở Homepage (`components/home/figma-award-mock.ts`).
   */
  name: string;
  /**
   * URL ảnh huy hiệu do server cấp (bảng `badges.image_url`, xem báo cáo
   * researcher §synthesis dòng "badges"). `null`/thiếu → hiện fallback dạng
   * chữ, KHÔNG tự vẽ ảnh thay thế — xem `secret-box-badge-image.tsx`.
   */
  imageUrl: string | null;
}

export interface SecretBoxModalProps {
  open: boolean;
  onClose: () => void;
  /**
   * Gọi RPC mở hộp thật (phase-16). Track A chỉ gọi và chờ kết quả để nhả
   * chốt chặn double-click — KHÔNG tự trừ/tự cộng bất kỳ số nào từ kết quả trả
   * về. Hiển thị luôn theo prop `remaining`/`lastBadge` mà CHA truyền xuống ở
   * lần render kế tiếp (cha là nơi cập nhật state sau khi RPC trả lời).
   */
  onOpenBox: () => Promise<{ badge: SecretBoxBadge; remaining: number }>;
  /** Số hộp chưa mở — LUÔN từ server. Không có bộ đếm nội bộ nào khác trong namespace này. */
  remaining: number;
  /** Huy hiệu vừa nhận được gần nhất, hiển thị bên trong hộp. `null` = chưa mở lần nào trong phiên này. */
  lastBadge: SecretBoxBadge | null;
  /**
   * `true` khi cha đang có lời gọi `onOpenBox` bay tới server. Đây là lớp
   * chặn THỨ HAI (phản ánh trạng thái xác thực từ cha); lớp THỨ NHẤT là ref
   * cục bộ trong `use-secret-box-open.ts`, chặn ngay trong tick bấm đầu tiên
   * trước khi prop này kịp lật sang `true`.
   */
  opening: boolean;
  /**
   * Cha set khi RPC báo hết hộp — kể cả khi `remaining` (đo lúc modal mở) vẫn
   * còn >0, ví dụ do một tab khác vừa mở hết ngay trước lúc request tới nơi.
   * Hiện thông báo hết hộp thay vì để người dùng bấm vào khoảng trống.
   */
  errorCode?: "NO_UNOPENED_BOX";
}
