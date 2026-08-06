"use server";

import { revalidatePath } from "next/cache";

import { requireUser } from "@/lib/auth/dal";
import { createClient } from "@/lib/supabase/server";
import { mapRpcErrorCode } from "@/lib/kudos/rpc-error";

export type OpenSecretBoxErrorCode = "UNAUTHENTICATED" | "NO_UNOPENED_BOX" | "UNKNOWN";

export type OpenSecretBoxResult =
  | { ok: true; badgeId: number; badgeCode: string; remaining: number }
  | { ok: false; code: OpenSecretBoxErrorCode };

const RPC_KNOWN_CODES = ["UNAUTHENTICATED", "NO_UNOPENED_BOX"] as const;

/**
 * Mở Secret Box qua RPC `open_secret_box()` — server-authoritative hoàn toàn
 * (Requirements: "Số hộp chưa mở luôn từ server"). Hết hộp → RPC raise
 * `NO_UNOPENED_BOX`, action dịch thành lỗi có mã, KHÔNG tạo badge và KHÔNG
 * throw (Implementation Steps bước 12).
 */
export async function openSecretBoxAction(): Promise<OpenSecretBoxResult> {
  await requireUser();

  const supabase = await createClient();
  const { data, error } = await supabase.rpc("open_secret_box");

  if (error) {
    const code = mapRpcErrorCode(error, RPC_KNOWN_CODES, "UNKNOWN" as const);
    return { ok: false, code };
  }

  const result = data?.[0];
  if (!result) {
    return { ok: false, code: "UNKNOWN" };
  }

  revalidatePath("/kudos");
  revalidatePath("/profile");

  return { ok: true, badgeId: result.badge_id, badgeCode: result.badge_code, remaining: result.remaining };
}
