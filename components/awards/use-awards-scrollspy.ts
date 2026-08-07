"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export interface UseAwardsScrollspyOptions {
  /** Danh sách slug theo đúng thứ tự hiển thị — dùng để chọn slug đầu khi không có hash hợp lệ. */
  slugs: string[];
  /**
   * Slug ban đầu do trang cha truyền vào (nếu có) — dùng làm state khởi tạo,
   * PHẢI giống nhau giữa server và client để tránh lệch hydrate. Vì lý do đó,
   * hook KHÔNG đọc `window.location.hash` ở đây (giá trị này chỉ tồn tại phía
   * trình duyệt) — hash thật được đọc trong `useEffect` bên dưới, chạy sau khi
   * hydrate xong nên không gây lệch.
   */
  initialSlug?: string;
}

/**
 * Theo dõi thẻ giải nào đang ở trong khung nhìn để tô sáng đúng mục menu trái
 * (CSV: "Active state: gold color + underline on selected item; scroll to
 * target section"). Tự quản lý HOÀN TOÀN trong `AwardsPage` (đúng integration
 * contract của phase-12) — trang cha chỉ cần truyền `awards` + `activeSlug`
 * ban đầu, không cần biết trạng thái cuộn.
 *
 * `IntersectionObserver` với `rootMargin` âm phía trên bằng chiều cao header
 * cố định (~112px) + biên dưới rộng để mục "đang đọc" là mục gần đỉnh khung
 * nhìn nhất, không phải mục chiếm nhiều diện tích nhất — khớp hành vi menu
 * trái thường thấy hơn `threshold` đơn thuần khi các thẻ cao thấp khác nhau.
 */
export function useAwardsScrollspy({ slugs, initialSlug }: UseAwardsScrollspyOptions) {
  const [activeSlug, setActiveSlug] = useState(initialSlug ?? slugs[0] ?? "");
  const nodesRef = useRef(new Map<string, HTMLElement>());
  // Cờ chặn observer ghi đè active state trong lúc đang cuộn theo lệnh (bấm
  // menu/scroll ban đầu) — cuộn mượt đi qua nhiều thẻ khác trước khi tới đích,
  // observer sẽ báo sai mục nếu không tạm khoá.
  const suppressUntilRef = useRef(0);

  const registerRef = useCallback((slug: string, node: HTMLElement | null) => {
    if (node) nodesRef.current.set(slug, node);
    else nodesRef.current.delete(slug);
  }, []);

  const scrollToSlug = useCallback((slug: string, behavior: ScrollBehavior = "smooth") => {
    const node = nodesRef.current.get(slug);
    if (!node) return;
    suppressUntilRef.current = Date.now() + 700;
    setActiveSlug(slug);
    node.scrollIntoView({ behavior, block: "start" });
    // Đồng bộ hash lên URL mà KHÔNG điều hướng App Router (tránh re-fetch data
    // của trang) — giữ link chia sẻ được đúng theo integration contract.
    window.history.replaceState(null, "", `#${slug}`);
  }, []);

  useEffect(() => {
    // Đọc hash THẬT của trình duyệt ở đây, không phải ở lazy initializer của
    // `useState` — `window.location.hash` chỉ tồn tại phía client, đọc nó lúc
    // render sẽ làm HTML server và client lệch nhau (React báo lỗi hydrate).
    // `useEffect` chỉ chạy sau khi hydrate xong nên an toàn.
    const hashSlug = window.location.hash.replace(/^#/, "");
    const target = hashSlug || initialSlug;
    if (target && slugs.includes(target)) scrollToSlug(target, "auto");
    // Chỉ chạy đúng 1 lần lúc mount — cuộn ban đầu không nên lặp lại khi
    // `initialSlug`/`slugs` đổi giá trị tham chiếu ở các render sau.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (Date.now() < suppressUntilRef.current) return;
        const visible = entries.filter((entry) => entry.isIntersecting);
        if (visible.length === 0) return;
        // Trong các thẻ đang giao khung nhìn, chọn thẻ có mép trên gần đỉnh
        // nhất — đúng thẻ người dùng đang đọc.
        const topMost = visible.reduce((closest, entry) =>
          entry.boundingClientRect.top < closest.boundingClientRect.top ? entry : closest,
        );
        const slug = slugs.find((candidate) => nodesRef.current.get(candidate) === topMost.target);
        if (slug) setActiveSlug(slug);
      },
      { rootMargin: "-112px 0px -60% 0px", threshold: 0 },
    );

    for (const slug of slugs) {
      const node = nodesRef.current.get(slug);
      if (node) observer.observe(node);
    }

    return () => observer.disconnect();
  }, [slugs]);

  return { activeSlug, registerRef, scrollToSlug };
}
