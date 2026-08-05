# Kiến Trúc

## Tương Tác Dịch Vụ

| Từ | Đến | Phương thức | Mô tả |
|----|-----|-------------|-------|
| employee-frontend | employee-backend | GET /api/nhan-vien | Lấy danh sách nhân viên |

## Sự Kiện

| Chủ đề | Vai trò | Sự kiện |
|--------|---------|---------|
| nhanvien.tao | producer | NhanVienTao |
