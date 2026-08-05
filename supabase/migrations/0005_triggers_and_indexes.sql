-- Phase-02: 3 trigger counter (kudos/hearts denormalize) + 7 index
-- Trigger Broadcast (kudos-board realtime) nằm ở 0006b — file riêng, sau khi
-- view/grant/revoke (0006) đã tồn tại.

-- trg_kudos_counters: profiles.received_kudos_count (+recipient),
-- profiles.sent_kudos_count (+sender). Xử lý cả INSERT lẫn DELETE để counter
-- không lệch khi seed hoặc khi xoá kudos (Risk Assessment).
create function trg_kudos_counters_fn()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if (tg_op = 'INSERT') then
    update profiles set received_kudos_count = received_kudos_count + 1 where id = new.recipient_id;
    update profiles set sent_kudos_count = sent_kudos_count + 1 where id = new.sender_id;
    return new;
  elsif (tg_op = 'DELETE') then
    update profiles set received_kudos_count = received_kudos_count - 1 where id = old.recipient_id;
    update profiles set sent_kudos_count = sent_kudos_count - 1 where id = old.sender_id;
    return old;
  end if;
  return null;
end;
$$;

create trigger trg_kudos_counters
after insert or delete on kudos
for each row execute function trg_kudos_counters_fn();

-- trg_heart_counters: kudos.heart_count +/-(2 nếu bonus, ngược lại 1);
-- profiles.received_hearts_count của recipient tương ứng. Đọc NEW.is_special_day_bonus
-- lúc INSERT và OLD.is_special_day_bonus lúc DELETE — KHÔNG tính lại theo now(),
-- vì unlike có thể xảy ra khác ngày với lúc thả tim (Risk Assessment).
create function trg_heart_counters_fn()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_kudos_id bigint;
  v_recipient_id uuid;
  v_delta int;
begin
  if (tg_op = 'INSERT') then
    v_kudos_id := new.kudos_id;
    v_delta := case when new.is_special_day_bonus then 2 else 1 end;
  elsif (tg_op = 'DELETE') then
    v_kudos_id := old.kudos_id;
    v_delta := -1 * (case when old.is_special_day_bonus then 2 else 1 end);
  else
    return null;
  end if;

  update kudos set heart_count = heart_count + v_delta where id = v_kudos_id
  returning recipient_id into v_recipient_id;

  if v_recipient_id is not null then
    update profiles set received_hearts_count = received_hearts_count + v_delta where id = v_recipient_id;
  end if;

  if (tg_op = 'INSERT') then
    return new;
  else
    return old;
  end if;
end;
$$;

create trigger trg_heart_counters
after insert or delete on hearts
for each row execute function trg_heart_counters_fn();

-- trg_kudos_hashtag_limit: chặn kudos có quá 5 hashtag (RPC create_kudos ở
-- phase-04 cũng ép giới hạn này, trigger là lưới an toàn thứ hai tại DB).
create function trg_kudos_hashtag_limit_fn()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_count int;
begin
  select count(*) into v_count from kudos_hashtags where kudos_id = new.kudos_id;
  if v_count >= 5 then
    raise exception 'Kudos đã có đủ 5 hashtag, không thể thêm nữa';
  end if;
  return new;
end;
$$;

create trigger trg_kudos_hashtag_limit
before insert on kudos_hashtags
for each row execute function trg_kudos_hashtag_limit_fn();

-- Index: keyset cursor (created_at desc, id desc) cho feed nhận/gửi không lặp/nhảy
-- hàng; heart_count desc cho Highlight top-5; các index còn lại phục vụ join/filter.
create index idx_kudos_recipient_feed on kudos (recipient_id, created_at desc, id desc);
create index idx_kudos_sender_feed on kudos (sender_id, created_at desc, id desc);
create index idx_kudos_heart_count on kudos (heart_count desc, created_at desc);
create index idx_hearts_kudos_id on hearts (kudos_id);
create index idx_hearts_user_id on hearts (user_id);
create index idx_kudos_hashtags_hashtag_id on kudos_hashtags (hashtag_id);
create index idx_profiles_department_id on profiles (department_id);
