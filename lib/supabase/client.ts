import { createBrowserClient } from "@supabase/ssr";

import type { Database } from "./database.types";

/**
 * Supabase client cho Client Component.
 *
 * Chỉ dùng anon/publishable key — key này công khai được, RLS mới là hàng rào thật.
 * Không bao giờ đưa service_role key vào đây (nó không có tiền tố NEXT_PUBLIC_
 * chính là để tránh chuyện đó).
 */
export function createClient() {
  return createBrowserClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
  );
}
