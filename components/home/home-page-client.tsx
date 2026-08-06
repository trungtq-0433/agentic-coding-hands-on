"use client";

import type { AccountMenuProfile } from "@/components/ui/account-menu";

import { buildFigmaAwardMock } from "./figma-award-mock";
import { HomePage } from "./home-page";
import { useHomeT } from "./use-home-text";

export interface HomePageClientProps {
  targetIso: string;
  /** `null` = khách chưa đăng nhập. `app/page.tsx` đọc từ session thật. */
  profile: AccountMenuProfile | null;
  isAdmin: boolean;
  /** Server Action `signOutAction` — huỷ cookie session rồi `redirect("/")`. */
  signOut: () => Promise<void>;
}

/**
 * Boundary Client Component mỏng giữa `app/page.tsx` (Server Component) và
 * `HomePage`. Lý do tồn tại giống hệt `login-page-client.tsx`: Next.js không cho
 * truyền function THƯỜNG từ Server Component xuống Client Component qua props,
 * nhưng contract của `HomePage` cần callback đồng bộ thật.
 *
 * Ngoại lệ là **Server Action** — `signOut` truyền xuống được vì nó là Server
 * Action, không phải function thường.
 *
 * **Còn lại của phase-16** (grep `phase-16` để tìm):
 * `onCompose` / `onRules` mở modal Viết Kudo (phase-10) và Thể lệ (phase-13) —
 * hai màn CHƯA TỒN TẠI. Không dựng modal giả ở đây: phase-06 đã chốt
 * `ModalShell` là chrome dùng chung, ba phase tự dựng là ba Esc-listener đá
 * nhau. Nút vẫn bấm được và FAB vẫn thu gọn lại; chưa có gì mở ra.
 */
export function HomePageClient({ targetIso, profile, isAdmin, signOut }: HomePageClientProps) {
  const t = useHomeT();
  // KHÔNG bọc `useMemo`: `useNamespaceTranslation` trả về một arrow function
  // MỚI mỗi lần render, nên `[t]` luôn khác và memo không bao giờ trúng — chỉ
  // thêm một tầng gọi hàm mà không tiết kiệm gì. Bản thân việc dựng là map qua
  // 6 phần tử, rẻ hơn cả chi phí so sánh dependency.
  const awards = buildFigmaAwardMock(t);

  function handleCompose() {
    // phase-16: mở modal Viết Kudo (phase-10).
  }

  function handleRules() {
    // phase-16: mở modal Thể lệ (phase-13).
  }

  function handleSignOut() {
    // `onSignOut` trong contract là đồng bộ (`() => void`), còn Server Action
    // trả Promise — nuốt promise ở đây. Không cần `router.refresh()`: bản thân
    // `signOutAction` kết thúc bằng `redirect("/")`, Next tự điều hướng lại và
    // render lại trang ở trạng thái khách.
    void signOut().catch((error: unknown) => {
      console.error("[home] đăng xuất thất bại:", error);
    });
  }

  return (
    <HomePage
      targetIso={targetIso}
      awards={awards}
      profile={profile}
      isAdmin={isAdmin}
      onCompose={handleCompose}
      onRules={handleRules}
      onSignOut={handleSignOut}
    />
  );
}
