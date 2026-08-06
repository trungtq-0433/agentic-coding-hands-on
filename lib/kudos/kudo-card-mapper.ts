import type { Database } from "@/lib/supabase/database.types";

type PublicKudosFeedRow = Database["public"]["Views"]["public_kudos_feed"]["Row"];
type MySentKudosRow = Database["public"]["Views"]["my_sent_kudos"]["Row"];
type KudoRowLike = PublicKudosFeedRow | MySentKudosRow;

export interface KudoCardHashtag {
  id: number;
  name: string;
}

export interface KudoCardPerson {
  id: string;
  fullName: string;
  avatarUrl: string | null;
  departmentId: number | null;
}

export interface KudoCard {
  id: number;
  body: string;
  isAnonymous: boolean;
  status: string;
  heartCount: number;
  createdAt: string;
  recipient: Omit<KudoCardPerson, "departmentId">;
  /**
   * `null` khi kudo ẩn danh (view `public_kudos_feed` đã che sender_*) HOẶC khi
   * hàng đến từ `my_sent_kudos` (chính chủ luôn là sender, view đó không lặp
   * lại thông tin của chính họ).
   */
  sender: KudoCardPerson | null;
  hashtags: KudoCardHashtag[];
}

function hasSenderColumns(row: KudoRowLike): row is PublicKudosFeedRow {
  return "sender_id" in row;
}

/**
 * Mapper DUY NHẤT từ hàng view (`public_kudos_feed` hoặc `my_sent_kudos`) →
 * `KudoCard` — bắt buộc để card trên board và trên profile không phân kỳ
 * (TC_WEB_PROFILE_GUI_006, Risk Assessment).
 *
 * `hashtags` không nằm trong 2 view (sống ở bảng join `kudos_hashtags` riêng)
 * nên được truyền vào từ ngoài (`lib/data/kudos-queries.ts` batch-fetch), mapper
 * chỉ ghép lại — giữ mapper thuần, không tự query.
 *
 * Các cột `id`/`recipient_id`/`recipient_full_name` được ép non-null: cả hai
 * view join `inner join profiles p_recipient` trên cột NOT NULL của bảng gốc
 * (xem 0006_views_and_rls.sql), nên null ở đây nghĩa là dữ liệu view hỏng —
 * đáng ném lỗi hơn là âm thầm thay bằng giá trị rỗng.
 */
export function mapKudoRowToCard(row: KudoRowLike, hashtags: KudoCardHashtag[] = []): KudoCard {
  if (row.id === null || row.recipient_id === null) {
    throw new Error("kudo-card-mapper: hàng view thiếu id/recipient_id — dữ liệu view không hợp lệ");
  }

  const sender: KudoCardPerson | null =
    hasSenderColumns(row) && !row.is_anonymous && row.sender_id
      ? {
          id: row.sender_id,
          fullName: row.sender_full_name ?? "",
          avatarUrl: row.sender_avatar_url,
          departmentId: row.sender_department_id,
        }
      : null;

  return {
    id: row.id,
    body: row.body ?? "",
    isAnonymous: row.is_anonymous ?? false,
    status: row.status ?? "active",
    heartCount: row.heart_count ?? 0,
    createdAt: row.created_at ?? "",
    recipient: {
      id: row.recipient_id,
      fullName: row.recipient_full_name ?? "",
      avatarUrl: row.recipient_avatar_url,
    },
    sender,
    hashtags,
  };
}
