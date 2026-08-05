"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";

import { isLocale, LOCALE_COOKIE } from "../i18n/config";

const ONE_YEAR_SECONDS = 60 * 60 * 24 * 365;

/**
 * Đổi ngôn ngữ giao diện.
 *
 * Đây là Server Action — chỉ ở Server Function / Route Handler mới GHI được
 * cookie. Server Component render không set cookie được (Next 16).
 */
export async function setLocale(next: string): Promise<void> {
  if (!isLocale(next)) {
    throw new Error(`Locale không hợp lệ: ${next}`);
  }

  const cookieStore = await cookies();
  cookieStore.set(LOCALE_COOKIE, next, {
    path: "/",
    maxAge: ONE_YEAR_SECONDS,
    sameSite: "lax",
  });

  // Layout đọc cookie lúc render nên phải làm mới toàn bộ cây.
  revalidatePath("/", "layout");
}
