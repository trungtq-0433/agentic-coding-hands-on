-- Phase-03: bootstrap profile qua DB trigger (không phải code app) + RPC đồng bộ
-- lại full_name/avatar_url mỗi lần đăng nhập.

-- handle_new_user(): chèn đúng MỘT hàng profiles + user_roles khi auth.users có
-- user mới, chạy nguyên tử trong transaction insert của Supabase Auth — không
-- phụ thuộc đường vào (Google OAuth hôm nay, provider khác sau này nếu có).
-- security definer vì hàm cần ghi vào profiles/user_roles dù người gọi trigger
-- (auth admin API) không có quyền ghi hai bảng đó; search_path cố định BẮT BUỘC
-- (hàm chạy quyền owner trên auth.users, thiếu là lỗ chiếm quyền — theo đúng
-- quy ước đã áp dụng cho is_admin() và mọi trigger ở 0005).
--
-- full_name không NOT NULL-safe từ raw_user_meta_data (một số provider không trả
-- 'full_name'/'name') nên có fallback tĩnh; KHÔNG fallback về email — profiles là
-- bảng public, không được rò một phần địa chỉ email qua đó. Giá trị thật được
-- ghi đè ngay sau bởi sync_profile_from_google() ở app/auth/callback trong cùng
-- lượt đăng nhập, nên fallback này chỉ là lưới an toàn cho ràng buộc NOT NULL.
create function handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  insert into profiles (id, full_name, avatar_url)
  values (
    new.id,
    coalesce(
      new.raw_user_meta_data ->> 'full_name',
      new.raw_user_meta_data ->> 'name',
      'Người dùng mới'
    ),
    coalesce(
      new.raw_user_meta_data ->> 'avatar_url',
      new.raw_user_meta_data ->> 'picture'
    )
  )
  on conflict (id) do nothing;

  insert into user_roles (user_id, role)
  values (new.id, 'user')
  on conflict (user_id) do nothing;

  return new;
end;
$$;

comment on function handle_new_user() is 'Bootstrap profiles + user_roles(role=user) khi có tài khoản mới trong auth.users. Security definer, search_path cố định. ON CONFLICT DO NOTHING để trigger idempotent nếu chạy lại.';

create trigger on_auth_user_created
after insert on auth.users
for each row execute function handle_new_user();

-- sync_profile_from_google(): đường ghi DUY NHẤT cho phép app đồng bộ lại
-- full_name/avatar_url của chính người đang đăng nhập, mỗi lần qua
-- app/auth/callback (Google có thể đổi tên/ảnh giữa các lần đăng nhập).
--
-- Vì sao cần RPC thay vì `supabase.from('profiles').update(...)` thẳng từ client:
-- 0006_views_and_rls đã revoke toàn bộ quyền ghi trên profiles và KHÔNG có policy
-- update nào cho anon/authenticated ("chỉ đọc, trigger là nơi duy nhất ghi" — comment
-- gốc ở 0002 viết trước khi có yêu cầu đồng bộ lại avatar, nay bổ sung đường ghi
-- narrow này). UPDATE trực tiếp sẽ bị từ chối ở tầng grant trước khi tới RLS.
-- security definer bỏ qua việc thiếu grant, nhưng `auth.uid() = id` NGAY TRONG
-- CÂU UPDATE mới là ranh giới an ninh thật — ai gọi cũng chỉ sửa được đúng hàng
-- của chính mình, không nhận tham số id từ client.
create function sync_profile_from_google(p_full_name text, p_avatar_url text)
returns void
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if auth.uid() is null then
    raise exception 'sync_profile_from_google yêu cầu phiên đăng nhập hợp lệ';
  end if;

  update profiles
  set
    full_name = coalesce(nullif(trim(p_full_name), ''), full_name),
    avatar_url = coalesce(p_avatar_url, avatar_url)
  where id = auth.uid();
end;
$$;

comment on function sync_profile_from_google(text, text) is 'Chính chủ (auth.uid()) tự đồng bộ full_name/avatar_url từ metadata Google mới nhất — gọi từ app/auth/callback sau exchangeCodeForSession. Đường ghi duy nhất vào profiles ngoài trigger bootstrap.';

revoke all on function sync_profile_from_google(text, text) from public;
grant execute on function sync_profile_from_google(text, text) to authenticated;
