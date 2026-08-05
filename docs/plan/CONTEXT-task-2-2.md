# Bối cảnh Hệ thống (CONTEXT): Task 2.2 - NLP & Local ML Layer

## 1. Tri thức Tổng hợp
- **Task:** Sprint 2 - Task 2.2: NLP & Local ML Layer (Outputs 5, 6, 7, 10)
- **Mục tiêu:** Xây dựng 4 outputs sử dụng **GPT-4o API**
- **⚠️ THAY ĐỔI:** KHÔNG còn local ML (torch/transformers)
- **Tài liệu:** `docs/plan/PLAN-task-2-2.md`

## 2. Dependencies
```bash
pip install openai underthesea
```

## 3. ĐÃ LOẠI BỎ
- ❌ `transformers` (>2GB)
- ❌ `torch` (>2GB)
- ❌ PhoBERT model
- ❌ emotion-english-distilroberta-base

## 4. Files cần tạo
- `apps/api/modules/nlp/gpt_analyzer.py` - GPT-4o NLP
- `apps/api/modules/nlp/routes.py` - API Routes
- `tests/test_nlp/` - Test suite
