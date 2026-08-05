-- Phase-02: 2 view bảo mật + toàn bộ grant/revoke tường minh + policy còn lại.
-- Nguyên tắc: đọc thì qua view, ghi thì qua RPC (phase-04). Không bảng nghiệp vụ
-- nào nhận ghi trực tiếp từ client. Xem Security Considerations trong
-- phase-02-schema-migrations-rls.md — đây là ranh giới an ninh của cả phase.

-- public_kudos_feed: che sender_* = NULL khi is_anonymous. security_invoker = false
-- viết TƯỜNG MINH (không dựa mặc định) — nếu vô tình để true, view sẽ áp RLS của
-- caller lên bảng kudos vốn đã bị revoke SELECT, khiến feed rỗng với mọi client.
create view public_kudos_feed
with (security_invoker = false)
as
select
  k.id,
  case when k.is_anonymous then null else k.sender_id end as sender_id,
  case when k.is_anonymous then null else p_sender.full_name end as sender_full_name,
  case when k.is_anonymous then null else p_sender.avatar_url end as sender_avatar_url,
  case when k.is_anonymous then null else p_sender.department_id end as sender_department_id,
  k.recipient_id,
  p_recipient.full_name as recipient_full_name,
  p_recipient.avatar_url as recipient_avatar_url,
  k.body,
  k.is_anonymous,
  k.status,
  k.heart_count,
  k.created_at
from kudos k
join profiles p_recipient on p_recipient.id = k.recipient_id
left join profiles p_sender on p_sender.id = k.sender_id
where k.status = 'active';

comment on view public_kudos_feed is 'Feed public. security_invoker=false tường minh: view chạy quyền owner (bỏ qua revoke select trên kudos), tự che sender_* khi is_anonymous. Ranh giới ẩn danh nằm ở ĐÂY, không phải ở UI.';

grant select on public_kudos_feed to anon, authenticated;

-- my_sent_kudos: definer view, where sender_id = auth.uid() CHÍNH LÀ ranh giới an
-- ninh (không phải điều kiện if phía React). KHÔNG che ẩn danh — tự xem thì thấy.
-- Chỉ grant authenticated, KHÔNG grant anon (anon không có auth.uid()).
create view my_sent_kudos
with (security_invoker = false)
as
select
  k.id,
  k.recipient_id,
  p_recipient.full_name as recipient_full_name,
  p_recipient.avatar_url as recipient_avatar_url,
  k.body,
  k.is_anonymous,
  k.status,
  k.heart_count,
  k.created_at
from kudos k
join profiles p_recipient on p_recipient.id = k.recipient_id
where k.sender_id = auth.uid();

comment on view my_sent_kudos is 'Sent-list của chính chủ. security_invoker=false tường minh + where sender_id = auth.uid() là ranh giới an ninh thật. Không grant anon.';

grant select on my_sent_kudos to authenticated;

-- === Khối revoke tường minh (Key Insight #9) ===
-- Vì sao revoke chứ không chỉ dựa policy: policy "with check (auth.uid() = sender_id)"
-- chỉ xác thực AI ghi, không xác thực GHI CÁI GÌ. Nó không chặn được kudo 0 hashtag,
-- tự thả tim vào kudos của chính mình, hay tự set is_special_day_bonus = true.
-- Mọi luật nghiệp vụ đó sống trong RPC (phase-04) — đường ghi trực tiếp phải đóng.
-- `revoke all` chứ không phải `revoke insert, update, delete`: liệt kê từng quyền
-- sẽ bỏ sót TRUNCATE. TRUNCATE xoá sạch bảng và KHÔNG đi qua RLS — một tài khoản
-- authenticated bất kỳ (spec cho phép MỌI tài khoản Google đăng nhập) sẽ xoá được
-- toàn bộ tim/hashtag/ảnh. Đã kiểm chứng lỗ hổng này bằng psql trước khi sửa.
-- Cách an toàn: thu hết rồi cấp lại đúng thứ cần.
revoke all on kudos from anon, authenticated;
revoke all on kudos_hashtags, kudos_images, hearts from anon, authenticated;

-- Các bảng vẫn cần SELECT trực tiếp (không đi qua view) vì chúng không mang
-- thông tin nhạy cảm cần che — chỉ kudos (qua sender_id) mới cần view để ẩn danh.
grant select on kudos_hashtags, kudos_images, hearts to anon, authenticated;

-- === Grant SELECT tường minh cho các bảng còn lại (phát hiện khi kiểm bằng psql) ===
-- Giả định ban đầu SAI: nghĩ rằng Supabase mặc định cấp sẵn SELECT/INSERT/UPDATE/
-- DELETE cho anon/authenticated trên mọi bảng mới, RLS policy là đủ để mở khoá đọc.
-- Thực tế trên instance local này: `alter default privileges` của role `postgres`
-- (role chạy migration) cho schema public chỉ cấp sẵn REFERENCES/TRIGGER/TRUNCATE —
-- KHÔNG có SELECT. Có RLS policy `using (true)` mà không có GRANT SELECT thì
-- Postgres từ chối truy vấn ngay ở tầng privilege, chưa tới lượt RLS lọc dòng
-- (đã kiểm chứng: `permission denied for table secret_box_grants` dù đã có policy
-- select_own). Vì vậy phải GRANT tường minh cho mọi bảng đọc-công-khai, không chỉ
-- 4 bảng có ghi trực tiếp bị revoke ở trên.
-- Thu sạch trước khi cấp lại, vì cùng lý do TRUNCATE ở trên: default privilege
-- cấp sẵn REFERENCES/TRIGGER/TRUNCATE cho MỌI bảng, không riêng 4 bảng nghiệp vụ.
-- Không thu thì bất kỳ tài khoản nào cũng truncate được master data.
revoke all on departments, hashtags, badges, special_days from anon, authenticated;
revoke all on profiles, profile_badges, user_roles, secret_box_grants from anon, authenticated;

grant select on departments, hashtags, badges, special_days to anon, authenticated;
-- `profiles` cấp quyền THEO CỘT, cố tình bỏ `sent_kudos_count`.
--
-- Vì sao: counter đó cộng cả kudos ẩn danh. Để nó công khai là mở đường suy luận
-- trừ, phá sạch cơ chế ẩn danh mà toàn bộ phase này dựng lên:
--     số_ẩn_danh(X) = profiles.sent_kudos_count(X)
--                     − count(public_kudos_feed where sender_id = X)
-- Đã đo trên seed: kết quả khớp CHÍNH XÁC số kudo ẩn danh thật của từng người.
-- Nguy hiểm hơn nữa: theo dõi counter này theo thời gian rồi đối chiếu với thời
-- điểm kudo ẩn danh xuất hiện trên feed thì truy được TỪNG kudo về đúng người gửi.
--
-- RLS chặn theo hàng, không chặn theo cột — nên hàng rào ở đây phải là GRANT cấp cột.
-- Chính chủ muốn xem số đã gửi thì đọc qua `my_sent_kudos` (đã lọc theo auth.uid()).
grant select (
  id, full_name, avatar_url, department_id,
  received_kudos_count, received_hearts_count, created_at
) on profiles to anon, authenticated;
grant select on profile_badges to anon, authenticated;
-- user_roles và secret_box_grants: chỉ "chính chủ" đọc được (policy select_own),
-- và chỉ authenticated mới có auth.uid() — KHÔNG grant anon (khớp bảng ma trận RLS).
grant select on user_roles to authenticated;
grant select on secret_box_grants to authenticated;

-- Hai VIEW vẫn hiện REFERENCES/TRIGGER/TRUNCATE cho anon/authenticated trong
-- information_schema. Cố ý không revoke: Postgres từ chối TRUNCATE trên view
-- ("... is not a table"), nên đó là quyền không bao giờ thực thi được, không
-- phải lỗ hổng. Đã kiểm chứng. Thêm revoke ở đây chỉ là nghi lễ.
-- Điều THỰC SỰ quan trọng đã đúng: anon KHÔNG có SELECT trên my_sent_kudos.
