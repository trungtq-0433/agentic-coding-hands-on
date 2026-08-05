import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr";

import type { Database } from "./database.types";

/**
 * Supabase client cho Server Component / Server Action / Route Handler.
 *
 * Next 16: `cookies()` là async — phải await. Cookie chỉ GHI được từ Server
 * Function hoặc Route Handler; gọi từ Server Component lúc render sẽ throw,
 * nên `setAll` nuốt lỗi và để `proxy.ts` lo việc làm mới cookie session.
 *
 * Chỉ dùng cặp getAll/setAll — API get/set/remove lẻ đã bị loại khỏi khuyến
 * nghị của @supabase/ssr vì làm hỏng cookie chunk.
 */
export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            for (const { name, value, options } of cookiesToSet) {
              cookieStore.set(name, value, options);
            }
          } catch {
            // Gọi từ Server Component — không ghi cookie được. Hợp lệ:
            // proxy.ts đã làm mới session cho request này rồi.
          }
        },
      },
    },
  );
}
