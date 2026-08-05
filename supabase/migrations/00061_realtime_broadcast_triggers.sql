-- DEVIATION so với phase-02-schema-migrations-rls.md: plan đặt tên file này là
-- "0006b_realtime_broadcast_triggers.sql", nhưng `npx supabase db reset` từ chối
-- áp dụng với lỗi "file name must match pattern <timestamp>_name.sql" — CLI đòi
-- phần trước dấu "_" đầu tiên phải TOÀN SỐ (chữ "b" làm hỏng điều kiện này).
-- Đặt lại số phiên bản dạng số thuần "00061" để CLI chấp nhận. Vì "0006" + số
-- luôn xếp trước "0006_..." trong so sánh chuỗi (chữ số < ký tự "_" trong ASCII),
-- migration này áp dụng TRƯỚC 0006_views_and_rls.sql thay vì sau — không ảnh
-- hưởng vì 2 trigger ở đây chỉ phụ thuộc bảng kudos/hearts (0003), không phụ
-- thuộc view/grant/revoke của 0006. Đã kiểm bằng `npx supabase db reset` (xanh).
--
-- Phase-02: 2 trigger phát Supabase Realtime Broadcast, thay cho Postgres Changes.
-- Lý do đổi cơ chế (Key Insight #10): Postgres Changes uỷ quyền từng subscriber
-- bằng chính RLS/grant của bảng kudos — nhưng bảng kudos đã bị revoke SELECT ở
-- 0006 để chặn rò sender_id ẩn danh. Hai thứ loại trừ nhau; an toàn thắng tiện lợi.
-- Payload CHỈ mang id + loại event — kênh Broadcast KHÔNG đi qua RLS của bảng,
-- nên bất cứ thứ gì nhét vào payload là công khai với người nghe kênh.

-- trg_kudos_broadcast: topic 'kudos-board', payload {kudos_id, event}.
-- security definer + search_path cố định (bắt buộc cho mọi hàm definer).
create function trg_kudos_broadcast_fn()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  perform realtime.send(
    jsonb_build_object(
      'kudos_id', new.id,
      'event', case when tg_op = 'INSERT' then 'insert' else 'update' end
    ),
    'kudos-board',
    'kudos-board',
    false
  );
  return new;
end;
$$;

comment on function trg_kudos_broadcast_fn() is 'Payload chỉ {kudos_id, event} — tuyệt đối không kèm sender_id/body/cột nội dung, vì Broadcast không đi qua RLS.';

create trigger trg_kudos_broadcast
after insert or update on kudos
for each row execute function trg_kudos_broadcast_fn();

-- trg_hearts_broadcast: topic 'user-hearts:<recipient_id>', payload {kudos_id, hearted}.
-- Đọc NEW.kudos_id lúc INSERT, OLD.kudos_id lúc DELETE. Tra recipient_id từ kudos
-- để định tuyến đúng kênh riêng của người nhận (không phát công khai).
create function trg_hearts_broadcast_fn()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_kudos_id bigint;
  v_recipient_id uuid;
  v_hearted boolean;
begin
  if (tg_op = 'INSERT') then
    v_kudos_id := new.kudos_id;
    v_hearted := true;
  else
    v_kudos_id := old.kudos_id;
    v_hearted := false;
  end if;

  select recipient_id into v_recipient_id from kudos where id = v_kudos_id;

  if v_recipient_id is not null then
    perform realtime.send(
      jsonb_build_object('kudos_id', v_kudos_id, 'hearted', v_hearted),
      'user-hearts',
      'user-hearts:' || v_recipient_id::text,
      false
    );
  end if;

  if (tg_op = 'INSERT') then
    return new;
  else
    return old;
  end if;
end;
$$;

comment on function trg_hearts_broadcast_fn() is 'Payload chỉ {kudos_id, hearted} trên kênh riêng của recipient — không kèm user_id người thả tim hay nội dung kudos.';

create trigger trg_hearts_broadcast
after insert or delete on hearts
for each row execute function trg_hearts_broadcast_fn();
