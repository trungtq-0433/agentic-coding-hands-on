-- Phase-04: Storage bucket cho ảnh đính kèm kudos (0-5 ảnh/kudos).
-- Kiểm MIME thật (file.type + extension) nằm ở lib/actions/kudos-actions.ts —
-- policy ở đây chỉ kiểm soát AI được ghi vào ĐÂU, không kiểm loại file (Storage
-- API không có hook kiểm nội dung file trước upload).

insert into storage.buckets (id, name, public)
values ('kudos-images', 'kudos-images', true)
on conflict (id) do nothing;

-- INSERT: chỉ authenticated, và chỉ vào thư mục mang đúng uuid của chính mình
-- (storage.foldername tách path 'a0.../file.png' thành mảng {'a0...'}).
-- Ngăn user A ghi đè/ghi lẫn vào thư mục của user B.
create policy "kudos_images_insert_own_folder" on storage.objects
  for insert
  to authenticated
  with check (
    bucket_id = 'kudos-images'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

-- SELECT: công khai — ảnh kudos hiển thị trên feed cho mọi người xem, kể cả
-- guest chưa đăng nhập (board Live board không bắt buộc auth để xem).
create policy "kudos_images_select_all" on storage.objects
  for select
  to anon, authenticated
  using (bucket_id = 'kudos-images');
