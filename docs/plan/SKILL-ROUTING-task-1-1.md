# Kỹ năng phân luồng (SKILL-ROUTING): Task 1.1

## Kỹ năng được phép (Allowed)
- Dùng `run_command` (powershell/bash) để tạo các thư mục trống.
- Dùng `write_to_file` để tạo các file migration (.sql) và file script (.py).
- Đọc lại các file PRD (`docs/prd_v5_enhanced.md`, v.v.) nếu cần đối chiếu schema.

## Kỹ năng bị cấm (Forbidden)
- KHÔNG cài đặt thư viện (`pip install`) ở bước này. Việc cấu hình môi trường/Dockerfile sẽ nằm ở Task 1.2.
- KHÔNG tự động connect vào DB thật để apply migration. Chúng ta chỉ tạo file SQL thô trong thư mục `supabase/migrations/`.
- KHÔNG sửa đổi các code cũ không liên quan.
