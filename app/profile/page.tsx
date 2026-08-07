import { notFound } from "next/navigation";

import type { DepartmentOption } from "@/lib/data/master-queries";

import { signOutAction } from "@/lib/actions/auth-actions";
import { getCurrentProfile, isCurrentUserAdmin, requireUser } from "@/lib/auth/dal";
import { listDepartments } from "@/lib/data/master-queries";
import { findMockOtherProfile } from "@/components/profile/figma-profile-mock";
import { ProfilePageClient } from "@/components/profile/profile-page-client";
import { resolveProfileIdParam } from "@/components/profile/validate-profile-id";
import type { ProfileStats, ProfileSummary } from "@/components/profile/profile-types";

/**
 * `department_id` → tên hiển thị. Trả `null` khi chưa gán phòng ban, để
 * `ProfileHero` ẩn hẳn dòng đó (TC_WEB_PROFILE_GUI_009) thay vì hiện chuỗi rỗng.
 * KHÔNG rơi về mục ảo "Chưa phân loại": mục đó dành cho bộ lọc ở Live board,
 * dùng làm nhãn profile sẽ thành khẳng định sai rằng người này thuộc một phòng
 * ban tên như vậy.
 */
function resolveDepartmentName(
  departments: DepartmentOption[],
  departmentId: number | null,
): string | null {
  if (departmentId === null) return null;
  return departments.find((d) => d.id === departmentId)?.name ?? null;
}

/**
 * Màn `/profile` — Server Component mỏng, đúng khuôn `app/kudos/page.tsx`
 * (phase-09): nối phiên đăng nhập thật NGAY (không hoãn tới phase-16, bài học
 * "phase-09..12" trong clarifications.md), giao hết phần UI/tương tác cho
 * `ProfilePageClient`.
 *
 * Next 16: `searchParams` là Promise, PHẢI `await` trước khi đọc (không dùng
 * `PageProps<'/profile'>` toàn cục — kiểu đó do `next dev` sinh lại từ đĩa mỗi
 * khi route mới xuất hiện, và `npx tsc --noEmit` có thể chạy trước khi file đó
 * kịp regen; khai type nội bộ ở đây tránh phụ thuộc thời điểm).
 *
 * **`/profile` (chính mình) và `/profile?id=` (người khác) là HAI MẶT của cùng
 * route** — quyết định bởi `resolveProfileIdParam` (hàm thuần, test được riêng ở
 * `components/profile/validate-profile-id.ts`), KHÔNG phải bởi hai route khác nhau.
 *
 * **Track B ngoài phạm vi phase này**: query `profiles`/`public_kudos_feed`/
 * `my_sent_kudos` thật, definer view Sent-list, keyset pagination, thả tim thật
 * → phase-16. Ở đây CHỈ có auth thật (`requireUser`/`getCurrentProfile`, vì đó
 * đã là hạ tầng có sẵn từ phase-03, giống hệt cách `app/kudos/page.tsx` dùng nó)
 * và dữ liệu MOCK cho phần còn lại — id của "profile người khác" khớp đúng 8
 * hàng demo trong `supabase/seed.sql` nên khi phase-16 nối query thật, không
 * cần đổi id nào ở phía UI.
 */
export default async function ProfileRoute({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  // `requireUser()` tự redirect `/login` khi chưa đăng nhập (TC_WEB_PROFILE_ACC_001)
  // — đây là lớp bảo vệ THẬT (`lib/auth/dal.ts`), không phải middleware lạc quan.
  const viewer = await requireUser();
  const params = await searchParams;
  const resolution = resolveProfileIdParam(params.id, viewer.id);

  if (resolution.kind === "invalid") {
    // `?id` sai khuôn UUID, hoặc lặp (`?id=a&id=b`) — chặn TRƯỚC khi chạm dữ
    // liệu (TC_WEB_PROFILE_FUN_004/005), không để lộ 500 từ Postgres 22P02.
    notFound();
  }

  const [selfProfile, isAdmin, departments] = await Promise.all([
    getCurrentProfile(),
    isCurrentUserAdmin(),
    listDepartments(),
  ]);
  if (!selfProfile) {
    // Phòng hờ: `requireUser()` xác nhận có session thật, nhưng nếu vì lý do gì
    // đó bảng `profiles` chưa có hàng tương ứng (trigger `handle_new_user` lẽ ra
    // đã tạo) thì đây là dữ liệu hỏng, không phải luồng người dùng bình thường.
    notFound();
  }

  const headerProfile = { name: selfProfile.fullName, avatarUrl: selfProfile.avatarUrl };

  if (resolution.kind === "self") {
    const profile: ProfileSummary = {
      id: selfProfile.id,
      fullName: selfProfile.fullName,
      avatarUrl: selfProfile.avatarUrl,
      /* Tên phòng ban resolve từ `listDepartments()` (Track B). Server Component
         gọi được vì đây là file của `app/`, cùng khuôn `app/kudos/page.tsx` đã
         ship — `components/profile/**` vẫn tuyệt đối không chạm Track B.

         ⚠ Vẫn `null` với tài khoản đăng nhập Google THẬT, và đó không phải lỗi ở
         đây: `handle_new_user()` tạo profile không kèm phòng ban nên
         `department_id` là NULL (Red Team #6 — "không có đường gán"). Kiểm bằng
         DB: 8/9 profile seed có phòng ban, đúng 1 profile NULL là tài khoản
         Google thật. Muốn thấy dòng này thì phải gán `department_id` cho tài
         khoản đó; TC_WEB_PROFILE_GUI_009 xác nhận NULL → ẩn dòng là đúng. */
      departmentName: resolveDepartmentName(departments, selfProfile.departmentId),
      starCount: selfProfile.starCount,
      receivedKudosCount: selfProfile.receivedKudosCount,
    };
    const stats: ProfileStats = {
      receivedKudos: selfProfile.receivedKudosCount,
      // MOCK: cột `sent_kudos_count` bị loại khỏi grant công khai (phase-02) vì
      // suy ra được số kudos ẩn danh đã gửi; số THẬT phải qua `my_sent_kudos`
      // (definer view, Track B, phase-16). Giữ một số cố định nhỏ để dropdown/
      // feed "Đã gửi" có gì đó kiểm được (TC_WEB_PROFILE_FUN_009/010/011).
      sentKudos: 6,
      hearts: selfProfile.receivedHeartsCount,
      // Luôn 0 — quy tắc cấp Secret Box chưa chốt (clarifications gap #9).
      openedBoxes: 0,
      unopenedBoxes: 0,
    };

    return (
      <ProfilePageClient
        headerProfile={headerProfile}
        isAdmin={isAdmin}
        signOut={signOutAction}
        profile={profile}
        stats={stats}
      />
    );
  }

  // resolution.kind === "other": tra mock theo id khớp `seed.sql` (Track B thật nối ở phase-16).
  const otherProfile = findMockOtherProfile(resolution.id);
  if (!otherProfile) {
    // UUID đúng khuôn nhưng không khớp Sunner nào đã biết (TC_WEB_PROFILE_FUN_003).
    notFound();
  }

  return (
    <ProfilePageClient
      headerProfile={headerProfile}
      isAdmin={isAdmin}
      signOut={signOutAction}
      profile={otherProfile}
      stats={null}
    />
  );
}
