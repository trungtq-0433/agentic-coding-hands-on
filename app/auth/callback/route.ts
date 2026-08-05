import { NextResponse, type NextRequest } from "next/server";
import type { SupabaseClient, User } from "@supabase/supabase-js";

import { createClient } from "@/lib/supabase/server";
import type { Database } from "@/lib/supabase/database.types";

/**
 * Route Handler nhận callback từ Google sau khi user đồng ý consent.
 *
 * `exchangeCodeForSession` PHẢI chạy trong Route Handler (một trong hai chỗ
 * duy nhất Next 16 cho phép ghi cookie, cùng với Server Action). Không có
 * `params`/`searchParams` động nên không cần `await ctx.params`.
 */
export async function GET(request: NextRequest) {
  const code = new URL(request.url).searchParams.get("code");

  if (!code) {
    return NextResponse.redirect(new URL("/login?error=oauth", request.url));
  }

  // try/catch bao ngoài: đây là điểm cuối của luồng đăng nhập, nơi người dùng
  // quay về từ Google. Một exception không lường trước (Supabase sập, DB rớt,
  // metadata dị dạng) mà lọt ra sẽ thành trang 500 trần — user không hiểu gì và
  // không có đường đi tiếp. Mọi hỏng hóc phải quy về cùng một chỗ hạ cánh:
  // /login?error=oauth, nơi UI hiển thị thông báo thử lại (spec Login item 2.2.1).
  try {
    const supabase = await createClient();
    const { data, error } = await supabase.auth.exchangeCodeForSession(code);

    if (error || !data.user) {
      console.error("[auth/callback] exchangeCodeForSession thất bại:", error?.message);
      return NextResponse.redirect(new URL("/login?error=oauth", request.url));
    }

    // Trigger handle_new_user() (0007) đã bootstrap profiles/user_roles nếu đây
    // là lần đăng nhập đầu. Đồng bộ lại full_name/avatar_url từ metadata Google
    // mới nhất — Google có thể đổi tên/ảnh giữa các lần đăng nhập.
    await syncProfileFromIdentity(supabase, data.user);

    return NextResponse.redirect(new URL("/", request.url));
  } catch (unexpected) {
    console.error("[auth/callback] lỗi không lường trước:", unexpected);
    return NextResponse.redirect(new URL("/login?error=oauth", request.url));
  }
}

/**
 * Đồng bộ full_name/avatar_url qua RPC `sync_profile_from_google` — profiles
 * không có UPDATE grant trực tiếp cho authenticated (0006_views_and_rls.sql),
 * đây là đường ghi duy nhất ngoài trigger bootstrap (xem comment trong
 * 0007_auth_bootstrap_trigger.sql). Lỗi đồng bộ KHÔNG chặn đăng nhập — user
 * vẫn có profile hợp lệ từ trigger, chỉ tên/ảnh có thể tạm cũ.
 */
async function syncProfileFromIdentity(
  supabase: SupabaseClient<Database>,
  user: User,
): Promise<void> {
  const metadata = user.user_metadata ?? {};
  const fullName =
    typeof metadata.full_name === "string"
      ? metadata.full_name
      : typeof metadata.name === "string"
        ? metadata.name
        : null;
  const avatarUrl =
    typeof metadata.avatar_url === "string"
      ? metadata.avatar_url
      : typeof metadata.picture === "string"
        ? metadata.picture
        : null;

  if (!fullName && !avatarUrl) return;

  const { error } = await supabase.rpc("sync_profile_from_google", {
    p_full_name: fullName ?? "",
    // Kiểu sinh tự động khai `p_avatar_url: string` — generator không mã hoá
    // nullability cho tham số hàm SQL (khác cột bảng). Cột thật nhận NULL bình
    // thường, hàm SQL tự `coalesce(p_avatar_url, avatar_url)`, nên cast ở đây
    // là an toàn, không phải né kiểm tra thật.
    p_avatar_url: avatarUrl as string,
  });

  if (error) {
    console.error("[auth/callback] Đồng bộ profile thất bại:", error.message);
  }
}
