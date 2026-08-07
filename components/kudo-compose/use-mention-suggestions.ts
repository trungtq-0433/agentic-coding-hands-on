"use client";

import { useEffect, useRef, useState } from "react";

import { findMentionQuery } from "./rich-text-formatting";
import type { Profile } from "./compose-kudo-types";

export interface MentionState {
  /** Vị trí ký tự "@" trong `body` — cần để thay đúng đoạn khi chọn gợi ý. */
  mentionStart: number;
  query: string;
  results: Profile[];
}

/**
 * Phát hiện "@tên đang gõ dở" quanh vị trí con trỏ và gọi `searchSunners` để
 * lấy gợi ý mention (TC_12/13/33). Dùng LẠI đúng callback `searchSunners` của
 * integration contract — draft không có `mentionIds` riêng (đã bỏ khỏi MVP),
 * nên không cần một nguồn dữ liệu thứ hai cho việc gợi ý tên.
 *
 * Chỉ gọi khi phần gõ sau "@" đã có ÍT NHẤT 1 KÝ TỰ, khớp đúng ràng buộc
 * "tối thiểu 1 ký tự" của `searchSunners` (mms_B.2) — gõ "@" trơ trọi chưa
 * kích hoạt tìm kiếm, chỉ khi gõ thêm ký tự đầu tiên.
 *
 * `active`/`activeQuery` tính THẲNG trong thân hàm (không phải state) — đây
 * là giá trị suy được từ `body`+`cursor` mỗi lần render, không phải side
 * effect. Effect bên dưới chỉ còn đúng MỘT việc: gọi `searchSunners` khi có
 * mention query mới, tránh lỗi `react-hooks/set-state-in-effect` (đặt state
 * lại state suy được từ props ngay trong effect).
 */
export function useMentionSuggestions(
  body: string,
  cursor: number,
  searchSunners: (query: string) => Promise<Profile[]>,
) {
  const active = findMentionQuery(body, cursor);
  const activeQuery = active && active.query.length > 0 ? active.query : null;

  const [results, setResults] = useState<Profile[]>([]);
  const requestIdRef = useRef(0);

  useEffect(() => {
    if (!activeQuery) return undefined; // không có mention đang gõ — giữ nguyên `results` cũ, không hiển thị vì `mention` bên dưới sẽ là null
    const requestId = ++requestIdRef.current;
    const timer = window.setTimeout(() => {
      searchSunners(activeQuery)
        .then((profiles) => {
          if (requestIdRef.current !== requestId) return;
          setResults(profiles);
        })
        .catch((error: unknown) => {
          console.error("[kudo-compose] gợi ý mention thất bại:", error);
        });
    }, 200);
    return () => window.clearTimeout(timer);
  }, [activeQuery, searchSunners]);

  const mention: MentionState | null =
    active && activeQuery ? { mentionStart: active.start, query: activeQuery, results } : null;

  return { mention };
}
