import { requireAdmin } from "@/lib/auth/dal";

/**
 * `/admin` — **placeholder có chủ đích**, đúng như bản đồ route ở `plan.md`
 * dòng 69 ("`/admin` placeholder").
 *
 * **Vì sao phải có file này ngay bây giờ:** `AccountMenu` (phase-06) render mục
 * "Quản trị" cho tài khoản admin và gọi `router.push("/admin")` — có 3 chỗ gọi
 * trong `components/`. `lib/auth/route-guard.ts` cũng đã khai `/admin` trong
 * `PROTECTED_PREFIXES` và `ADMIN_PREFIXES`. Nhưng KHÔNG có page nào, nên admin
 * bấm vào mục đó sẽ rơi thẳng vào 404 — một nút chết ngay trong menu chính.
 *
 * Trang này KHÔNG dựng chức năng quản trị nào (màn Admin thật nằm ngoài MVP,
 * xem mục "Còn treo" của `clarifications.md`). Nó chỉ làm hai việc: chặn quyền
 * thật và nói rõ trạng thái, để đường điều hướng không còn gãy.
 *
 * `requireAdmin()` là hàng rào THẬT (`lib/auth/dal.ts`) — `proxy.ts` chỉ kiểm
 * lạc quan theo session, không truy vấn DB nên không biết ai là admin.
 */
export default async function AdminPage() {
  await requireAdmin();

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-[1152px] flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="text-2xl font-bold text-[#FFEA9E]">Trang quản trị</h1>
      <p className="max-w-prose text-base text-white/70">
        Khu vực quản trị chưa nằm trong phạm vi MVP. Việc cấp thêm Secret Box hiện làm bằng tay qua
        RPC <code className="text-[#FFEA9E]">admin_grant_secret_box()</code> — xem{" "}
        <code className="text-[#FFEA9E]">docs/runbook-su-kien.md</code>.
      </p>
    </main>
  );
}
