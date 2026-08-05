import { createClient } from "@/lib/supabase/client";

/**
 * Helper client-side khởi động luồng Google OAuth. KHÔNG giới hạn domain —
 * spec Login item 2.2.1 cho phép MỌI tài khoản Google đăng nhập.
 *
 * Chỉ gọi được từ Client Component (dùng `window.location.origin`). UI nút
 * bấm thật thuộc Track A phase-07/phase-16 — hàm này chỉ là logic dùng lại.
 */
export async function signInWithGoogle(): Promise<void> {
  const supabase = createClient();
  const { error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: {
      redirectTo: `${window.location.origin}/auth/callback`,
    },
  });

  if (error) {
    console.error("[auth] signInWithOAuth thất bại:", error.message);
    throw error;
  }
}
