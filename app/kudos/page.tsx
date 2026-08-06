import { signOutAction } from "@/lib/actions/auth-actions";
import { getCurrentProfile, isCurrentUserAdmin } from "@/lib/auth/dal";
import { BoardPageClient } from "@/components/board/board-page-client";

/**
 * Màn `/kudos` — Sun* Kudos Live board.
 *
 * Server Component mỏng: đọc phiên đăng nhập thật rồi giao hết phần UI cho
 * `BoardPageClient`.
 *
 * **Nối phiên NGAY từ đầu, không hoãn tới phase-16** — đây là bài học trực tiếp
 * từ phase-08: ở đó `profile` bị truyền cứng `null` theo đúng ranh giới Track
 * A/B, nhưng `proxy.ts` của Track B lại đọc cookie thật, nên trang có hai nguồn
 * sự thật ngược nhau và người đã đăng nhập bị kẹt vòng không thoát ra được. Màn
 * này cũng có header với menu tài khoản nên sẽ dính y hệt. Xem
 * `plans/reports/debugger-260806-1347-header-mau-thuan-trang-thai-dang-nhap.md`.
 *
 * `verifySession()` bọc `cache()` nên hai lệnh gọi song song chỉ hỏi Supabase
 * Auth MỘT lần cho cả request.
 *
 * Ràng buộc Track A vẫn giữ nguyên ở tầng component: `components/board/**`
 * không import `lib/data|actions|supabase|realtime` — chỉ file page này được phép.
 */
export default async function KudosBoardRoute() {
  const [profile, isAdmin] = await Promise.all([getCurrentProfile(), isCurrentUserAdmin()]);

  return (
    <BoardPageClient
      profile={profile ? { name: profile.fullName, avatarUrl: profile.avatarUrl } : null}
      isAdmin={isAdmin}
      signOut={signOutAction}
    />
  );
}
