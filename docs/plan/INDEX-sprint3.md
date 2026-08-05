# Sprint 3 - Task Group Index

## Overview

Sprint 3: AI Script Generation gồm **5 Task Groups**, mỗi group có **5 files** theo chuẩn TIER1_PROMPT.md.

---

## Task Groups

| # | Task Group | Files | Dependencies | Status |
|---|------------|-------|--------------|--------|
| 1 | RAG Retrieval | 5 files | Sprint 2 ✅ | ⏳ Pending |
| 2 | Idea Generation | 5 files | Task 1 | ⏳ Pending |
| 3 | Script Generation | 5 files | Task 1 | ⏳ Pending |
| 4 | Scene Breakdown | 5 files | Task 3 | ⏳ Pending |
| 5 | Integration | 5 files | Tasks 1-4 | ⏳ Pending |

---

## Files per Task Group

### Task Group 1: RAG Retrieval
```
docs/plan/CONTEXT-sprint3-rag-retrieval.md
docs/plan/SKILL-ROUTING-sprint3-rag-retrieval.md
docs/plan/PLAN-sprint3-rag-retrieval.md
docs/plan/MSEW-sprint3-rag-retrieval.md
docs/plan/ACCEPTANCE-sprint3-rag-retrieval.md
```

### Task Group 2: Idea Generation
```
docs/plan/CONTEXT-sprint3-idea-generation.md
docs/plan/SKILL-ROUTING-sprint3-idea-generation.md
docs/plan/PLAN-sprint3-idea-generation.md
docs/plan/MSEW-sprint3-idea-generation.md
docs/plan/ACCEPTANCE-sprint3-idea-generation.md
```

### Task Group 3: Script Generation
```
docs/plan/CONTEXT-sprint3-script-generation.md
docs/plan/SKILL-ROUTING-sprint3-script-generation.md
docs/plan/PLAN-sprint3-script-generation.md
docs/plan/MSEW-sprint3-script-generation.md
docs/plan/ACCEPTANCE-sprint3-script-generation.md
```

### Task Group 4: Scene Breakdown
```
docs/plan/CONTEXT-sprint3-scene-breakdown.md
docs/plan/SKILL-ROUTING-sprint3-scene-breakdown.md
docs/plan/PLAN-sprint3-scene-breakdown.md
docs/plan/MSEW-sprint3-scene-breakdown.md
docs/plan/ACCEPTANCE-sprint3-scene-breakdown.md
```

### Task Group 5: Integration
```
docs/plan/CONTEXT-sprint3-integration.md
docs/plan/SKILL-ROUTING-sprint3-integration.md
docs/plan/PLAN-sprint3-integration.md
docs/plan/MSEW-sprint3-integration.md
docs/plan/ACCEPTANCE-sprint3-integration.md
```

---

## SQL Migrations Required

| Migration | Table | Task Group |
|-----------|-------|------------|
| `0014_match_dna_chunks.sql` | RPC function | 1 |
| `0015_ideas.sql` | `generated_ideas` | 2 |
| `0016_scripts.sql` | `generated_scripts` | 3 |

---

## Output Files Summary

### Services (Python)
- `apps/worker/services/rag_service.py`
- `apps/worker/services/idea_generator.py`
- `apps/worker/services/antislop_service.py`
- `apps/worker/services/scene_breaker.py`

### Tasks (Celery)
- `apps/worker/tasks/script_generate.py`
- `apps/worker/tasks/scene_breakdown.py`

### API Routers
- `apps/api/routers/scripts.py`

### Tests
- `apps/worker/services/test_rag_service.py`
- `apps/worker/services/test_idea_generator.py`
- `apps/worker/services/test_antislop_service.py`
- `apps/worker/services/test_scene_breaker.py`
- `tests/unit/test_api_scripts.py`
- `tests/integration/test_script_flow.py`

---

## Estimated Timeline

| Task Group | Effort | Recommended |
|------------|--------|-------------|
| 1: RAG Retrieval | 6h | Tier 2 |
| 2: Idea Generation | 8h | Tier 2 |
| 3: Script Generation | 12h | Tier 2 |
| 4: Scene Breakdown | 8h | Tier 2 |
| 5: Integration | 4h | Tier 2 |
| **Total** | **~38h** | |

---

## Next Steps

1. Tier 2 đọc từng Task Group theo thứ tự
2. Implement theo MSEW checklist
3. Self-verify với ACCEPTANCE criteria
4. Báo cáo khi hoàn thành từng Task Group
