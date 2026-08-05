-- Sun* Kudos — seed dữ liệu demo
-- `db reset` xoá sạch dữ liệu mỗi lần chạy → file này là NGUỒN SỰ THẬT cho dữ
-- liệu demo (Key Insight #8), không phải "chạy một lần rồi để yên".
-- Chạy bằng quyền owner (postgres) nên không vướng khối `revoke` ở 0006_views_and_rls.sql.
-- Thứ tự: departments → hashtags → badges → special_days → auth.users demo →
-- profiles → user_roles → kudos → kudos_hashtags → kudos_images → hearts →
-- secret_box_grants/profile_badges.

-- ============================================================
-- 1) departments — 50 phòng ban, sinh bởi scripts/count-departments.mjs
--    (chép nguyên khối, không chép tay — xem Implementation Steps bước 8b)
-- ============================================================
insert into departments (code, name) values
  ('CTO', 'CTO'),
  ('SPD', 'SPD'),
  ('FCOV', 'FCOV'),
  ('CEVC1', 'CEVC1'),
  ('CEVC2', 'CEVC2'),
  ('STVC-R-D', 'STVC - R&D'),
  ('CEVC2-CYSS', 'CEVC2 - CySS'),
  ('FCOV-LRM', 'FCOV - LRM'),
  ('CEVC2-SYSTEM', 'CEVC2 - System'),
  ('OPDC-HRF', 'OPDC - HRF'),
  ('CEVC1-DSV-UI-UX-1', 'CEVC1 - DSV - UI/UX 1'),
  ('CEVC1-DSV', 'CEVC1 - DSV'),
  ('CEVEC', 'CEVEC'),
  ('OPDC-HRD-C-C', 'OPDC - HRD - C&C'),
  ('STVC', 'STVC'),
  ('FCOV-F-A', 'FCOV - F&A'),
  ('CEVC1-DSV-UI-UX-2', 'CEVC1 - DSV - UI/UX 2'),
  ('CEVC1-AIE', 'CEVC1 - AIE'),
  ('OPDC-HRF-C-B', 'OPDC - HRF - C&B'),
  ('FCOV-GA', 'FCOV - GA'),
  ('FCOV-ISO', 'FCOV - ISO'),
  ('STVC-EE', 'STVC - EE'),
  ('GEU-HUST', 'GEU - HUST'),
  ('CEVEC-SAPD', 'CEVEC - SAPD'),
  ('OPDC-HRF-OD', 'OPDC - HRF - OD'),
  ('CEVEC-GSD', 'CEVEC - GSD'),
  ('GEU-TM', 'GEU - TM'),
  ('STVC-R-D-DTR', 'STVC - R&D - DTR'),
  ('STVC-R-D-DPS', 'STVC - R&D - DPS'),
  ('CEVC3', 'CEVC3'),
  ('STVC-R-D-AIR', 'STVC - R&D - AIR'),
  ('CEVC4', 'CEVC4'),
  ('PAO', 'PAO'),
  ('GEU', 'GEU'),
  ('GEU-DUT', 'GEU - DUT'),
  ('OPDC-HRD-L-D', 'OPDC - HRD - L&D'),
  ('OPDC-HRD-TI', 'OPDC - HRD - TI'),
  ('OPDC-HRF-TA', 'OPDC - HRF - TA'),
  ('GEU-UET', 'GEU - UET'),
  ('STVC-R-D-SDX', 'STVC - R&D - SDX'),
  ('OPDC-HRD-HRBP', 'OPDC - HRD - HRBP'),
  ('PAO-PEC', 'PAO - PEC'),
  ('IAV', 'IAV'),
  ('STVC-INFRA', 'STVC - Infra'),
  ('CPV-CGP', 'CPV - CGP'),
  ('GEU-UIT', 'GEU - UIT'),
  ('OPDC-HRD', 'OPDC - HRD'),
  ('BDV', 'BDV'),
  ('CPV', 'CPV'),
  -- FIXME(nguồn): trùng tên cha, chờ xác nhận từ người soạn spec — mục thứ 50
  -- trong CSV gốc là "PAO - PAO", một phòng ban con trùng tên với cha "PAO"
  -- (mục thứ 33). Gần như chắc chắn lỗi nhập liệu bên soạn spec, nhưng vẫn seed
  -- đủ 50 theo đúng nguồn — không tự ý gộp hay bỏ (clarifications.md "Còn treo").
  ('PAO-PAO', 'PAO - PAO');

-- Nối cha-con sau khi đã chèn hết, khỏi phải lo thứ tự
update departments c set parent_id = p.id
from departments p
where c.name like '% - %'
  and p.name = left(c.name, length(c.name) - position(' - ' in reverse(c.name)) - 2);

-- ============================================================
-- 2) hashtags — 13 hashtag, từ spec-dropdown-hashtag-filter-JWpsISMAaM.csv item A
-- ============================================================
insert into hashtags (name, sort_order) values
  ('Toàn diện', 1),
  ('Giỏi chuyên môn', 2),
  ('Hiệu suất cao', 3),
  ('Truyền cảm hứng', 4),
  ('Cống hiến', 5),
  ('Aim High', 6),
  ('Be Agile', 7),
  ('Wasshoi', 8),
  ('Hướng mục tiêu', 9),
  ('Hướng khách hàng', 10),
  ('Chuẩn quy trình', 11),
  ('Giải pháp sáng tạo', 12),
  ('Quản lý xuất sắc', 13);

-- ============================================================
-- 3) badges — 6 huy hiệu Secret Box, từ spec-open-secret-box-J3-4YFIpMM.csv item C
--    Trọng số 30/25/10/5/20/10, tổng đúng 100 (Success Criteria phase-02).
-- ============================================================
insert into badges (code, name, probability_weight) values
  ('stay_gold', 'Stay Gold', 30),
  ('flow_to_horizon', 'Flow to Horizon', 25),
  ('beyond_the_boundary', 'Beyond the Boundary', 10),
  ('root_further', 'Root Further', 5),
  ('touch_of_light', 'Touch of Light', 20),
  ('revival', 'Revival', 10);

-- ============================================================
-- 4) special_days — ngày đặc biệt cho heart bonus x2. Seed tay, chưa có UI admin.
-- ============================================================
insert into special_days (day, note) values
  ('2026-08-10', 'Ngày khởi động sự kiện Sun* Kudos'),
  ('2026-08-15', 'Kỷ niệm thành lập Sun*'),
  ('2026-08-20', 'Ngày đôi tim x2 giữa sự kiện'),
  ('2026-08-25', 'Ngày tổng kết trao giải');

-- ============================================================
-- 5) auth.users demo (~8 user) — encrypted_password giả, chỉ dùng local dev.
--    profiles.id là FK tới auth.users nên phải có hàng auth.users trước.
-- ============================================================
insert into auth.users (
  instance_id, id, aud, role, email, encrypted_password,
  email_confirmed_at, created_at, updated_at,
  raw_app_meta_data, raw_user_meta_data, is_super_admin,
  confirmation_token, recovery_token, email_change_token_new, email_change,
  is_sso_user, is_anonymous
) values
  ('00000000-0000-0000-0000-000000000000', 'a0000000-0000-0000-0000-000000000001', 'authenticated', 'authenticated', 'an.nguyen@sunkudos.demo', crypt('demo-not-a-real-password', gen_salt('bf')), now(), now(), now(), '{"provider":"google","providers":["google"]}', '{"full_name":"Nguyễn Văn An","avatar_url":null}', false, '', '', '', '', false, false),
  ('00000000-0000-0000-0000-000000000000', 'a0000000-0000-0000-0000-000000000002', 'authenticated', 'authenticated', 'binh.tran@sunkudos.demo', crypt('demo-not-a-real-password', gen_salt('bf')), now(), now(), now(), '{"provider":"google","providers":["google"]}', '{"full_name":"Trần Thị Bình","avatar_url":null}', false, '', '', '', '', false, false),
  ('00000000-0000-0000-0000-000000000000', 'a0000000-0000-0000-0000-000000000003', 'authenticated', 'authenticated', 'cuong.le@sunkudos.demo', crypt('demo-not-a-real-password', gen_salt('bf')), now(), now(), now(), '{"provider":"google","providers":["google"]}', '{"full_name":"Lê Văn Cường","avatar_url":null}', false, '', '', '', '', false, false),
  ('00000000-0000-0000-0000-000000000000', 'a0000000-0000-0000-0000-000000000004', 'authenticated', 'authenticated', 'dung.pham@sunkudos.demo', crypt('demo-not-a-real-password', gen_salt('bf')), now(), now(), now(), '{"provider":"google","providers":["google"]}', '{"full_name":"Phạm Thị Dung","avatar_url":null}', false, '', '', '', '', false, false),
  ('00000000-0000-0000-0000-000000000000', 'a0000000-0000-0000-0000-000000000005', 'authenticated', 'authenticated', 'em.hoang@sunkudos.demo', crypt('demo-not-a-real-password', gen_salt('bf')), now(), now(), now(), '{"provider":"google","providers":["google"]}', '{"full_name":"Hoàng Văn Em","avatar_url":null}', false, '', '', '', '', false, false),
  ('00000000-0000-0000-0000-000000000000', 'a0000000-0000-0000-0000-000000000006', 'authenticated', 'authenticated', 'phuong.do@sunkudos.demo', crypt('demo-not-a-real-password', gen_salt('bf')), now(), now(), now(), '{"provider":"google","providers":["google"]}', '{"full_name":"Đỗ Thị Phương","avatar_url":null}', false, '', '', '', '', false, false),
  ('00000000-0000-0000-0000-000000000000', 'a0000000-0000-0000-0000-000000000007', 'authenticated', 'authenticated', 'giang.vu@sunkudos.demo', crypt('demo-not-a-real-password', gen_salt('bf')), now(), now(), now(), '{"provider":"google","providers":["google"]}', '{"full_name":"Vũ Văn Giang","avatar_url":null}', false, '', '', '', '', false, false),
  ('00000000-0000-0000-0000-000000000000', 'a0000000-0000-0000-0000-000000000008', 'authenticated', 'authenticated', 'hoa.bui@sunkudos.demo', crypt('demo-not-a-real-password', gen_salt('bf')), now(), now(), now(), '{"provider":"google","providers":["google"]}', '{"full_name":"Bùi Thị Hoa","avatar_url":null}', false, '', '', '', '', false, false);

-- ============================================================
-- 6) profiles — không có trigger handle_new_user() ở phase này (thuộc phase-03),
--    nên phải tự tay insert profiles cho từng auth.users demo ở trên.
--    received_kudos_count/sent_kudos_count/received_hearts_count để mặc định 0,
--    trigger ở 0005 tự tính khi seed kudos/hearts phía dưới (không ghi cứng).
-- ============================================================
insert into profiles (id, full_name, avatar_url, department_id) values
  ('a0000000-0000-0000-0000-000000000001', 'Nguyễn Văn An', 'https://api.dicebear.com/7.x/initials/svg?seed=An', (select id from departments where code = 'CTO')),
  ('a0000000-0000-0000-0000-000000000002', 'Trần Thị Bình', 'https://api.dicebear.com/7.x/initials/svg?seed=Binh', (select id from departments where code = 'CEVC1-DSV')),
  ('a0000000-0000-0000-0000-000000000003', 'Lê Văn Cường', 'https://api.dicebear.com/7.x/initials/svg?seed=Cuong', (select id from departments where code = 'STVC-R-D')),
  ('a0000000-0000-0000-0000-000000000004', 'Phạm Thị Dung', 'https://api.dicebear.com/7.x/initials/svg?seed=Dung', (select id from departments where code = 'FCOV')),
  ('a0000000-0000-0000-0000-000000000005', 'Hoàng Văn Em', 'https://api.dicebear.com/7.x/initials/svg?seed=Em', (select id from departments where code = 'CEVC2-CYSS')),
  ('a0000000-0000-0000-0000-000000000006', 'Đỗ Thị Phương', 'https://api.dicebear.com/7.x/initials/svg?seed=Phuong', (select id from departments where code = 'OPDC-HRD')),
  ('a0000000-0000-0000-0000-000000000007', 'Vũ Văn Giang', 'https://api.dicebear.com/7.x/initials/svg?seed=Giang', (select id from departments where code = 'GEU')),
  ('a0000000-0000-0000-0000-000000000008', 'Bùi Thị Hoa', 'https://api.dicebear.com/7.x/initials/svg?seed=Hoa', (select id from departments where code = 'PAO'));

-- ============================================================
-- 7) user_roles — 1 admin (An), 7 user thường.
-- ============================================================
insert into user_roles (user_id, role) values
  ('a0000000-0000-0000-0000-000000000001', 'admin'),
  ('a0000000-0000-0000-0000-000000000002', 'user'),
  ('a0000000-0000-0000-0000-000000000003', 'user'),
  ('a0000000-0000-0000-0000-000000000004', 'user'),
  ('a0000000-0000-0000-0000-000000000005', 'user'),
  ('a0000000-0000-0000-0000-000000000006', 'user'),
  ('a0000000-0000-0000-0000-000000000007', 'user'),
  ('a0000000-0000-0000-0000-000000000008', 'user');

-- ============================================================
-- 8) kudos — 30 kudos demo, xoay vòng 8 profile (offset +3 nên sender luôn
--    khác recipient, thoả CHECK kudos_no_self). Mỗi kudos thứ 6 là ẩn danh.
--    heart_count để mặc định 0 — trigger trg_heart_counters (0005) tự cộng khi
--    seed hearts ở bước 10, KHÔNG ghi cứng (Requirements phi chức năng).
-- ============================================================
with params as (
  select
    'a0000000-0000-0000-0000-000000000001'::uuid as p1,
    'a0000000-0000-0000-0000-000000000002'::uuid as p2,
    'a0000000-0000-0000-0000-000000000003'::uuid as p3,
    'a0000000-0000-0000-0000-000000000004'::uuid as p4,
    'a0000000-0000-0000-0000-000000000005'::uuid as p5,
    'a0000000-0000-0000-0000-000000000006'::uuid as p6,
    'a0000000-0000-0000-0000-000000000007'::uuid as p7,
    'a0000000-0000-0000-0000-000000000008'::uuid as p8
)
insert into kudos (sender_id, recipient_id, body, is_anonymous, created_at)
select
  (case (n - 1) % 8
    when 0 then p1 when 1 then p2 when 2 then p3 when 3 then p4
    when 4 then p5 when 5 then p6 when 6 then p7 else p8 end),
  (case (n - 1 + 3) % 8
    when 0 then p1 when 1 then p2 when 2 then p3 when 3 then p4
    when 4 then p5 when 5 then p6 when 6 then p7 else p8 end),
  'Cảm ơn bạn rất nhiều vì đã hỗ trợ và đồng hành cùng team trong dự án gần đây! (Kudo demo #' || n || ')',
  (n % 6 = 0),
  now() - make_interval(hours => (30 - n)::int)
from generate_series(1, 30) as n, params;

-- ============================================================
-- 9) kudos_hashtags — mỗi kudos ít nhất 1 hashtag (round-robin qua 13 hashtag),
--    kudos chẵn có thêm hashtag thứ 2, kudos chia hết cho 3 có thêm hashtag thứ 3.
--    Offset (+5, +9) đảm bảo không trùng hashtag_id cho cùng 1 kudos (mod 13 ≠ 0).
-- ============================================================
with k as (
  select id, row_number() over (order by id) as rn from kudos
)
insert into kudos_hashtags (kudos_id, hashtag_id)
select k.id, h.id
from k
join hashtags h on h.id = ((k.rn - 1) % 13) + 1;

with k as (
  select id, row_number() over (order by id) as rn from kudos
)
insert into kudos_hashtags (kudos_id, hashtag_id)
select k.id, h.id
from k
join hashtags h on h.id = ((k.rn - 1 + 5) % 13) + 1
where k.rn % 2 = 0;

with k as (
  select id, row_number() over (order by id) as rn from kudos
)
insert into kudos_hashtags (kudos_id, hashtag_id)
select k.id, h.id
from k
join hashtags h on h.id = ((k.rn - 1 + 9) % 13) + 1
where k.rn % 3 = 0;

-- ============================================================
-- 10) kudos_images — vài kudos có 1 ảnh minh hoạ (kudos thứ 7, 14, 21, 28).
-- ============================================================
with k as (
  select id, row_number() over (order by id) as rn from kudos
)
insert into kudos_images (kudos_id, url, position)
select k.id, 'https://picsum.photos/seed/kudos-' || k.rn || '/600/400', 0
from k
where k.rn % 7 = 0;

-- ============================================================
-- 11) hearts — tập hợp lượt tim xoay vòng (kudos x profile, loại trừ chính
--    sender), cộng thêm vài lượt tim "bonus" rơi vào special_days để minh hoạ
--    is_special_day_bonus. Trigger trg_heart_counters (0005) tự cộng heart_count
--    và profiles.received_hearts_count — không ghi cứng ở đây.
-- ============================================================
with k as (
  select id, sender_id, row_number() over (order by id) as rn from kudos
),
pr as (
  select id, row_number() over (order by id) as rn from profiles
)
insert into hearts (kudos_id, user_id, is_special_day_bonus, created_at)
select k.id, pr.id, false, now() - make_interval(hours => (30 - k.rn)::int)
from k
join pr on pr.id <> k.sender_id
where (k.rn + pr.rn) % 5 = 0;

-- Vài lượt tim bonus (x2) rơi đúng vào special_days, do người không phải sender
-- thả — minh hoạ trg_heart_counters cộng +2 thay vì +1. ON CONFLICT DO NOTHING
-- đề phòng trùng với tập xoay vòng ở trên (UNIQUE(kudos_id, user_id)).
insert into hearts (kudos_id, user_id, is_special_day_bonus, created_at)
select k.id, u.user_id, true, sd.day + interval '10 hours'
from (values
  (1, 'a0000000-0000-0000-0000-000000000002'::uuid),
  (2, 'a0000000-0000-0000-0000-000000000003'::uuid),
  (3, 'a0000000-0000-0000-0000-000000000004'::uuid)
) as u(kudos_rn, user_id)
join (select id, row_number() over (order by id) as rn from kudos) k on k.rn = u.kudos_rn
cross join lateral (select day from special_days order by day limit 1) sd
where u.user_id <> (select sender_id from kudos where id = k.id)
on conflict (kudos_id, user_id) do nothing;

-- ============================================================
-- 12) secret_box_grants + profile_badges — vài hộp chưa mở (demo, rule cấp phát
--    thật còn treo — clarifications gap #9), vài hộp đã mở kèm huy hiệu tương ứng
--    trong bộ sưu tập profile_badges.
-- ============================================================
insert into secret_box_grants (profile_id, status) values
  ('a0000000-0000-0000-0000-000000000001', 'unopened'),
  ('a0000000-0000-0000-0000-000000000001', 'unopened'),
  ('a0000000-0000-0000-0000-000000000002', 'unopened'),
  ('a0000000-0000-0000-0000-000000000002', 'unopened'),
  ('a0000000-0000-0000-0000-000000000003', 'unopened'),
  ('a0000000-0000-0000-0000-000000000004', 'unopened'),
  ('a0000000-0000-0000-0000-000000000007', 'unopened'),
  ('a0000000-0000-0000-0000-000000000008', 'unopened');

insert into secret_box_grants (profile_id, status, badge_id, opened_at) values
  ('a0000000-0000-0000-0000-000000000005', 'opened', (select id from badges where code = 'stay_gold'), now() - interval '2 days'),
  ('a0000000-0000-0000-0000-000000000006', 'opened', (select id from badges where code = 'revival'), now() - interval '1 day');

insert into profile_badges (profile_id, badge_id, awarded_at) values
  ('a0000000-0000-0000-0000-000000000005', (select id from badges where code = 'stay_gold'), now() - interval '2 days'),
  ('a0000000-0000-0000-0000-000000000006', (select id from badges where code = 'revival'), now() - interval '1 day');
