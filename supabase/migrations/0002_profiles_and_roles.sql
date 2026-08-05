-- Phase-02: profiles + user_roles + is_admin()
-- Role tách khỏi profiles thành bảng riêng (Key Insight #3): scope 2 role (user/admin)
-- không cần Custom Access Token Hook, và gỡ quyền admin có hiệu lực tức thì.

-- profiles: KHÔNG chứa email/auth identifier — tránh lộ qua public_kudos_feed.
-- Ba counter (received_kudos_count, sent_kudos_count, received_hearts_count) do
-- trigger ở 0005 duy trì, seed KHÔNG được ghi cứng.
create table profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  full_name text not null,
  avatar_url text,
  department_id bigint references departments (id) on delete set null,
  received_kudos_count int not null default 0,
  sent_kudos_count int not null default 0,
  received_hearts_count int not null default 0,
  created_at timestamptz not null default now()
);

comment on table profiles is 'Hồ sơ public của user. Không có cột email/role — tránh lộ danh tính qua view public.';

alter table profiles enable row level security;

-- Đọc công khai cho mọi người (board/profile hiển thị public); không có UPDATE
-- cho bất kỳ ai — profile chỉ đọc, Google OAuth trigger (phase-03) là nơi duy nhất ghi.
create policy "profiles_select_all" on profiles
  for select
  to anon, authenticated
  using (true);

-- user_roles: bảng role riêng, tách khỏi profiles (Key Insight #3).
create table user_roles (
  user_id uuid primary key references auth.users (id) on delete cascade,
  role text not null check (role in ('user', 'admin')),
  created_at timestamptz not null default now()
);

comment on table user_roles is 'Role riêng biệt khỏi profiles, để gỡ quyền admin có hiệu lực tức thì.';

alter table user_roles enable row level security;

-- Chỉ chính chủ SELECT được role của mình; không ai ghi trực tiếp
-- (cấp role là thao tác thủ công qua Studio/seed ở MVP, không có RPC).
create policy "user_roles_select_own" on user_roles
  for select
  to authenticated
  using (auth.uid() = user_id);

-- is_admin(): helper security definer cho policy/RPC kiểm tra quyền admin.
-- BẮT BUỘC set search_path — nếu không, kẻ tấn công tạo schema riêng chứa
-- bảng/hàm cùng tên và chiếm được quyền của owner (definer chạy với quyền cao hơn).
create function is_admin()
returns boolean
language sql
security definer
stable
set search_path = public, pg_temp
as $$
  select exists (
    select 1 from user_roles
    where user_id = auth.uid() and role = 'admin'
  );
$$;

comment on function is_admin() is 'Security definer, search_path cố định. Dùng trong policy/RPC để kiểm tra quyền admin.';
