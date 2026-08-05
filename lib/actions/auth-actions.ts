"use server";

import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

/**
 * Đăng xuất — không có dialog xác nhận (spec dropdown-profile-admin). Server
 * Action là một trong hai chỗ Next 16 cho phép ghi cookie, nên việc huỷ cookie
 * session (`signOut()`) làm được ngay tại đây.
 */
export async function signOutAction(): Promise<void> {
  const supabase = await createClient();
  const { error } = await supabase.auth.signOut();

  if (error) {
    // Không chặn redirect vì lỗi ở đây hiếm khi khôi phục được (session đã
    // hết hạn/network) — vẫn đưa user về "/" để không kẹt lại màn cũ.
    console.error("[auth] signOut thất bại:", error.message);
  }

  redirect("/");
}
