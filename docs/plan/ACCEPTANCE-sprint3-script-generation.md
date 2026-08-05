# Sprint 3 Task Group 3: Script Generation - Acceptance Criteria

## Definition of Done

### Để task này được coi là **HOÀN THÀNH**, Tầng 2 phải:

---

## AC1: SQL Migration

- [ ] **AC1.1:** Migration `0016_scripts.sql` tồn tại
- [ ] **AC1.2:** Table `generated_scripts` có đúng columns
- [ ] **AC1.3:** Foreign key đến `channel_assistants`
- [ ] **AC1.4:** RLS policy cho user access

---

## AC2: Anti-Slop Layer 1 (Regex)

- [ ] **AC2.1:** Detect Vietnamese slop patterns
- [ ] **AC2.2:** Detect English slop patterns
- [ ] **AC2.3:** Detect excessive filler words
- [ ] **AC2.4:** Return violations list

### Test AC2:

```python
# Slop detected
is_clean, violations = service.layer1_regex_check("Cảm ơn bạn đã xem video này")
assert is_clean is False

# Clean text
is_clean, violations = service.layer1_regex_check("Hôm nay tôi sẽ hướng dẫn...")
assert is_clean is True
```

---

## AC3: Anti-Slop Layer 2 (LLM Scoring)

- [ ] **AC3.1:** LLM returns score 1-10
- [ ] **AC3.2:** LLM returns reason
- [ ] **AC3.3:** JSON response parsing works
- [ ] **AC3.4:** Default model is gpt-4o-mini

### Test AC3:

```python
mock_client = MagicMock()
mock_client.chat.completions.create.return_value = MagicMock(
    choices=[MagicMock(message=MagicMock(content='{"score": 8, "reason": "good"}'))]
)
score, reason = service.layer2_llm_semantic_check("test", client=mock_client)
assert score == 8
assert reason == "good"
```

---

## AC4: Anti-Slop Layer 3 (Cost Cap)

- [ ] **AC4.1:** Stop retry when budget exceeded
- [ ] **AC4.2:** Return best attempt on max retries
- [ ] **AC4.3:** Track total cost
- [ ] **AC4.4:** Return correct status

### Test AC4:

```python
result = service.validate_with_retry(
    text="clean text",
    client=mock_client,
    max_retries=3,
    min_score=6.0,
    budget_usd=0.10,
)
assert 'status' in result
assert 'total_cost' in result
assert 'attempts' in result
```

---

## AC5: Celery Task

- [ ] **AC5.1:** Task `apps.worker.tasks.script_generate.run` registered
- [ ] **AC5.2:** Uses RAG for context
- [ ] **AC5.3:** Uses Anti-Slop validation
- [ ] **AC5.4:** Saves to `generated_scripts` table
- [ ] **AC5.5:** Updates job status

---

## AC6: API Endpoint

- [ ] **AC6.1:** `POST /api/scripts/generate` works
- [ ] **AC6.2:** Auth required
- [ ] **AC6.3:** Validates assistant belongs to user
- [ ] **AC6.4:** Returns job_id for tracking

### Test AC6:

```bash
curl -X POST http://localhost:8000/api/scripts/generate \
  -H "Authorization: Bearer <token>" \
  -d '{"assistant_id": "uuid", "topic": "test"}'
```

---

## AC7: Unit Tests

- [ ] **AC7.1:** Tests for Layer 1 patterns
- [ ] **AC7.2:** Tests for Layer 2 mock
- [ ] **AC7.3:** Tests for Layer 3 budget
- [ ] **AC7.4:** All pass: `pytest -v`

---

## Self-Check

1. [ ] All AC1-AC7 ✅
2. [ ] `pytest services/test_antislop_service.py -v` → PASSED
3. [ ] `ReadLints` → No errors

---

## Sign-off

```
✓ Task: Sprint 3 - Script Generation
✓ Status: COMPLETED
✓ Files Created:
  - supabase/migrations/0016_scripts.sql
  - apps/worker/services/antislop_service.py
  - apps/worker/tasks/script_generate.py
  - apps/api/routers/scripts.py
  - apps/worker/services/test_antislop_service.py
✓ All Acceptance Criteria: PASSED
✓ Ready for next task group: Scene Breakdown
```
