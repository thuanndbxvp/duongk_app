# Bối cảnh Hệ thống (CONTEXT): Task 2.2 - NLP & Local ML Layer

## 1. Tri thức Tổng hợp
- **Task:** Sprint 2 - Task 2.2: NLP & Local ML Layer (Outputs 5, 6, 7, 10)
- **Mục tiêu:** Xây dựng 4 outputs sử dụng ML models
- **E2 FIX:** Singleton pattern cho ML models
- **Tài liệu:** `docs/plan/PLAN-task-2-2.md`

## 2. Dependencies
```bash
pip install transformers torch underthesea textstat
```

## 3. Files cần tạo
- `apps/worker/ml_models.py` - Singleton loaders
- `apps/api/modules/nlp/emotions.py`
- `apps/api/modules/nlp/pacing.py`
- `apps/api/modules/nlp/category.py`
- `apps/api/modules/nlp/hooks.py`
- `tests/test_nlp/`
