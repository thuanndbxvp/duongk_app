# Bối cảnh Hệ thống (CONTEXT): Task 2.3 - LLM & Vision Layer

## 1. Tri thức Tổng hợp
- **Task:** Sprint 2 - Task 2.3: LLM & Vision Layer (Outputs 8, 9, 11, 14)
- **Mục tiêu:** Xây dựng 4 outputs sử dụng GPT-4o và Vision
- **E7 FIX:** Versioning cho channel_deep_analysis
- **Tài liệu:** `docs/plan/PLAN-task-2-3.md`

## 2. Dependencies
```bash
pip install openai
```

## 3. Outputs
- Output 8: Hook Analysis (LLM)
- Output 9: Structural Formula (LLM)
- Output 11: Mimic Rules (LLM)
- Output 14: Thumbnail Analysis (Vision)

## 4. Files cần tạo
- `apps/api/modules/llm/analyzer.py`
- `apps/api/modules/llm/prompts.py`
- `apps/api/modules/vision/thumbnail_analyzer.py`
- `supabase/migrations/0012_analysis_versions.sql`
