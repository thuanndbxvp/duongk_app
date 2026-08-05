# Sprint 3 Task Group 5: Integration - Acceptance Criteria

## Definition of Done

---

## AC1: API Unit Tests

- [ ] **AC1.1:** `test_generate_script_missing_topic` - returns 422
- [ ] **AC1.2:** `test_generate_script_invalid_uuid` - returns 422
- [ ] **AC1.3:** `test_generate_script_assistant_not_found` - returns 404
- [ ] **AC1.4:** `test_generate_script_success` - returns 201 with job_id

### Test AC1:

```bash
pytest tests/unit/test_api_scripts.py -v
```

---

## AC2: Integration Tests

- [ ] **AC2.1:** `test_full_pipeline_flow` - end-to-end works
- [ ] **AC2.2:** `test_anti_slop_validation` - slop detected
- [ ] **AC2.3:** `test_error_handling_invalid_assistant` - 404
- [ ] **AC2.4:** `test_realtime_progress` - progress visible

### Test AC2:

```bash
pytest tests/integration/test_script_flow.py -v -m integration
```

---

## AC3: GET Script Endpoint

- [ ] **AC3.1:** `GET /api/scripts/{id}` returns script with scenes
- [ ] **AC3.2:** Returns 404 for missing script
- [ ] **AC3.3:** Returns 403 for non-owned script
- [ ] **AC3.4:** Response includes score, cost, metadata

---

## AC4: Full Pipeline Works

- [ ] **AC4.1:** Script generation uses RAG
- [ ] **AC4.2:** Script generation uses anti-slop
- [ ] **AC4.3:** Scene breakdown segments correctly
- [ ] **AC4.4:** Results saved to database

---

## AC5: Error Handling

- [ ] **AC5.1:** Invalid input returns 422
- [ ] **AC5.2:** Not found returns 404
- [ ] **AC5.3:** Unauthorized returns 401/403
- [ ] **AC5.4:** Server error returns 500

---

## Self-Check

1. [ ] All AC1-AC5 ✅
2. [ ] `pytest tests/ -v` → PASSED
3. [ ] `ReadLints` → No errors

---

## Sign-off

```
✓ Task: Sprint 3 - Integration
✓ Status: COMPLETED
✓ Files Created:
  - tests/unit/test_api_scripts.py
  - tests/integration/test_script_flow.py
  - tests/conftest.py
  - apps/api/routers/scripts.py (updated)
✓ All Acceptance Criteria: PASSED
✓ SPRINT 3 COMPLETE
```
