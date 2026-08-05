# Sprint 3 Task Group 3: Script Generation & Anti-Slop

## 1. Context & Mục đích

### Bối cảnh

**AppDK** sinh kịch bản YouTube chuẩn phong cách kênh mẫu. Task này implement **Script Generation** với:
1. Prompt Assembly (RAG context + channel persona)
2. Anti-Slop Layer 1 (Regex Vietnamese slop)
3. Anti-Slop Layer 2 (LLM Semantic scoring)
4. Cost-Capped Retry (E5: max $0.10)

### Dependencies

- ✅ Task Group 1: RAG Retrieval (dùng `RAGService.build_script_prompt()`)
- ⏳ Task Group 4: Scene Breakdown (depends on this)

---

## 2. Database Schema

### New Table: generated_scripts

```sql
-- Migration: 0016_scripts.sql
CREATE TABLE generated_scripts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assistant_id UUID NOT NULL REFERENCES channel_assistants(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
  topic TEXT NOT NULL,
  script_text TEXT NOT NULL,
  score FLOAT,
  cost_usd NUMERIC(10,6) NOT NULL DEFAULT 0,
  attempts INT NOT NULL DEFAULT 1,
  scenes JSONB,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_scripts_assistant ON generated_scripts(assistant_id, created_at DESC);
```

---

## 3. Anti-Slop Patterns

### Layer 1: Regex (Fast)

```python
VIETNAMESE_SLOP_PATTERNS = [
    r'\b(cảm ơn bạn đã xem|like and subscribe|nhấn like|đăng ký kênh)\b',
    r'\b(um+|uh+|à|ừ|ờ)\b',  # Filler words
    r'\b(đừng quên|hãy nhớ rằng)\b',
]

ENGLISH_SLOP_PATTERNS = [
    r'\b(game-changer|leverage|synergy|scalable|paradigm)\b',
    r'\b(in this video|welcome back)\b',
]
```

### Layer 2: LLM Semantic (Slow, Expensive)

```python
# GPT-4o-mini scoring 1-10
# Pass: score >= 6
# Cost: ~$0.001 per call
```

### Layer 3: Cost Cap

```python
# Max budget: $0.10
# Max attempts: 3
# Strategy: Best-of-N selection
```

---

## 4. Files to Create

| File | Purpose |
|------|---------|
| `supabase/migrations/0016_scripts.sql` | Table schema |
| `apps/worker/services/antislop_service.py` | Anti-slop validation |
| `apps/worker/tasks/script_generate.py` | Celery task |
| `apps/api/routers/scripts.py` | API endpoint |
| `apps/worker/services/test_antislop_service.py` | Unit tests |

---

## 5. Acceptance Summary

| # | Criteria |
|---|----------|
| AC1 | Regex Layer 1 detect Vietnamese slop |
| AC2 | LLM Layer 2 scoring 1-10 |
| AC3 | Cost cap stops at $0.10 |
| AC4 | Script generation end-to-end |
| AC5 | API endpoint works |
| AC6 | Unit tests pass |
