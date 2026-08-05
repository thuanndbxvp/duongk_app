# Sprint 3 Task Group 3: Script Generation - Plan

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  SCRIPT GENERATION PIPELINE                                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Input: assistant_id, topic                                      │
│                    │                                              │
│                    ▼                                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ STEP 1: RAG Context Retrieval                               │ │
│  │ • RAGService.retrieve_context()                             │ │
│  │ • build_script_prompt()                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                    │                                              │
│                    ▼                                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ STEP 2: LLM Generation (GPT-4o)                            │ │
│  │ • System prompt + RAG context                              │ │
│  │ • JSON response format                                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                    │                                              │
│                    ▼                                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ STEP 3: Anti-Slop Validation                                │ │
│  │ • Layer 1: Regex check (fast)                              │ │
│  │ • Layer 2: LLM semantic score (slow)                       │ │
│  │ • Layer 3: Cost-capped retry                               │ │
│  └────────────────────────────────────────────────────────────┘ │
│                    │                                              │
│        ┌──────────┴──────────┐                                   │
│        │                     │                                   │
│        ▼                     ▼                                   │
│    PASS                  FAIL                                   │
│   (score>=6)          (retry up to 3x, $0.10 max)              │
│        │                     │                                   │
│        └──────────┬──────────┘                                   │
│                   ▼                                              │
│  Output: {title, hook, body, cta, score, cost_usd, attempts}    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Anti-Slop Layer Details

### Layer 1: Regex Patterns
```python
VIETNAMESE_SLOP = [
    r'\b(cảm ơn bạn đã xem|like and subscribe|nhấn like|đăng ký kênh)\b',
    r'\b(um+|uh+|à|ừ|ờ)\b',
    r'\b(đừng quên|hãy nhớ rằng|vì vậy|tuy nhiên)\b',
]
ENGLISH_SLOP = [
    r'\b(game-changer|leverage|synergy|scalable|paradigm)\b',
    r'\b(in this video|welcome back|let me know)\b',
]
```

### Layer 2: LLM Scoring
```python
# System prompt for scoring
SCORING_PROMPT = """Bạn là chuyên gia đánh giá kịch bản YouTube.
Đánh giá:
1. Tính tự nhiên (không robotic)
2. Độ độc đáo (không generic)
3. Phù hợp văn hóa Việt Nam
4. Không có văn mẫu AI

Trả lời JSON: {"score": 1-10, "reason": "..."}"""

# Model: gpt-4o-mini (cheap)
# Threshold: score >= 6
```

### Layer 3: Cost Cap
```python
MAX_BUDGET_USD = 0.10
MAX_RETRIES = 3

# Track total cost across retries
# Stop when budget exceeded or max retries reached
# Return best attempt
```

## Files to Create

### 1. SQL Migration
**File:** `supabase/migrations/0016_scripts.sql`

### 2. Anti-Slop Service
**File:** `apps/worker/services/antislop_service.py`

### 3. Celery Task
**File:** `apps/worker/tasks/script_generate.py`

### 4. API Router
**File:** `apps/api/routers/scripts.py`

### 5. Unit Tests
**File:** `apps/worker/services/test_antislop_service.py`
