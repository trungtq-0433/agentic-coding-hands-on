-- Phase-02: bảng master data dùng chung (chỉ đọc, không giao dịch nghiệp vụ)
-- departments, hashtags, badges, special_days — mọi Sunner/guest đều SELECT được.

-- departments: cây phòng ban tự tham chiếu, suy ra từ tên lồng nhau
-- (vd "CEVC2 - CySS" là con của "CEVC2"). Xem seed.sql cho 50 dòng thật.
create table departments (
  id bigint generated always as identity primary key,
  code text not null unique,
  name text not null,
  parent_id bigint references departments (id) on delete set null,
  created_at timestamptz not null default now()
);

comment on table departments is 'Phòng ban Sun*, phân cấp qua parent_id. Seed 50 dòng, xem seed.sql.';

alter table departments enable row level security;

create policy "departments_select_all" on departments
  for select
  to anon, authenticated
  using (true);

-- hashtags: dùng cho filter Live board + multi-select trong Viết Kudo (1-5/kudos)
create table hashtags (
  id bigint generated always as identity primary key,
  name text not null unique,
  sort_order smallint not null default 0,
  created_at timestamptz not null default now()
);

comment on table hashtags is 'Master data hashtag. Seed 13 dòng, xem seed.sql.';

alter table hashtags enable row level security;

create policy "hashtags_select_all" on hashtags
  for select
  to anon, authenticated
  using (true);

-- badges: 6 huy hiệu Secret Box, trọng số xác suất cộng lại đúng 100
create table badges (
  id bigint generated always as identity primary key,
  code text not null unique,
  name text not null,
  image_url text,
  probability_weight int not null check (probability_weight > 0),
  created_at timestamptz not null default now()
);

comment on table badges is 'Huy hiệu Secret Box. Tổng probability_weight phải = 100 (Success Criteria phase-02).';

alter table badges enable row level security;

create policy "badges_select_all" on badges
  for select
  to anon, authenticated
  using (true);

-- special_days: ngày đặc biệt cho heart bonus x2. Chưa có UI admin ở MVP -> seed tay.
create table special_days (
  id bigint generated always as identity primary key,
  day date not null unique,
  note text,
  created_at timestamptz not null default now()
);

comment on table special_days is 'Ngày đặc biệt (heart bonus +2). Seed tay, không có UI admin ở MVP (clarifications gap #8).';

alter table special_days enable row level security;

create policy "special_days_select_all" on special_days
  for select
  to anon, authenticated
  using (true);
