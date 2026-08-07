"use client";

import { useCallback, useRef } from "react";

import type { SecretBoxBadge } from "./secret-box-types";

/**
 * Chốt chặn double-open cho nút mở Secret Box.
 *
 * **Cùng lỗi, cùng cách sửa như `components/board/use-heart-toggle.ts` (phase-09):**
 * nếu chỉ kiểm cờ bằng `useState`, 5 cú bấm liên tiếp trong CÙNG một tick đều
 * đọc phải closure cũ (state chỉ đổi SAU khi component render lại), nên cả 5
 * đều lọt qua và bắn 5 lời gọi `onOpenBox` thật — dù con số hiển thị vẫn có
 * thể trông "đúng" vì server có ràng buộc chống trùng, khiến lỗi dễ lọt qua
 * mắt nếu chỉ nhìn kết quả cuối. Ref cập nhật ĐỒNG BỘ ngay trong lệnh gọi đầu
 * tiên nên cú bấm thứ hai trở đi thấy ngay dấu vết, không cần chờ render lại.
 *
 * Đây là lớp chặn THỨ NHẤT, độc lập với prop `opening` mà cha truyền xuống —
 * `opening` chỉ đổi SAU khi cha re-render (lớp chặn thứ hai), còn ref này đổi
 * ngay lập tức trong cùng tick bấm, trước khi prop đó kịp lật.
 */
export function useSecretBoxOpen(
  onOpenBox: () => Promise<{ badge: SecretBoxBadge; remaining: number }>,
): () => void {
  const openingRef = useRef(false);

  const handleOpen = useCallback(() => {
    if (openingRef.current) return;
    openingRef.current = true;

    void onOpenBox()
      .catch((error: unknown) => {
        // Contract của phase này không có callback lỗi riêng: cha hiển thị
        // thông báo "hết hộp" qua prop `errorCode` khi RPC trả về đúng mã đó.
        // Lỗi mạng/lỗi khác thì log ra để không âm thầm biến mất (Gate #1).
        console.error("[secret-box] mở hộp thất bại:", error);
      })
      .finally(() => {
        openingRef.current = false;
      });
  }, [onOpenBox]);

  return handleOpen;
}
