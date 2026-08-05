# Phân bổ Kỹ năng (SKILL-ROUTING): Task 2.2

## 1. Chiến lược tổng thể
Task này cần load ML models. Tập trung vào:
- Singleton pattern (E2 FIX) để tránh cold-start
- underthesea cho Vietnamese NLP
- textstat cho readability metrics

## 2. Bảng Phân bổ

| Step | Task | Primary Skill | Reference |
|------|------|---------------|-----------|
| 1 | ML Models Singleton | `general-purpose` | - |
| 2 | Emotion Analysis | `general-purpose` | - |
| 3 | Pacing Profile | `general-purpose` | - |
| 4 | Category Classification | `general-purpose` | - |
| 5 | Hook Analysis | `general-purpose` | - |
| 6 | Unit Tests | `tester` | - |

## 3. Files KHÔNG được đụng
- `apps/worker/tasks/` - Celery tasks (Sprint 2.5)
- `apps/api/modules/llm/` - LLM module (Task 2.3)
