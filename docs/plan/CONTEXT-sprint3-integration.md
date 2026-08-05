# Sprint 3 Task Group 5: Integration & API Testing

## 1. Context & Mục đích

### Bối cảnh

Tất cả Task Groups 1-4 đã hoàn thành:
- ✅ Task Group 1: RAG Retrieval
- ✅ Task Group 2: Idea Generation
- ✅ Task Group 3: Script Generation
- ✅ Task Group 4: Scene Breakdown

Task Group 5 là **Integration** - đảm bảo các components hoạt động cùng nhau và viết integration tests.

---

## 2. Integration Flow

```
┌──────────────────────────────────────────────────────────────────┐
│  FULL PIPELINE FLOW                                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  POST /api/scripts/generate                                       │
│         │                                                         │
│         ▼                                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 1. Validate input                                          │  │
│  │ 2. Create job in DB                                        │  │
│  │ 3. Enqueue script_generate task                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│         │                                                         │
│         ▼                                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Celery: script_generate                                    │  │
│  │   - RAG retrieval (Task Group 1)                          │  │
│  │   - LLM generation                                        │  │
│  │   - Anti-slop validation (Task Group 3)                   │  │
│  │   - Save script to DB                                      │  │
│  └────────────────────────────────────────────────────────────┘  │
│         │                                                         │
│         ▼                                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ POST /api/scripts/breakdown-scenes                         │  │
│  │   - Enqueue scene_breakdown task                          │  │
│  └────────────────────────────────────────────────────────────┘  │
│         │                                                         │
│         ▼                                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Celery: scene_breakdown (Task Group 4)                    │  │
│  │   - Segment scenes                                        │  │
│  │   - Translate B-roll                                      │  │
│  │   - Save to DB                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│         │                                                         │
│         ▼                                                         │
│  GET /api/jobs/{id} → Realtime progress                         │
│         │                                                         │
│         ▼                                                         │
│  GET /api/scripts/{id} → Final result                           │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Integration Tests

### Test Cases

| Test ID | Description | Expected |
|---------|-------------|----------|
| IT1 | Full flow: generate script → breakdown scenes | Script + Scenes returned |
| IT2 | RAG retrieval improves script quality | Context included |
| IT3 | Anti-slop rejects low quality scripts | Score < 6 triggers retry |
| IT4 | Realtime progress updates | Status changes visible |
| IT5 | Error handling: invalid assistant_id | 404 returned |
| IT6 | Error handling: insufficient credits | 402 returned |

---

## 4. Files to Create

| File | Purpose |
|------|---------|
| `tests/integration/test_script_flow.py` | Full pipeline integration tests |
| `tests/unit/test_api_scripts.py` | API endpoint unit tests |
| `apps/api/routers/scripts.py` | Add GET endpoint for script retrieval |

---

## 5. Acceptance Summary

| # | Criteria |
|---|----------|
| AC1 | Full pipeline integration test passes |
| AC2 | API endpoints work end-to-end |
| AC3 | Error handling tested |
| AC4 | Realtime progress works |
| AC5 | All tests pass |
