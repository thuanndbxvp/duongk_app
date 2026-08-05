# Bối cảnh Hệ thống (CONTEXT): Task 2.1 - Deterministic Layer

## 1. Tri thức Tổng hợp
- **Task:** Sprint 2 - Task 2.1: Deterministic Layer (Outputs 1-4)
- **Mục tiêu:** Xây dựng 4 outputs đầu tiên từ pure Python
- **Tài liệu:** `docs/plan/PLAN-task-2-1.md`

## 2. 14 Outputs tổng quan

| # | Output | Task | Method |
|---|--------|------|--------|
| 1 | Metadata Analysis | 2.1 | Pure Python |
| 2 | Tags Analysis | 2.1 | Pure Python |
| 3 | Performance Reports | 2.1 | Pure Python |
| 4 | Optimal Duration | 2.1 | Pure Python |
| 5 | Emotional Tone | 2.2 | ML (PhoBERT) |
| 6 | Pacing Profile | 2.2 | NLP |
| 7 | Content Category | 2.2 | ML |
| 8 | Hook Analysis | 2.3 | LLM (GPT-4o) |
| 9 | Structural Formula | 2.3 | LLM |
| 10 | Hook Strength | 2.2 | NLP |
| 11 | Mimic Rules | 2.3 | LLM |
| 12 | Hidden Insights | 2.1 | Chi-square + LLM |
| 13 | Content Ideas | Sprint 3 | HDBSCAN |
| 14 | Thumbnail Analysis | 2.3 | Vision |

## 3. Dependencies
```bash
pip install numpy scipy pandas
```

## 4. Files cần tạo
- `apps/api/modules/analysis/formulas.py`
- `apps/api/modules/analysis/outputs.py`
- `apps/api/modules/analysis/insights.py`
- `apps/api/modules/analysis/routes.py`
- `tests/test_analysis/`
