import { createClient } from "@/lib/supabase/server";

export interface HashtagOption {
  id: number;
  name: string;
  sortOrder: number;
}

export interface DepartmentOption {
  id: number | "unassigned";
  name: string;
  parentId: number | null;
}

/** Mã của mục ảo "Chưa phân loại" — mọi user thật có `department_id = NULL`
 * (Key Insight #9). Đứng cuối danh sách trả về của `listDepartments()`. */
export const UNASSIGNED_DEPARTMENT_ID = "unassigned" as const;
const UNASSIGNED_DEPARTMENT_LABEL = "Chưa phân loại";

/** Master data hashtag (1–5 chọn ở Viết Kudo, filter Live board). */
export async function listHashtags(): Promise<HashtagOption[]> {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("hashtags")
    .select("id, name, sort_order")
    .order("sort_order", { ascending: true });

  if (error) {
    throw new Error(`listHashtags: ${error.message}`);
  }

  return (data ?? []).map((row) => ({
    id: row.id,
    name: row.name,
    sortOrder: row.sort_order,
  }));
}

/**
 * Master data phòng ban + mục ảo "Chưa phân loại" đứng cuối (Implementation
 * Steps bước 8b) — mọi user đăng nhập thật hôm nay đều `department_id = NULL`
 * (Google OAuth không trả phòng ban), không có nhánh này thì họ biến mất khỏi
 * mọi kết quả filter mà không báo lỗi gì.
 */
export async function listDepartments(): Promise<DepartmentOption[]> {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("departments")
    .select("id, name, parent_id")
    .order("name", { ascending: true });

  if (error) {
    throw new Error(`listDepartments: ${error.message}`);
  }

  const options: DepartmentOption[] = (data ?? []).map((row) => ({
    id: row.id,
    name: row.name,
    parentId: row.parent_id,
  }));

  options.push({ id: UNASSIGNED_DEPARTMENT_ID, name: UNASSIGNED_DEPARTMENT_LABEL, parentId: null });
  return options;
}
