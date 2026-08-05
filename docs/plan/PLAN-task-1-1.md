# Kiến trúc & Luồng xử lý (PLAN): Task 1.1

## Kiến trúc Thư mục (Monorepo)
- `/apps/api/`: Chứa code FastAPI (sẽ code ở task sau).
- `/apps/worker/`: Chứa code Celery (sẽ code ở task sau).
- `/packages/shared-types/`: Chứa các Pydantic models dùng chung.
- `/scripts/`: Chứa các tool nội bộ (như `sync_types.py`).
- `/supabase/migrations/`: Chứa các file SQL khởi tạo DB.

## Cấu trúc Database (11 Migrations)
1. `0001_users.sql`: Bảng users cơ bản (id, email, credits).
2. `0002_jobs.sql`: Bảng jobs lưu trạng thái tiến trình AI. Kèm cột `sub_progress` (Fix D1).
3. `0003_credit_transactions.sql`: Bảng lưu lịch sử trừ/cộng credit.
4. `0004_api_usage_logs.sql`: Bảng track cost API (OpenAI, YT).
5. `0005_quota_ledger.sql`: Bảng quản lý Quota YouTube theo ngày.
6. `0006_credit_hold_commit.sql`: RPC `partial_commit_credits` (Atomic - Fix E1).
7. `0007_rls_policies.sql`: Placeholder cho RLS (để trống hoặc comment).
8. `0008_channel_assistants.sql`: Bảng thông tin kênh mẫu.
9. `0009_channel_deep_analysis.sql`: Bảng lưu 14 Outputs (hỗ trợ versioning - Fix E7).
10. `0010_dna_chunks.sql`: Bảng RAG lưu chunks (có `expires_at` TTL 90 ngày - Fix E6).
11. `0011_transcripts_cron.sql`: Bảng transcripts và pg_cron dọn rác 90 ngày.
