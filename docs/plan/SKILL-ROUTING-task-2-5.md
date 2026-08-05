# Phân bổ Kỹ năng (SKILL-ROUTING): Task 2.5

## 1. Chiến lược tổng thể
Task này tạo ProgressTracker cho Celery worker:
- D1 FIX: Race-safe RPC
- Progress tracking cho 14 outputs
- Integration với Celery tasks

## 2. Bảng Phân bổ

| Step | Task | Primary Skill | Reference |
|------|------|---------------|-----------|
| 1 | Progress RPC | `databases` | - |
| 2 | ProgressTracker | `general-purpose` | - |
| 3 | Celery Task Example | `general-purpose` | - |
| 4 | Unit Tests | `tester` | - |

## 3. Special Notes
- Cần SUPABASE_URL và SUPABASE_SERVICE_ROLE_KEY
- FOR UPDATE lock ngăn race conditions
- Async updates cho Celery
