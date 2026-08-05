import { cache } from "react";
import { redirect } from "next/navigation";
import type { User } from "@supabase/supabase-js";

import { createClient } from "@/lib/supabase/server";
import { toPublicProfile, type PublicProfile } from "./dto";

/**
 * Data Access Layer cho auth — lớp bảo vệ THẬT (không phải proxy.ts, chỉ là
 * UX lạc quan). Gọi trong page/Server Action, KHÔNG gọi trong layout — layout
 * không re-render mỗi lần navigate (Partial Rendering) nên không bắt được
 * trường hợp user điều hướng client-side vào route cần bảo vệ.
 *
 * `cache()` đảm bảo một request chỉ hỏi Supabase Auth một lần dù nhiều nơi
 * trong cây component cùng gọi verifySession().
 */
export const verifySession = cache(async (): Promise<User | null> => {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  return user ?? null;
});

/** Bắt buộc có session, không thì redirect `/login`. Trả về user thật (có email) —
 * chỉ dùng nội bộ trong page/Server Action, KHÔNG bao giờ trả thẳng ra client. */
export async function requireUser(): Promise<User> {
  const user = await verifySession();
  if (!user) {
    redirect("/login");
  }
  return user;
}

/**
 * Bắt buộc là admin. Query bảng `user_roles` mới nhất mỗi lần gọi (không dựa
 * JWT claim) — nhờ vậy gỡ quyền admin trong Studio có hiệu lực ngay ở request
 * kế tiếp, không cần user đăng xuất/đăng nhập lại.
 */
export async function requireAdmin(): Promise<User> {
  const user = await requireUser();
  const admin = await isCurrentUserAdmin();
  if (!admin) {
    redirect("/");
  }
  return user;
}

/** Có phải admin không. Guest hoặc lỗi truy vấn → false (fail-closed). */
export async function isCurrentUserAdmin(): Promise<boolean> {
  const user = await verifySession();
  if (!user) return false;

  const supabase = await createClient();
  const { data, error } = await supabase
    .from("user_roles")
    .select("role")
    .eq("user_id", user.id)
    .maybeSingle();

  if (error) {
    console.error("[auth/dal] Không đọc được user_roles:", error.message);
    return false;
  }
  return data?.role === "admin";
}

/** Profile công khai của user đang đăng nhập, đã lọc qua DTO. Guest → null. */
export async function getCurrentProfile(): Promise<PublicProfile | null> {
  const user = await verifySession();
  if (!user) return null;

  const supabase = await createClient();
  const { data, error } = await supabase
    .from("profiles")
    .select(
      "id, full_name, avatar_url, department_id, received_kudos_count, received_hearts_count, created_at",
    )
    .eq("id", user.id)
    .maybeSingle();

  if (error || !data) {
    if (error) {
      console.error("[auth/dal] Không đọc được profile:", error.message);
    }
    return null;
  }
  return toPublicProfile(data);
}
