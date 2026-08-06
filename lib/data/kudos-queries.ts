import { createClient } from "@/lib/supabase/server";
import { decodeCursor } from "@/lib/kudos/cursor";
import { mapKudoRowToCard, type KudoCard } from "@/lib/kudos/kudo-card-mapper";
import { UNASSIGNED_DEPARTMENT_ID } from "@/lib/data/master-queries";
import {
  buildKudosPage,
  fetchHashtagsForKudosIds,
  type KudosPage,
  type SupabaseServerClient,
} from "@/lib/data/kudos-feed-shared";

const DEFAULT_PAGE_SIZE = 20;
const HIGHLIGHT_LIMIT = 5;

export interface KudoFeedFilters {
  hashtagId?: number;
  departmentId?: number | typeof UNASSIGNED_DEPARTMENT_ID;
}

export interface ListKudosOptions extends KudoFeedFilters {
  /** Cursor mã hoá (base64url) từ trang trước — không phải OFFSET (Key Insight #6). */
  cursor?: string | null;
  limit?: number;
}

/**
 * All Kudos: keyset cursor `(created_at, id)`, page mặc định 20, lọc theo
 * hashtag và/hoặc phòng ban NGƯỜI NHẬN (Implementation Steps bước 8). Đọc
 * CHỈ qua `public_kudos_feed` — không bao giờ `.from('kudos')`.
 */
export async function listKudos(options: ListKudosOptions = {}): Promise<KudosPage> {
  const limit = options.limit ?? DEFAULT_PAGE_SIZE;
  const supabase = await createClient();

  const kudosIdFilter = await resolveKudosIdsForHashtag(supabase, options.hashtagId);
  if (kudosIdFilter !== null && kudosIdFilter.length === 0) {
    return { items: [], nextCursor: null };
  }

  const recipientIdFilter = await resolveRecipientIdsForDepartment(supabase, options.departmentId);
  if (recipientIdFilter !== null && recipientIdFilter.length === 0) {
    return { items: [], nextCursor: null };
  }

  let query = supabase
    .from("public_kudos_feed")
    .select("*")
    .order("created_at", { ascending: false })
    .order("id", { ascending: false })
    // +1 để biết còn trang sau hay không, không phải để hiển thị.
    .limit(limit + 1);

  if (kudosIdFilter !== null) query = query.in("id", kudosIdFilter);
  if (recipientIdFilter !== null) query = query.in("recipient_id", recipientIdFilter);

  const cursor = decodeCursor(options.cursor);
  if (cursor) {
    // (created_at, id) < (cursor.createdAt, cursor.id) — điều kiện keyset đúng
    // thứ tự sắp xếp desc,desc ở trên (Key Insight #6).
    query = query.or(
      `created_at.lt.${cursor.createdAt},and(created_at.eq.${cursor.createdAt},id.lt.${cursor.id})`,
    );
  }

  const { data, error } = await query;
  if (error) throw new Error(`listKudos: ${error.message}`);

  return buildKudosPage(supabase, data ?? [], limit);
}

/** Highlight: top-5 theo `heart_count desc, created_at desc`, cùng bộ lọc với `listKudos`. */
export async function listHighlightKudos(filters: KudoFeedFilters = {}): Promise<KudoCard[]> {
  const supabase = await createClient();

  const kudosIdFilter = await resolveKudosIdsForHashtag(supabase, filters.hashtagId);
  if (kudosIdFilter !== null && kudosIdFilter.length === 0) return [];

  const recipientIdFilter = await resolveRecipientIdsForDepartment(supabase, filters.departmentId);
  if (recipientIdFilter !== null && recipientIdFilter.length === 0) return [];

  let query = supabase
    .from("public_kudos_feed")
    .select("*")
    .order("heart_count", { ascending: false })
    .order("created_at", { ascending: false })
    .limit(HIGHLIGHT_LIMIT);

  if (kudosIdFilter !== null) query = query.in("id", kudosIdFilter);
  if (recipientIdFilter !== null) query = query.in("recipient_id", recipientIdFilter);

  const { data, error } = await query;
  if (error) throw new Error(`listHighlightKudos: ${error.message}`);

  const rows = data ?? [];
  const ids = rows.map((row) => row.id).filter((id): id is number => id !== null);
  const hashtagsByKudoId = await fetchHashtagsForKudosIds(supabase, ids);
  return rows.map((row) => mapKudoRowToCard(row, hashtagsByKudoId.get(row.id ?? -1) ?? []));
}

/** Chi tiết một kudo (permalink "copy link", modal detail). `null` nếu không tồn tại. */
export async function getKudoById(id: number): Promise<KudoCard | null> {
  const supabase = await createClient();
  const { data, error } = await supabase.from("public_kudos_feed").select("*").eq("id", id).maybeSingle();
  if (error) throw new Error(`getKudoById: ${error.message}`);
  if (!data) return null;

  const hashtagsByKudoId = await fetchHashtagsForKudosIds(supabase, [id]);
  return mapKudoRowToCard(data, hashtagsByKudoId.get(id) ?? []);
}

/** Tổng số kudos công khai — nguồn số "388 KUDOS" ở Spotlight. */
export async function countKudos(): Promise<number> {
  const supabase = await createClient();
  const { count, error } = await supabase
    .from("public_kudos_feed")
    .select("*", { count: "exact", head: true });
  if (error) throw new Error(`countKudos: ${error.message}`);
  return count ?? 0;
}

export interface SpotlightName {
  name: string;
  weight: number;
}

const SPOTLIGHT_NAME_LIMIT = 100;

/**
 * Danh sách tên cho word-cloud Spotlight, trọng số = số kudo ĐÃ NHẬN (tôn vinh
 * người được cảm ơn, không phải người gửi). Query lúc tải trang, không
 * realtime (clarifications gap #13). Giới hạn 100 tên nổi bật nhất.
 */
export async function listSpotlightNames(): Promise<SpotlightName[]> {
  const supabase = await createClient();
  const { data, error } = await supabase.from("public_kudos_feed").select("recipient_full_name");
  if (error) throw new Error(`listSpotlightNames: ${error.message}`);

  const weights = new Map<string, number>();
  for (const row of data ?? []) {
    if (!row.recipient_full_name) continue;
    weights.set(row.recipient_full_name, (weights.get(row.recipient_full_name) ?? 0) + 1);
  }

  return [...weights.entries()]
    .map(([name, weight]) => ({ name, weight }))
    .sort((a, b) => b.weight - a.weight)
    .slice(0, SPOTLIGHT_NAME_LIMIT);
}

/** `undefined` → không lọc (null). Mảng rỗng → lọc match 0 kudo (gọi nơi dùng trả rỗng ngay, khỏi query feed). */
async function resolveKudosIdsForHashtag(
  supabase: SupabaseServerClient,
  hashtagId: number | undefined,
): Promise<number[] | null> {
  if (hashtagId === undefined) return null;

  const { data, error } = await supabase.from("kudos_hashtags").select("kudos_id").eq("hashtag_id", hashtagId);
  if (error) throw new Error(`resolveKudosIdsForHashtag: ${error.message}`);
  return (data ?? []).map((row) => row.kudos_id);
}

/**
 * Lọc phòng ban NGƯỜI NHẬN qua bảng `profiles` (view feed không có cột
 * `recipient_department_id` — xem Deviations trong báo cáo bàn giao cuối
 * phase-04). `departmentId === 'unassigned'` gom mọi profile
 * `department_id is null` (Key Insight #9).
 */
async function resolveRecipientIdsForDepartment(
  supabase: SupabaseServerClient,
  departmentId: number | typeof UNASSIGNED_DEPARTMENT_ID | undefined,
): Promise<string[] | null> {
  if (departmentId === undefined) return null;

  const query = supabase.from("profiles").select("id");
  const filtered =
    departmentId === UNASSIGNED_DEPARTMENT_ID
      ? query.is("department_id", null)
      : query.eq("department_id", departmentId);

  const { data, error } = await filtered;
  if (error) throw new Error(`resolveRecipientIdsForDepartment: ${error.message}`);
  return (data ?? []).map((row) => row.id);
}
