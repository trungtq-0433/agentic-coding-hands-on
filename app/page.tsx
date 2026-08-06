import { signOutAction } from "@/lib/actions/auth-actions";
import { getCurrentProfile, isCurrentUserAdmin } from "@/lib/auth/dal";
import { HomePageClient } from "@/components/home/home-page-client";

/**
 * Trang chủ `/` — thay hoàn toàn trang mặc định của create-next-app.
 *
 * `NEXT_PUBLIC_EVENT_START_AT` bị **inline vào bundle lúc build**, không đọc lúc
 * chạy — đổi ngày thì BẮT BUỘC chạy lại `next build`, restart process là không
 * đủ (`node_modules/next/dist/docs/01-app/02-guides/environment-variables.md`).
 * Vì vậy phải viết `process.env.NEXT_PUBLIC_EVENT_START_AT` nguyên dạng, không
 * gán qua biến trung gian — bundler chỉ thay thế được khi thấy đúng mẫu đó.
 * Thiếu biến → chuỗi rỗng; `CountdownDigits` coi giá trị không parse được là
 * "đã qua mốc" và hiện `00 00 00` thay vì làm vỡ trang.
 *
 * **Nối phiên đăng nhập (2026-08-06, kéo sớm một phần phase-16).**
 * Trước đó file này truyền cứng `profile={null}` theo đúng ranh giới Track A/B
 * của plan. Nhưng `proxy.ts` lại đọc cookie THẬT để quyết định điều hướng, nên
 * trang có HAI nguồn sự thật khác nhau về "đã đăng nhập chưa": người đã đăng
 * nhập bị `/login` đá về `/`, mà `/` vẫn vẽ nút "Đăng nhập" — bấm vào thì quay
 * lại đúng chỗ cũ, không có đường nào thoát. Xem báo cáo debug cùng ngày.
 *
 * `verifySession()` bọc `cache()` nên hai lệnh gọi dưới đây chỉ hỏi Supabase
 * Auth MỘT lần cho cả request, dù chạy song song.
 *
 * `signOutAction` là Server Action — đây là lý do nó truyền được xuống Client
 * Component qua props, trong khi function thường thì không.
 */
export default async function HomePageRoute() {
  const targetIso = process.env.NEXT_PUBLIC_EVENT_START_AT ?? "";
  const [profile, isAdmin] = await Promise.all([getCurrentProfile(), isCurrentUserAdmin()]);

  return (
    <HomePageClient
      targetIso={targetIso}
      // Thu hẹp `PublicProfile` xuống đúng 2 trường `AccountMenu` cần. Không
      // đẩy nguyên DTO xuống client: các trường đếm (received_kudos_count...)
      // không liên quan gì tới header.
      profile={profile ? { name: profile.fullName, avatarUrl: profile.avatarUrl } : null}
      isAdmin={isAdmin}
      signOut={signOutAction}
    />
  );
}
