import type { SupabaseClient } from "@supabase/supabase-js";

import { mapKudoRowToCard, type KudoCard, type KudoCardHashtag } from "@/lib/kudos/kudo-card-mapper";
import type { Database } from "@/lib/supabase/database.types";

export type SupabaseBrowserClient = SupabaseClient<Database>;

/**
 * Refetch một kudo card theo id, dùng ở CLIENT (browser) sau khi nhận tín hiệu
 * Broadcast — payload không bao giờ là nguồn dữ liệu (4 điều không được sai #1).
 * Đọc qua `public_kudos_feed`: trả `null` khi hàng bị lọc/không đủ quyền hoặc
 * đã xoá — gọi nơi dùng phải BỎ QUA, không hiện gì. Đây chính là chỗ luật che
 * ẩn danh được thực thi lại cho dữ liệu đến qua realtime (view đã che sender_*
 * cho kudo `is_anonymous`).
 *
 * Ownership note: phase-05 phát hiện `getKudoById` đã có sẵn ở
 * `lib/data/kudos-queries.ts` (phase-04) làm đúng việc này, nhưng nó dùng
 * Supabase SERVER client (đọc cookie qua `next/headers`) — không gọi được từ
 * hook 'use client'. Thay vì sửa file thuộc ownership phase-04, đặt bản dùng
 * Supabase BROWSER client tại đây, trong phạm vi `lib/realtime/**` của phase-05.
 * Cùng dùng chung `mapKudoRowToCard` — không viết mapper thứ hai.
 */
export async function fetchKudoCardById(
  supabase: SupabaseBrowserClient,
  id: number,
): Promise<KudoCard | null> {
  const { data, error } = await supabase
    .from("public_kudos_feed")
    .select("*")
    .eq("id", id)
    .maybeSingle();
  if (error) throw new Error(`fetchKudoCardById: ${error.message}`);
  if (!data) return null;

  const hashtags = await fetchHashtagsForKudo(supabase, id);
  return mapKudoRowToCard(data, hashtags);
}

/** Batch 2-query (kudos_hashtags rồi hashtags) — cùng cách làm với `fetchHashtagsForKudosIds` của phase-04, chỉ khác client và phạm vi 1 id. */
async function fetchHashtagsForKudo(
  supabase: SupabaseBrowserClient,
  kudosId: number,
): Promise<KudoCardHashtag[]> {
  const { data: links, error: linkError } = await supabase
    .from("kudos_hashtags")
    .select("hashtag_id")
    .eq("kudos_id", kudosId);
  if (linkError) throw new Error(`fetchHashtagsForKudo: ${linkError.message}`);
  if (!links || links.length === 0) return [];

  const hashtagIds = [...new Set(links.map((link) => link.hashtag_id))];
  const { data: hashtags, error: hashtagError } = await supabase
    .from("hashtags")
    .select("id, name")
    .in("id", hashtagIds);
  if (hashtagError) throw new Error(`fetchHashtagsForKudo: ${hashtagError.message}`);

  return (hashtags ?? []).map((hashtag) => ({ id: hashtag.id, name: hashtag.name }));
}
