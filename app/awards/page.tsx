import { signOutAction } from "@/lib/actions/auth-actions";
import { getCurrentProfile, isCurrentUserAdmin } from "@/lib/auth/dal";
import { AwardsPageClient } from "@/components/awards/awards-page-client";
import { AWARDS } from "@/lib/content/awards";

/**
 * Màn `/awards` — Hệ thống giải thưởng SAA 2025.
 *
 * Server Component mỏng: đọc phiên đăng nhập thật + nội dung 6 hạng mục tĩnh,
 * rồi giao hết phần UI cho `AwardsPageClient`.
 *
 * **Nối phiên NGAY từ đầu, không hoãn tới phase-16** — bài học trực tiếp từ
 * phase-08 (`profile={null}` cứng làm người đã đăng nhập kẹt vòng lặp không
 * thoát được), đã áp dụng lại đúng khuôn ở `/kudos` (phase-09). Trang này có
 * header với menu tài khoản nên sẽ dính y hệt nếu bỏ qua. Xem
 * `plans/reports/debugger-260806-1347-header-mau-thuan-trang-thai-dang-nhap.md`.
 *
 * `verifySession()` bọc `cache()` nên hai lệnh gọi song song chỉ hỏi Supabase
 * Auth MỘT lần cho cả request.
 *
 * Ràng buộc Track A vẫn giữ nguyên ở tầng component: `components/awards/**`
 * không import `lib/data|actions|supabase|realtime` — chỉ file page này được phép.
 */
export default async function AwardsRoute() {
  const [profile, isAdmin] = await Promise.all([getCurrentProfile(), isCurrentUserAdmin()]);

  return (
    <AwardsPageClient
      awards={[...AWARDS].sort((a, b) => a.sortOrder - b.sortOrder)}
      profile={profile ? { name: profile.fullName, avatarUrl: profile.avatarUrl } : null}
      isAdmin={isAdmin}
      signOut={signOutAction}
    />
  );
}
