-- Phase-04: ba RPC nghiệp vụ — đường ghi DUY NHẤT cho kudos/hearts/secret box
-- (0006 đã revoke all quyền ghi trực tiếp trên kudos/kudos_hashtags/kudos_images/
-- hearts). Cả ba: security definer + search_path cố định (BẮT BUỘC — chuỗi 9/9
-- hàm definer trong repo đã tuân thủ, không phá ở đây) + revoke execute from anon
-- (guest không ghi được gì).

-- ============================================================
-- create_kudos: ghi nguyên tử 3 bảng (kudos, kudos_hashtags, kudos_images).
-- Không có p_mention_ids — bảng kudos_mentions đã bỏ khỏi MVP (Key Insight #1b).
--
-- DEVIATION so với chữ ký `uuid[]` trong bảng RPC của phase file: `hashtags.id`
-- và `kudos.id` là `bigint generated always as identity` (0001/0003), không
-- phải uuid — kiểu thật của schema đã dựng ở phase-02 thắng chữ ký giả định
-- trong tài liệu. Dùng `bigint[]`/`returns bigint` để khớp cột thật; xác nhận
-- bằng lỗi psql thật `invalid input syntax for type uuid` trước khi sửa.
-- ============================================================
create function create_kudos(
  p_recipient uuid,
  p_body text,
  p_is_anonymous boolean,
  p_hashtag_ids bigint[],
  p_image_urls text[]
)
returns bigint
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_sender uuid := auth.uid();
  v_kudos_id bigint;
  v_hashtag_count int;
  v_image_count int;
  v_body text := trim(coalesce(p_body, ''));
begin
  if v_sender is null then
    raise exception 'UNAUTHENTICATED';
  end if;

  if not exists (select 1 from profiles where id = p_recipient) then
    raise exception 'RECIPIENT_NOT_FOUND';
  end if;

  if v_sender = p_recipient then
    raise exception 'SELF_KUDOS';
  end if;

  if v_body = '' then
    raise exception 'EMPTY_BODY';
  end if;

  v_hashtag_count := coalesce(array_length(p_hashtag_ids, 1), 0);
  if v_hashtag_count < 1 or v_hashtag_count > 5 then
    raise exception 'HASHTAG_COUNT_INVALID';
  end if;

  -- Hashtag id không tồn tại/trùng lặp: đếm distinct match với bảng thật, phải
  -- khớp đúng số lượng phân biệt trong mảng đầu vào — chặn id rác lọt qua.
  if (
    select count(distinct h.id)
    from unnest(p_hashtag_ids) as h(id)
    join hashtags on hashtags.id = h.id
  ) <> (select count(distinct x) from unnest(p_hashtag_ids) as x) then
    raise exception 'HASHTAG_NOT_FOUND';
  end if;

  v_image_count := coalesce(array_length(p_image_urls, 1), 0);
  if v_image_count > 5 then
    raise exception 'IMAGE_COUNT_INVALID';
  end if;

  insert into kudos (sender_id, recipient_id, body, is_anonymous)
  values (v_sender, p_recipient, v_body, coalesce(p_is_anonymous, false))
  returning id into v_kudos_id;

  insert into kudos_hashtags (kudos_id, hashtag_id)
  select v_kudos_id, distinct_id
  from (select distinct unnest(p_hashtag_ids) as distinct_id) as d;

  if v_image_count > 0 then
    insert into kudos_images (kudos_id, url, position)
    select v_kudos_id, url, ord - 1
    from unnest(p_image_urls) with ordinality as img(url, ord);
  end if;

  return v_kudos_id;
end;
$$;

comment on function create_kudos(uuid, text, boolean, bigint[], text[]) is 'Ghi nguyên tử kudos+hashtags+images. sender=auth.uid(); revoke insert trực tiếp ở 0006 khiến đây là đường duy nhất. Không có p_mention_ids (Key Insight #1b).';

revoke all on function create_kudos(uuid, text, boolean, bigint[], text[]) from public;
revoke execute on function create_kudos(uuid, text, boolean, bigint[], text[]) from anon;
grant execute on function create_kudos(uuid, text, boolean, bigint[], text[]) to authenticated;

-- ============================================================
-- toggle_heart: 1 tim/user/kudos, cấm tự-tim, +2 ngày đặc biệt (tự tra, KHÔNG
-- nhận tham số), chống race bằng `select ... for update` + `on conflict do nothing`.
-- Thu hồi đọc is_special_day_bonus từ CHÍNH HÀNG bị xoá (Key Insight #3).
-- ============================================================
create function toggle_heart(p_kudos_id bigint)
returns table (hearted boolean, heart_count int)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_user uuid := auth.uid();
  v_sender_id uuid;
  v_already_hearted boolean;
  v_is_bonus boolean;
begin
  if v_user is null then
    raise exception 'UNAUTHENTICATED';
  end if;

  -- Khoá hàng kudos trước khi quyết định insert/delete — hai lời gọi song song
  -- (double-click) tuần tự hoá ở đây thay vì cùng đọc "chưa tim" rồi cùng insert.
  select sender_id into v_sender_id
  from kudos
  where id = p_kudos_id and status = 'active'
  for update;

  if not found then
    raise exception 'KUDOS_NOT_FOUND';
  end if;

  if v_sender_id = v_user then
    raise exception 'SELF_HEART';
  end if;

  v_already_hearted := exists (
    select 1 from hearts where kudos_id = p_kudos_id and user_id = v_user
  );

  if v_already_hearted then
    -- Thu hồi: hàng bị xoá đã mang sẵn is_special_day_bonus của chính nó, trigger
    -- trg_heart_counters (0005) đọc NGAY cột đó, KHÔNG tính lại theo now() — unlike
    -- sau nửa đêm vẫn trừ đúng số đã cộng lúc thả (Key Insight #3).
    delete from hearts where kudos_id = p_kudos_id and user_id = v_user;
  else
    -- Bonus do RPC tự tra special_days theo giờ VN — không có tham số nào cho
    -- client truyền cờ này vào (Key Insight #2, Bốn điều không được sai #1).
    v_is_bonus := exists (
      select 1 from special_days
      where day = (now() at time zone 'Asia/Ho_Chi_Minh')::date
    );

    -- on conflict do nothing: lời gọi trùng do double-click thành no-op thay vì
    -- ném lỗi UNIQUE lên UI (Key Insight #3b).
    insert into hearts (kudos_id, user_id, is_special_day_bonus)
    values (p_kudos_id, v_user, v_is_bonus)
    on conflict (kudos_id, user_id) do nothing;
  end if;

  return query
  select
    exists (select 1 from hearts where kudos_id = p_kudos_id and user_id = v_user),
    k.heart_count
  from kudos k
  where k.id = p_kudos_id;
end;
$$;

comment on function toggle_heart(bigint) is 'Toggle tim, chống race bằng for update + on conflict do nothing. Bonus +2 tự tra special_days (không tham số). Thu hồi đọc cờ từ hàng bị xoá.';

revoke all on function toggle_heart(bigint) from public;
revoke execute on function toggle_heart(bigint) from anon;
grant execute on function toggle_heart(bigint) to authenticated;

-- ============================================================
-- open_secret_box: mở đúng 1 hộp chưa mở của auth.uid(), random có trọng số,
-- chống double-open bằng `for update skip locked`.
-- ============================================================
create function open_secret_box()
returns table (badge_id bigint, badge_code text, remaining int)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
#variable_conflict use_column
-- BẮT BUỘC: `returns table(badge_id, ...)` tự khai báo `badge_id`/`badge_code`/
-- `remaining` thành BIẾN plpgsql cùng tên (OUT parameter), trùng với cột thật
-- `profile_badges.badge_id`/`secret_box_grants.badge_id`. Không có dòng này,
-- `insert ... on conflict (profile_id, badge_id)` ở dưới ném lỗi "column
-- reference badge_id is ambiguous" — đã bắt bằng test race SC11 thật, không
-- phải suy đoán. `use_column` ép mọi tên trùng ưu tiên hiểu là CỘT BẢNG bên
-- trong SQL lồng trong hàm; biến plpgsql vẫn dùng được qua tiền tố `v_`.
declare
  v_user uuid := auth.uid();
  v_grant_id bigint;
  v_total_weight int;
  v_pick numeric;
  v_badge_id bigint;
  v_badge_code text;
  v_remaining int;
begin
  if v_user is null then
    raise exception 'UNAUTHENTICATED';
  end if;

  -- skip locked: hai lời gọi song song, một cái khoá được hàng, cái kia bỏ qua
  -- hàng đang khoá thay vì chờ rồi double-open cùng một hộp.
  select id into v_grant_id
  from secret_box_grants
  where profile_id = v_user and status = 'unopened'
  order by id
  limit 1
  for update skip locked;

  if v_grant_id is null then
    raise exception 'NO_UNOPENED_BOX';
  end if;

  select sum(probability_weight) into v_total_weight from badges;

  -- QUAN TRỌNG: rút `random()` ra thành MỘT giá trị vô hướng TRƯỚC, rồi mới so
  -- sánh trong SQL. Bug thật đã bắt bằng test 10.000 lần (Success Criteria):
  -- đặt thẳng `random() * v_total_weight` trong mệnh đề WHERE khiến Postgres
  -- gọi `random()` MỘT LẦN CHO MỖI HÀNG của subquery `b` (6 hàng = 6 giá trị
  -- ngẫu nhiên độc lập, không phải một lần chung) — badge cuối (cumulative
  -- lớn nhất) gần như luôn tự thoả điều kiện của chính nó nên bị chọn cực hiếm
  -- (đo được ~0.4% thay vì 10%), lệch nghiêm trọng khỏi probability_weight.
  v_pick := random() * v_total_weight;

  -- Cộng dồn trọng số rồi chọn hàng đầu tiên có cumulative >= v_pick
  -- (Implementation Steps bước 2) — phân phối đúng theo probability_weight.
  select b.id, b.code
  into v_badge_id, v_badge_code
  from (
    select id, code, sum(probability_weight) over (order by id) as cumulative
    from badges
  ) b
  where b.cumulative >= v_pick
  order by b.cumulative
  limit 1;

  update secret_box_grants
  set status = 'opened', badge_id = v_badge_id, opened_at = now()
  where id = v_grant_id;

  insert into profile_badges (profile_id, badge_id)
  values (v_user, v_badge_id)
  on conflict (profile_id, badge_id) do nothing;

  select count(*) into v_remaining
  from secret_box_grants
  where profile_id = v_user and status = 'unopened';

  return query select v_badge_id, v_badge_code, v_remaining;
end;
$$;

comment on function open_secret_box() is 'Mở 1 hộp chưa mở của auth.uid(), random trọng số theo badges.probability_weight, chống double-open bằng for update skip locked. Hết hộp -> raise NO_UNOPENED_BOX.';

revoke all on function open_secret_box() from public;
revoke execute on function open_secret_box() from anon;
grant execute on function open_secret_box() to authenticated;
