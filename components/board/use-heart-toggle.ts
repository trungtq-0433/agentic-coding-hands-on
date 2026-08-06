"use client";

import { useCallback, useRef, useState } from "react";

import type { KudoCardData, ToggleHeartResult } from "./kudo-card-types";

export interface UseHeartToggleOptions {
  /** Gọi server. Track B cung cấp ở phase-16; hiện tại là hàm giả lập của trang cha. */
  onToggleHeart: (kudosId: number) => Promise<ToggleHeartResult>;
  /** Báo lỗi cho người dùng khi `ok:false`. */
  onError: () => void;
}

export interface UseHeartToggleResult {
  /** Các thẻ đang chờ server — truyền xuống `KudosFeed.pendingHeartIds`. */
  pendingHeartIds: ReadonlySet<number>;
  /** Áp kết quả thả tim lên danh sách gốc. Gọi khi render, không phải khi bấm. */
  applyOverrides: (items: KudoCardData[]) => KudoCardData[];
  toggle: (kudosId: number) => void;
}

/**
 * Quản lý việc thả tim: chặn double-click và áp kết quả server lên danh sách.
 *
 * **Hai luật của phase-09, đừng nới lỏng:**
 *
 * 1. **KHÔNG cập nhật lạc quan.** Con số tim chỉ đổi khi server trả về
 *    `heartCount` (TC_WEB_PROFILE_FUN_014). Bấm xong mà chưa có phản hồi thì
 *    UI đứng yên — cố ý, không phải thiếu sót. `ok:false` → giữ nguyên trạng
 *    thái cũ, chỉ hiện lỗi.
 * 2. **Một thẻ chỉ có tối đa MỘT lời gọi đang bay.** Kiểm `pending` ngay đầu
 *    `toggle` và thoát sớm. Nếu chỉ dựa vào prop `disabled` của nút thì bấm
 *    thật nhanh vẫn lọt nhiều lần trước lúc React kịp render lại — mà server
 *    có `for update skip locked` + `on conflict do nothing` (phase-04) nên
 *    lời gọi thừa sẽ âm thầm không có tác dụng, khiến số tim trông như nhảy loạn.
 *
 * Kết quả lưu thành lớp "đè" theo `id` thay vì sửa thẳng `items`: danh sách gốc
 * đến từ props (và ở phase-16 sẽ được refetch), nên copy nó vào state là tự tạo
 * ra hai nguồn sự thật.
 */
export function useHeartToggle({ onToggleHeart, onError }: UseHeartToggleOptions): UseHeartToggleResult {
  const [pending, setPending] = useState<ReadonlySet<number>>(() => new Set());
  /** Bản sao đồng bộ của `pending` — state cập nhật quá muộn để chặn double-click. */
  const pendingRef = useRef<ReadonlySet<number>>(new Set());
  const [overrides, setOverrides] = useState<ReadonlyMap<number, { hearted: boolean; heartCount: number }>>(
    () => new Map(),
  );

  const toggle = useCallback(
    (kudosId: number) => {
      // Chốt chặn đọc/ghi trên REF, không phải trên state.
      //
      // Bản đầu kiểm `pending.has(kudosId)` với `pending` là state — và nó KHÔNG
      // chặn được gì: năm cú bấm trong cùng một tick đều nhìn thấy đúng một
      // closure với `pending` còn rỗng (state chỉ đổi sau khi render lại), nên
      // cả năm đều lọt qua. Đã kiểm bằng trình duyệt: bấm 5 lần liên tiếp thì
      // nút vẫn `disabled === false` ngay sau đó, tức chưa hề khoá.
      // Con số hiển thị lúc ấy vẫn đúng, nhưng chỉ vì cả 5 lời gọi tính ra cùng
      // một kết quả — với RPC thật thì đó là 5 lần gọi server.
      // Ref cập nhật đồng bộ nên cú bấm thứ hai trở đi thấy ngay dấu vết cú đầu.
      if (pendingRef.current.has(kudosId)) return;
      pendingRef.current = new Set(pendingRef.current).add(kudosId);
      setPending(pendingRef.current);

      void onToggleHeart(kudosId)
        .then((result) => {
          if (result.ok && result.hearted !== undefined && result.heartCount !== undefined) {
            const next = { hearted: result.hearted, heartCount: result.heartCount };
            setOverrides((prev) => new Map(prev).set(kudosId, next));
            return;
          }
          onError();
        })
        .catch((error: unknown) => {
          console.error("[board] thả tim thất bại:", error);
          onError();
        })
        .finally(() => {
          const next = new Set(pendingRef.current);
          next.delete(kudosId);
          pendingRef.current = next;
          setPending(next);
        });
    },
    [onToggleHeart, onError],
  );

  const applyOverrides = useCallback(
    (items: KudoCardData[]) =>
      overrides.size === 0
        ? items
        : items.map((item) => {
            const override = overrides.get(item.id);
            return override ? { ...item, ...override } : item;
          }),
    [overrides],
  );

  return { pendingHeartIds: pending, applyOverrides, toggle };
}
