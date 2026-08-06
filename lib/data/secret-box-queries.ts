import { createClient } from "@/lib/supabase/server";
import { computeStarCount } from "@/lib/kudos/star-count";

/** Số hộp CHƯA MỞ của một profile — luôn từ server (Requirements: "Số hộp chưa
 * mở luôn từ server"). RLS `secret_box_grants_select_own` chỉ cho chính chủ
 * đọc hàng của mình, nên gọi với `userId` khác `auth.uid()` sẽ trả 0 (không lộ
 * số hộp của người khác) thay vì lỗi — hành vi này là chủ ý của RLS, không xử
 * lý thêm ở đây. */
export async function getUnopenedCount(userId: string): Promise<number> {
  const supabase = await createClient();
  const { count, error } = await supabase
    .from("secret_box_grants")
    .select("*", { count: "exact", head: true })
    .eq("profile_id", userId)
    .eq("status", "unopened");

  if (error) throw new Error(`getUnopenedCount: ${error.message}`);
  return count ?? 0;
}

export interface PrizeWinner {
  profileId: string;
  fullName: string;
  avatarUrl: string | null;
  badgeCode: string;
  badgeName: string;
  openedAt: string;
}

const LEADERBOARD_LIMIT = 10;

/** Leaderboard "10 Sunner nhận quà mới nhất" — secret_box_grants đã mở, mới nhất trước. */
export async function listRecentPrizeWinners(): Promise<PrizeWinner[]> {
  const supabase = await createClient();
  const { data: grants, error: grantError } = await supabase
    .from("secret_box_grants")
    .select("profile_id, badge_id, opened_at")
    .eq("status", "opened")
    .not("opened_at", "is", null)
    .not("badge_id", "is", null)
    .order("opened_at", { ascending: false })
    .limit(LEADERBOARD_LIMIT);

  if (grantError) throw new Error(`listRecentPrizeWinners: ${grantError.message}`);
  if (!grants || grants.length === 0) return [];

  const profileIds = [...new Set(grants.map((grant) => grant.profile_id))];
  const badgeIds = [...new Set(grants.map((grant) => grant.badge_id).filter((id): id is number => id !== null))];

  const [{ data: profiles, error: profileError }, { data: badges, error: badgeError }] = await Promise.all([
    supabase.from("profiles").select("id, full_name, avatar_url").in("id", profileIds),
    supabase.from("badges").select("id, code, name").in("id", badgeIds),
  ]);
  if (profileError) throw new Error(`listRecentPrizeWinners: ${profileError.message}`);
  if (badgeError) throw new Error(`listRecentPrizeWinners: ${badgeError.message}`);

  const profileById = new Map((profiles ?? []).map((profile) => [profile.id, profile]));
  const badgeById = new Map((badges ?? []).map((badge) => [badge.id, badge]));

  return grants.flatMap((grant): PrizeWinner[] => {
    const profile = profileById.get(grant.profile_id);
    const badge = grant.badge_id !== null ? badgeById.get(grant.badge_id) : undefined;
    if (!profile || !badge || !grant.opened_at) return [];
    return [
      {
        profileId: profile.id,
        fullName: profile.full_name,
        avatarUrl: profile.avatar_url,
        badgeCode: badge.code,
        badgeName: badge.name,
        openedAt: grant.opened_at,
      },
    ];
  });
}

export interface RankUpEntry {
  profileId: string;
  fullName: string;
  avatarUrl: string | null;
  starCount: number;
  receivedKudosCount: number;
}

/**
 * Leaderboard "10 Sunner thăng hạng mới nhất" — schema hiện KHÔNG có bảng ghi
 * lại lịch sử thời điểm một Sunner vượt ngưỡng hoa-thị (10/20/50), nên "mới
 * nhất" theo đúng nghĩa đen không tính được. Đây là XẤP XỈ có chủ đích, đã báo
 * lại trong báo cáo bàn giao: lấy top Sunner đang có hoa-thị (>=1 sao), sắp xếp
 * theo received_kudos_count giảm dần làm proxy — KHÔNG bịa thêm bảng/trigger
 * lịch sử ngoài phạm vi 2 migration 0008/0009 của phase này (đó là quyết định
 * kiến trúc cần PO/planner chốt, không phải việc của một task thực thi).
 */
export async function listRecentRankUps(): Promise<RankUpEntry[]> {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("profiles")
    .select("id, full_name, avatar_url, received_kudos_count")
    .gte("received_kudos_count", 10)
    .order("received_kudos_count", { ascending: false })
    .limit(LEADERBOARD_LIMIT);

  if (error) throw new Error(`listRecentRankUps: ${error.message}`);

  return (data ?? []).map((profile) => ({
    profileId: profile.id,
    fullName: profile.full_name,
    avatarUrl: profile.avatar_url,
    starCount: computeStarCount(profile.received_kudos_count),
    receivedKudosCount: profile.received_kudos_count,
  }));
}
