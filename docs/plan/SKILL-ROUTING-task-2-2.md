# Phân bổ Kỹ năng (SKILL-ROUTING): Task 2.2

## 1. Chiến lược tổng thể
Task này dùng GPT-4o API thay vì local ML. Không cần:
- ML models
- torch/transformers
- ML Worker trên Railway

## 2. Bảng Phân bổ

| Step | Task | Primary Skill | Reference |
|------|------|---------------|-----------|
| 1 | GPT NLP Analyzer | `general-purpose` | - |
| 2 | API Routes | `general-purpose` | - |
| 3 | Unit Tests | `tester` | - |

## 3. Files KHÔNG được đụng
- `apps/worker/ml_models.py` - ĐÃ LOẠI BỎ
- ML Worker Railway - ĐÃ XÓA
- transformers/torch - KHÔNG cài đặt
