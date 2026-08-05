import { NextResponse, type NextRequest } from "next/server";
import { createServerClient } from "@supabase/ssr";

import type { Database } from "./database.types";

/**
 * Làm mới session Supabase cho mỗi request, chạy từ `proxy.ts`.
 *
 * Cookie mới phải ghi lên CẢ request lẫn response: request để Server Component
 * phía sau đọc được session vừa refresh, response để trình duyệt lưu lại.
 *
 * Trả về `user` để proxy khỏi phải gọi getUser() lần hai.
 */
export async function updateSession(request: NextRequest) {
  let response = NextResponse.next({ request });

  const supabase = createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          for (const { name, value } of cookiesToSet) {
            request.cookies.set(name, value);
          }
          response = NextResponse.next({ request });
          for (const { name, value, options } of cookiesToSet) {
            response.cookies.set(name, value, options);
          }
        },
      },
    },
  );

  // KHÔNG chèn bất kỳ code nào giữa createServerClient và getUser().
  // Chen vào giữa là dễ sinh lỗi đăng xuất ngẫu nhiên rất khó truy.
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return { response, user };
}
