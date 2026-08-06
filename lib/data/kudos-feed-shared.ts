import { createClient } from "@/lib/supabase/server";
import { encodeCursor } from "@/lib/kudos/cursor";
import { mapKudoRowToCard, type KudoCard, type KudoCardHashtag } from "@/lib/kudos/kudo-card-mapper";
import type { Database } from "@/lib/supabase/database.types";

/**
 * Phần dùng chung giữa `kudos-queries.ts` (board/feed công khai) và
 * `profile-queries.ts` (nhận/gửi của một profile) — cùng một khuôn keyset
 * `(created_at, id)` (Key Insight #6) và cùng cách gắn hashtag cho card, chỉ
 * khác nguồn view/bộ lọc. Không export ra ngoài `lib/data/**`.
 */

export type SupabaseServerClient = Awaited<ReturnType<typeof createClient>>;

type FeedRow =
  | Database["public"]["Views"]["public_kudos_feed"]["Row"]
  | Database["public"]["Views"]["my_sent_kudos"]["Row"];

export interface KudosPage {
  items: KudoCard[];
  nextCursor: string | null;
}

/**
 * Batch-fetch hashtag {id, name} cho một danh sách kudos_id — 2 query rời
 * (kudos_hashtags rồi hashtags) để không phụ thuộc suy luận kiểu embed của
 * supabase-js.
 */
export async function fetchHashtagsForKudosIds(
  supabase: SupabaseServerClient,
  kudosIds: number[],
): Promise<Map<number, KudoCardHashtag[]>> {
  const map = new Map<number, KudoCardHashtag[]>();
  if (kudosIds.length === 0) return map;

  const { data: links, error: linkError } = await supabase
    .from("kudos_hashtags")
    .select("kudos_id, hashtag_id")
    .in("kudos_id", kudosIds);
  if (linkError) throw new Error(`fetchHashtagsForKudosIds: ${linkError.message}`);
  if (!links || links.length === 0) return map;

  const hashtagIds = [...new Set(links.map((link) => link.hashtag_id))];
  const { data: hashtags, error: hashtagError } = await supabase
    .from("hashtags")
    .select("id, name")
    .in("id", hashtagIds);
  if (hashtagError) throw new Error(`fetchHashtagsForKudosIds: ${hashtagError.message}`);

  const nameById = new Map((hashtags ?? []).map((hashtag) => [hashtag.id, hashtag.name]));
  for (const link of links) {
    const name = nameById.get(link.hashtag_id);
    if (!name) continue;
    const list = map.get(link.kudos_id) ?? [];
    list.push({ id: link.hashtag_id, name });
    map.set(link.kudos_id, list);
  }
  return map;
}

/**
 * Ghép trang keyset từ kết quả thô đã fetch dư 1 hàng (`limit + 1`): cắt về
 * đúng `limit`, batch-fetch hashtag, dựng `nextCursor` từ hàng cuối nếu còn
 * trang sau (`decodeCursor` ở phía gọi trả `null` cho cursor rác — Risk
 * Assessment "Keyset cursor rác từ URL làm sập trang").
 */
export async function buildKudosPage(
  supabase: SupabaseServerClient,
  rows: FeedRow[],
  limit: number,
): Promise<KudosPage> {
  const hasMore = rows.length > limit;
  const pageRows = hasMore ? rows.slice(0, limit) : rows;
  const pageIds = pageRows.map((row) => row.id).filter((id): id is number => id !== null);

  const hashtagsByKudoId = await fetchHashtagsForKudosIds(supabase, pageIds);
  const items = pageRows.map((row) => mapKudoRowToCard(row, hashtagsByKudoId.get(row.id ?? -1) ?? []));

  const last = pageRows.at(-1);
  const nextCursor =
    hasMore && last && last.created_at !== null && last.id !== null
      ? encodeCursor({ createdAt: last.created_at, id: last.id })
      : null;

  return { items, nextCursor };
}
