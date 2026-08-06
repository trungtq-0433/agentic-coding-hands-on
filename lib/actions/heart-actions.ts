"use server";

import { revalidatePath } from "next/cache";

import { requireUser } from "@/lib/auth/dal";
import { createClient } from "@/lib/supabase/server";
import { mapRpcErrorCode } from "@/lib/kudos/rpc-error";

export type ToggleHeartErrorCode = "UNAUTHENTICATED" | "SELF_HEART" | "NOT_FOUND" | "UNKNOWN";

export type ToggleHeartResult =
  | { ok: true; hearted: boolean; heartCount: number }
  | { ok: false; code: ToggleHeartErrorCode };

/**
 * RPC raise `KUDOS_NOT_FOUND` — đổi tên thành `NOT_FOUND` ở CHÍNH ranh giới
 * action để khớp đúng bộ code mà UI/spec mong đợi (Bốn điều không được sai #3:
 * "heart-actions cũng phải có nhánh lỗi SELF_HEART/NOT_FOUND/UNAUTHENTICATED").
 */
const RPC_KNOWN_CODES = ["UNAUTHENTICATED", "SELF_HEART", "KUDOS_NOT_FOUND"] as const;

/**
 * Toggle tim qua RPC `toggle_heart`. KHÔNG throw lỗi nghiệp vụ — ban đầu action
 * này từng trả thẳng `{hearted, heartCount}` không nhánh lỗi, khiến UI không
 * phân biệt được "server từ chối" với "mạng hỏng" (Implementation Steps bước
 * 11). RPC tự lo chống race (for update + on conflict do nothing) và tự tra
 * bonus ngày đặc biệt — action chỉ gọi và dịch lỗi, không thêm luật nghiệp vụ.
 */
export async function toggleHeartAction(kudoId: number): Promise<ToggleHeartResult> {
  await requireUser();

  const supabase = await createClient();
  const { data, error } = await supabase.rpc("toggle_heart", { p_kudos_id: kudoId });

  if (error) {
    const rawCode = mapRpcErrorCode(error, RPC_KNOWN_CODES, "UNKNOWN" as const);
    const code: ToggleHeartErrorCode = rawCode === "KUDOS_NOT_FOUND" ? "NOT_FOUND" : rawCode;
    return { ok: false, code };
  }

  const result = data?.[0];
  if (!result) {
    return { ok: false, code: "UNKNOWN" };
  }

  revalidatePath("/kudos");
  revalidatePath("/profile");

  return { ok: true, hearted: result.hearted, heartCount: result.heart_count };
}
