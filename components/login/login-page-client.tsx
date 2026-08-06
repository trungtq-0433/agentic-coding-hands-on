"use client";

import { signInWithGoogle } from "@/lib/auth/sign-in-with-google";

import { LoginScreen, type LoginScreenProps } from "./login-screen";

export interface LoginPageClientProps {
  errorCode?: LoginScreenProps["errorCode"];
}

/**
 * Boundary Client Component mỏng giữa Server Component `app/login/page.tsx` và
 * `LoginScreen`. Lý do tồn tại: Next.js không cho truyền một function thường
 * (không phải Server Action) từ Server Component xuống Client Component qua
 * props — nhưng contract `onGoogleLogin: () => void` cần một callback đồng bộ
 * thật, không phải Server Action. Nên `handleGoogleLogin` được định nghĩa NGAY
 * TRONG boundary client này; page.tsx chỉ truyền xuống `errorCode` — một
 * string, hợp lệ qua props.
 */
export function LoginPageClient({ errorCode }: LoginPageClientProps) {
  function handleGoogleLogin() {
    // signInWithGoogle là async (chuyển hướng sang Google), nhưng contract
    // `onGoogleLogin: () => void` là đồng bộ — nuốt promise ở đây và ghi log
    // nếu hỏng. Lỗi sau khi quay về được xử ở /auth/callback → /login?error=oauth.
    void signInWithGoogle().catch((error: unknown) => {
      console.error("[login] không khởi động được luồng Google OAuth:", error);
    });
  }

  return <LoginScreen onGoogleLogin={handleGoogleLogin} errorCode={errorCode} />;
}
