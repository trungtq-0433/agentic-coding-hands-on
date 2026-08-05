-- Phase-02: profile_badges + secret_box_grants + RPC admin_grant_secret_box()
-- secret_box_grants cấm hoàn toàn INSERT/UPDATE từ client (revoke ở 0006) —
-- chỉ RPC open_secret_box() (phase-04) và admin_grant_secret_box() (dưới đây) được ghi.

-- profile_badges: bộ sưu tập 6 slot hiển thị trên Profile.
create table profile_badges (
  profile_id uuid not null references profiles (id) on delete cascade,
  badge_id bigint not null references badges (id) on delete cascade,
  awarded_at timestamptz not null default now(),
  primary key (profile_id, badge_id)
);

comment on table profile_badges is 'Bộ sưu tập huy hiệu công khai của mỗi profile. Ghi chỉ qua open_secret_box() (phase-04).';

alter table profile_badges enable row level security;

create policy "profile_badges_select_all" on profile_badges
  for select
  to anon, authenticated
  using (true);

-- secret_box_grants: ledger hộp chưa mở/đã mở. Rule cấp phát để ngỏ
-- (clarifications gap #9) — runbook admin_grant_secret_box() là đường cầu tạm.
create table secret_box_grants (
  id bigint generated always as identity primary key,
  profile_id uuid not null references profiles (id) on delete cascade,
  status text not null default 'unopened' check (status in ('unopened', 'opened')),
  badge_id bigint references badges (id) on delete set null,
  opened_at timestamptz,
  created_at timestamptz not null default now()
);

comment on table secret_box_grants is 'Ledger Secret Box. status=opened kèm badge_id sau khi open_secret_box() (phase-04) chạy.';

alter table secret_box_grants enable row level security;

-- Chỉ chính chủ SELECT hộp của mình (số hộp phải từ server, không lộ của người khác).
create policy "secret_box_grants_select_own" on secret_box_grants
  for select
  to authenticated
  using (auth.uid() = profile_id);

-- admin_grant_secret_box(): đường cấp hộp thủ công giữa sự kiện khi hết hộp
-- (Runbook cuối phase-02.md). security definer + search_path cố định (bắt buộc
-- cho mọi hàm definer — nếu thiếu, kẻ tấn công tạo schema giả chiếm quyền owner).
create function admin_grant_secret_box(p_profile_ids uuid[], p_count int)
returns void
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if not is_admin() then
    raise exception 'FORBIDDEN';
  end if;

  if p_count is null or p_count < 1 then
    raise exception 'p_count phải >= 1';
  end if;

  insert into secret_box_grants (profile_id, status)
  select pid, 'unopened'
  from unnest(p_profile_ids) as pid
  cross join generate_series(1, p_count);
end;
$$;

comment on function admin_grant_secret_box(uuid[], int) is 'RPC admin: cấp thêm secret box chưa mở cho danh sách profile. Chặn non-admin bằng is_admin(). Xem Runbook trong phase-02-schema-migrations-rls.md.';
