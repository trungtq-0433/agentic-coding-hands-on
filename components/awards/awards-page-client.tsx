"use client";

import { useRouter } from "next/navigation";

import type { AccountMenuProfile } from "@/components/ui/account-menu";
import type { AwardContent } from "@/lib/content/awards";

import { AwardsPage } from "./awards-page";

export interface AwardsPageClientProps {
  awards: AwardContent[];
  /** `null` = khách chưa đăng nhập. `app/awards/page.tsx` đọc từ session thật. */
  profile: AccountMenuProfile | null;
  isAdmin: boolean;
  /** Server Action `signOutAction` — huỷ cookie session rồi `redirect("/")`. */
  signOut: () => Promise<void>;
}

/**
 * Boundary Client Component mỏng giữa `app/awards/page.tsx` (Server Component)
 * và `AwardsPage` — cùng lý do tồn tại như `home-page-client.tsx`/
 * `board-page-client.tsx`: Next không cho truyền function THƯỜNG từ Server
 * sang Client Component qua props, trừ Server Action.
 *
 * Không truyền `activeSlug` xuống `AwardsPage`: URL hash (`/awards#top-talent`,
 * đường vào từ thẻ giải Homepage) không bao giờ tới được server (đặc tả HTTP —
 * trình duyệt giữ fragment lại, không gửi kèm request), nên `app/awards/page.tsx`
 * không thể biết trước giá trị này. `use-awards-scrollspy.ts` tự đọc
 * `window.location.hash` bên trong `useEffect` (chạy sau khi hydrate xong,
 * không gây lệch HTML server/client) — xem comment ở đó.
 *
 * **Nối phiên NGAY khi dựng màn** (bài học phase-08, ghi trong
 * `clarifications.md` mục "phase-09..12"): `app/awards/page.tsx` đọc session
 * thật, không truyền cứng `profile={null}`.
 *
 * **Còn lại của phase-16:** `onRules` mở modal Thể lệ (phase-13) — CHƯA TỒN
 * TẠI. Không dựng modal giả (chốt ở phase-06: `ModalShell` là chrome dùng
 * chung, nhiều phase tự dựng là nhiều Esc-listener đá nhau).
 */
export function AwardsPageClient({ awards, profile, isAdmin, signOut }: AwardsPageClientProps) {
  const router = useRouter();

  function handleNavigate(path: string) {
    router.push(path);
  }

  function handleRules() {
    // phase-16: mở modal Thể lệ (phase-13).
  }

  function handleSignOut() {
    void signOut().catch((error: unknown) => {
      console.error("[awards] đăng xuất thất bại:", error);
    });
  }

  return (
    <AwardsPage
      awards={awards}
      onNavigate={handleNavigate}
      profile={profile}
      isAdmin={isAdmin}
      onSignOut={handleSignOut}
      onRules={handleRules}
    />
  );
}
