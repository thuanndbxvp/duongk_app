# Bối cảnh (CONTEXT): Task 1.1 - Khởi tạo Kiến trúc Monorepo & Core Database

## Mục đích
Đây là bước đầu tiên và quan trọng nhất của dự án YouTube AI SaaS. Chúng ta cần thiết lập bộ khung thư mục (Monorepo) cho backend (FastAPI, Celery, Pydantic packages) và thiết lập toàn bộ schema cơ sở dữ liệu trên Supabase thông qua các file Migration.

## Môi trường
- Backend: Python (FastAPI, Celery)
- Database: PostgreSQL (Supabase) + pgvector + pg_cron
- Yêu cầu đặc biệt: Tuân thủ thứ tự 11 file migration từ G2 (implementation_plan_v1_fixes.md). Mặc dù có bảng users, nhưng chưa áp dụng RLS hay Auth ở giai đoạn này (chỉ tạo bảng/placeholder).
