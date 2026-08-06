"use client";

import { LoginScreen, type LoginScreenProps } from "./login-screen";

export interface LoginPageClientProps {
  errorCode?: LoginScreenProps["errorCode"];
}

/**
 * Boundary Client Component mỏng giữa Server Component `app/login/page.tsx` và
 * `LoginScreen`. Lý do tồn tại: Next.js không cho truyền một function thường
 * (không phải Server Action) từ Server Component xuống Client Component qua
 * props — nhưng contract `onGoogleLogin: () => void` của phase-16 lại cần một
 * callback đồng bộ thật, không phải Server Action. Nên `handleGoogleLogin`
 * (hiện là no-op placeholder) được định nghĩa NGAY TRONG boundary client này,
 * page.tsx chỉ truyền xuống `errorCode` — một string, hợp lệ qua props.
 */
export function LoginPageClient({ errorCode }: LoginPageClientProps) {
  function handleGoogleLogin() {
    // Placeholder — phase-16 sẽ thay bằng lời gọi signInWithGoogle() thật.
    console.log("[login] onGoogleLogin placeholder — phase-16 nối OAuth thật");
  }

  return <LoginScreen onGoogleLogin={handleGoogleLogin} errorCode={errorCode} />;
}
