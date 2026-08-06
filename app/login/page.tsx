import { LoginPageClient } from "@/components/login/login-page-client";

/**
 * Server Component — chỉ đọc `searchParams` (Next 16: Promise, PHẢI await) rồi
 * giao hết phần UI/tương tác cho `LoginPageClient`. Không tự truyền function
 * xuống Client Component qua props (xem docblock trong `login-page-client.tsx`).
 */
export default async function LoginPage({ searchParams }: PageProps<"/login">) {
  const params = await searchParams;
  const errorCode = params.error === "oauth" ? "oauth" : undefined;

  return <LoginPageClient errorCode={errorCode} />;
}
