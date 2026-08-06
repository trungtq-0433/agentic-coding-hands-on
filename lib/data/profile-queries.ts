import { createClient } from "@/lib/supabase/server";
import { toPublicProfile, type PublicProfile } from "@/lib/auth/dto";
import { decodeCursor } from "@/lib/kudos/cursor";
import { getUnopenedCount } from "@/lib/data/secret-box-queries";
import { buildKudosPage, type KudosPage } from "@/lib/data/kudos-feed-shared";

const DEFAULT_PAGE_SIZE = 20;
const MAX_SEARCH_LENGTH = 100;
const SEARCH_RESULT_LIMIT = 20;

export interface ListKudosPageOptions {
  cursor?: string | null;
  limit?: number;
}

/**
 * Profile công khai của một user, đúng bộ cột được grant (0006_views_and_rls.sql
 * — KHÔNG có `sent_kudos_count`, xem `lib/auth/dto.ts`). `null` nếu không tồn tại.
 */
export async function getProfile(id: string): Promise<PublicProfile | null> {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("profiles")
    .select("id, full_name, avatar_url, department_id, received_kudos_count, received_hearts_count, created_at")
    .eq("id", id)
    .maybeSingle();

  if (error) throw new Error(`getProfile: ${error.message}`);
  if (!data) return null;
  return toPublicProfile(data);
}

export interface ProfileStats {
  receivedKudosCount: number;
  sentKudosCount: number;
  receivedHeartsCount: number;
  openedBoxCount: number;
  unopenedBoxCount: number;
}

/**
 * 5 chỉ số Profile (nhận/gửi/tim nhận/box mở/box chưa mở) — CHỈ trả khi
 * `targetId === callerId` (Implementation Steps bước 9, TC_WEB_PROFILE_FUN_006).
 * Kiểm TRƯỚC khi query bất kỳ bảng nào — rẻ hơn và là một nhánh dữ liệu duy
 * nhất quyết định self/other. `sentKudosCount` đếm từ `my_sent_kudos` (không
 * phải cột `profiles.sent_kudos_count` bị cấm đọc — xem lib/auth/dto.ts).
 */
export async function getProfileStats(targetId: string, callerId: string): Promise<ProfileStats | null> {
  if (targetId !== callerId) return null;

  const supabase = await createClient();

  const [profileResult, sentCountResult, unopenedBoxCount, openedCountResult] = await Promise.all([
    supabase.from("profiles").select("received_kudos_count, received_hearts_count").eq("id", targetId).maybeSingle(),
    supabase.from("my_sent_kudos").select("*", { count: "exact", head: true }),
    getUnopenedCount(targetId),
    supabase
      .from("secret_box_grants")
      .select("*", { count: "exact", head: true })
      .eq("profile_id", targetId)
      .eq("status", "opened"),
  ]);

  if (profileResult.error) throw new Error(`getProfileStats: ${profileResult.error.message}`);
  if (!profileResult.data) return null;
  if (sentCountResult.error) throw new Error(`getProfileStats: ${sentCountResult.error.message}`);
  if (openedCountResult.error) throw new Error(`getProfileStats: ${openedCountResult.error.message}`);

  return {
    receivedKudosCount: profileResult.data.received_kudos_count,
    sentKudosCount: sentCountResult.count ?? 0,
    receivedHeartsCount: profileResult.data.received_hearts_count,
    openedBoxCount: openedCountResult.count ?? 0,
    unopenedBoxCount,
  };
}

/** Kudos đã NHẬN của một profile (tab "Đã nhận"), qua `public_kudos_feed`. */
export async function listReceivedKudos(
  profileId: string,
  options: ListKudosPageOptions = {},
): Promise<KudosPage> {
  const limit = options.limit ?? DEFAULT_PAGE_SIZE;
  const supabase = await createClient();

  let query = supabase
    .from("public_kudos_feed")
    .select("*")
    .eq("recipient_id", profileId)
    .order("created_at", { ascending: false })
    .order("id", { ascending: false })
    .limit(limit + 1);

  const cursor = decodeCursor(options.cursor);
  if (cursor) {
    query = query.or(`created_at.lt.${cursor.createdAt},and(created_at.eq.${cursor.createdAt},id.lt.${cursor.id})`);
  }

  const { data, error } = await query;
  if (error) throw new Error(`listReceivedKudos: ${error.message}`);

  return buildKudosPage(supabase, data ?? [], limit);
}

/**
 * Kudos đã GỬI của CHÍNH CHỦ (tab "Đã gửi") — chỉ đọc `my_sent_kudos`, KHÔNG
 * nhận tham số userId (Implementation Steps bước 9): view tự lọc theo
 * `auth.uid()`, nhận userId từ tham số sẽ tạo ảo giác kiểm soát được đối tượng
 * trong khi ranh giới thật nằm ở view.
 */
export async function listSentKudos(options: ListKudosPageOptions = {}): Promise<KudosPage> {
  const limit = options.limit ?? DEFAULT_PAGE_SIZE;
  const supabase = await createClient();

  let query = supabase
    .from("my_sent_kudos")
    .select("*")
    .order("created_at", { ascending: false })
    .order("id", { ascending: false })
    .limit(limit + 1);

  const cursor = decodeCursor(options.cursor);
  if (cursor) {
    query = query.or(`created_at.lt.${cursor.createdAt},and(created_at.eq.${cursor.createdAt},id.lt.${cursor.id})`);
  }

  const { data, error } = await query;
  if (error) throw new Error(`listSentKudos: ${error.message}`);

  return buildKudosPage(supabase, data ?? [], limit);
}

export interface SunnerSummary {
  id: string;
  fullName: string;
  avatarUrl: string | null;
}

/**
 * Autocomplete người nhận (Viết Kudo) + tìm Sunner (Spotlight, ≤100 ký tự —
 * Security Considerations). Escape `%`/`_` trước khi `ilike` để tránh truy vấn
 * quét toàn bảng bằng pattern do người dùng nhập tuỳ ý.
 */
export async function searchSunners(query: string): Promise<SunnerSummary[]> {
  const trimmed = query.trim().slice(0, MAX_SEARCH_LENGTH);
  if (trimmed.length === 0) return [];

  const escaped = trimmed.replace(/[%_]/g, (match) => `\\${match}`);
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("profiles")
    .select("id, full_name, avatar_url")
    .ilike("full_name", `%${escaped}%`)
    .order("full_name", { ascending: true })
    .limit(SEARCH_RESULT_LIMIT);

  if (error) throw new Error(`searchSunners: ${error.message}`);
  return (data ?? []).map((row) => ({ id: row.id, fullName: row.full_name, avatarUrl: row.avatar_url }));
}
