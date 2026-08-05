# Tiêu chí nghiệm thu (ACCEPTANCE): Task 1.1

Kiểm tra các hạng mục sau trước khi báo cáo hoàn thành:
1. Đã tạo đủ các thư mục `/apps/api`, `/apps/worker`, `/packages/shared-types`, `/scripts`, `/supabase/migrations`.
2. Có file `scripts/sync_types.py` (chứa code placeholder).
3. Thư mục `supabase/migrations/` phải chứa ĐÚNG 11 files, tên bắt đầu từ `0001_` đến `0011_`.
4. Không có lỗi cú pháp SQL (Tier 2 tự kiểm tra chéo bằng mắt).
5. Dimension của vector trong `dna_chunks` phải là `1024` chứ không phải `1536` (theo đúng chuẩn E3).
