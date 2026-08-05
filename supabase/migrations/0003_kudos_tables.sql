-- Phase-02: kudos + kudos_hashtags + kudos_images + hearts
-- Cố tình KHÔNG tạo kudos_mentions (Key Insight #7): không màn nào đọc bảng này,
-- @mention sống trong body dạng text thuần. Dựng lại khi có tính năng thật cần đọc.

-- kudos: heart_count denormalize (Key Insight #4), do trigger ở 0005 duy trì.
create table kudos (
  id bigint generated always as identity primary key,
  sender_id uuid not null references profiles (id) on delete cascade,
  recipient_id uuid not null references profiles (id) on delete cascade,
  body text not null,
  is_anonymous boolean not null default false,
  status text not null default 'active',
  heart_count int not null default 0,
  created_at timestamptz not null default now(),
  constraint kudos_no_self check (sender_id <> recipient_id)
);

comment on table kudos is 'Kudos gửi giữa Sunner. heart_count denormalize, do trigger duy trì. Ghi chỉ qua RPC create_kudos() (phase-04) — xem revoke ở 0006.';

alter table kudos enable row level security;

-- Không có policy select/insert/update/delete cho anon/authenticated ở đây:
-- toàn bộ quyền trực tiếp bị revoke tường minh ở 0006 (đọc qua view, ghi qua RPC).
-- Table vẫn cần RLS bật để Postgres không mặc định mở owner-bypass cho non-owner roles.

-- kudos_hashtags: join table, giới hạn 1-5/kudos ép ở RPC (phase-04) + trigger đếm (0005).
create table kudos_hashtags (
  kudos_id bigint not null references kudos (id) on delete cascade,
  hashtag_id bigint not null references hashtags (id) on delete cascade,
  primary key (kudos_id, hashtag_id)
);

comment on table kudos_hashtags is 'Join kudos-hashtag. Giới hạn 5/kudos ép bởi trg_kudos_hashtag_limit (0005) + RPC (phase-04).';

alter table kudos_hashtags enable row level security;

create policy "kudos_hashtags_select_all" on kudos_hashtags
  for select
  to anon, authenticated
  using (true);

-- kudos_images: tối đa 5 ảnh/kudos, position 0..4.
create table kudos_images (
  id bigint generated always as identity primary key,
  kudos_id bigint not null references kudos (id) on delete cascade,
  url text not null,
  position smallint not null check (position >= 0 and position <= 4),
  created_at timestamptz not null default now(),
  unique (kudos_id, position)
);

comment on table kudos_images is 'Ảnh đính kèm kudos, tối đa 5 (position 0..4).';

alter table kudos_images enable row level security;

create policy "kudos_images_select_all" on kudos_images
  for select
  to anon, authenticated
  using (true);

-- hearts: 1 tim/user/kudos, cờ bonus do RPC toggle_heart() (phase-04) tự tra
-- special_days rồi đặt — client không truyền vào được (revoke insert ở 0006).
create table hearts (
  id bigint generated always as identity primary key,
  kudos_id bigint not null references kudos (id) on delete cascade,
  user_id uuid not null references profiles (id) on delete cascade,
  is_special_day_bonus boolean not null default false,
  created_at timestamptz not null default now(),
  unique (kudos_id, user_id)
);

comment on table hearts is 'Lượt thả tim. is_special_day_bonus chỉ đáng tin vì đã revoke insert trực tiếp (0006) — chỉ RPC toggle_heart() đặt được.';

alter table hearts enable row level security;

create policy "hearts_select_all" on hearts
  for select
  to anon, authenticated
  using (true);
