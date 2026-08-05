# Sprint 3 Task Group 4: Scene Breakdown - Acceptance Criteria

## Definition of Done

---

## AC1: Scene Segmentation

- [ ] **AC1.1:** Script split by paragraphs (`\n\n`)
- [ ] **AC1.2:** Each paragraph becomes a scene
- [ ] **AC1.3:** Empty paragraphs ignored
- [ ] **AC1.4:** Scene number assigned sequentially

### Test AC1:

```python
script = "Para 1.\n\nPara 2.\n\nPara 3."
scenes = breaker.segment_scenes(script)
assert len(scenes) == 3
assert scenes[0]['scene_number'] == 1
```

---

## AC2: WPM Duration

- [ ] **AC2.1:** Duration = words / wpm
- [ ] **AC2.2:** Default WPM = 150
- [ ] **AC2.3:** WPM override from channel profile works
- [ ] **AC2.4:** Duration in seconds (not minutes)

### Test AC2:

```python
# 150 words / 150 wpm = 1 minute = 60 seconds
script = "Word " * 150
scenes = breaker.segment_scenes(script, wpm=150)
assert scenes[0]['duration_seconds'] == pytest.approx(60.0, rel=1)
```

---

## AC3: Timestamps

- [ ] **AC3.1:** First scene starts at 0.0
- [ ] **AC3.2:** `end_time = start_time + duration`
- [ ] **AC3.3:** Timestamps cumulative
- [ ] **AC3.4:** Timestamps rounded to 1 decimal

### Test AC3:

```python
scenes = breaker.segment_scenes("Para1.\n\nPara2.")
assert scenes[0]['start_time'] == 0.0
assert scenes[1]['start_time'] == scenes[0]['end_time']
```

---

## AC4: B-Roll Keywords

- [ ] **AC4.1:** Extract VN keywords with patterns
- [ ] **AC4.2:** Deduplicate keywords
- [ ] **AC4.3:** Max 5 keywords per scene
- [ ] **AC4.4:** Handle empty text

### Test AC4:

```python
text = "đang nấu ăn tại bếp"
keywords = breaker._extract_broll_keywords(text)
assert len(keywords) <= 5
```

---

## AC5: B-Roll Translation

- [ ] **AC5.1:** Translate VN → EN
- [ ] **AC5.2:** Generate pexels_query
- [ ] **AC5.3:** Map back to scenes
- [ ] **AC5.4:** Handle empty keywords

### Test AC5:

```python
translations = await breaker.translate_broll_keywords(["nấu ăn"], mock_client)
assert translations[0]['vn'] == "nấu ăn"
assert 'en' in translations[0]
```

---

## AC6: Save to Database

- [ ] **AC6.1:** Update `generated_scripts.scenes` with scenes array
- [ ] **AC6.2:** Job status updated to succeeded
- [ ] **AC6.3:** result_payload contains scenes

---

## AC7: Unit Tests

- [ ] **AC7.1:** Test scene segmentation
- [ ] **AC7.2:** Test duration calculation
- [ ] **AC7.3:** Test keyword extraction
- [ ] **AC7.4:** All pass

---

## Self-Check

1. [ ] All AC1-AC7 ✅
2. [ ] `pytest services/test_scene_breaker.py -v` → PASSED
3. [ ] `ReadLints` → No errors

---

## Sign-off

```
✓ Task: Sprint 3 - Scene Breakdown
✓ Status: COMPLETED
✓ Files Created:
  - apps/worker/services/scene_breaker.py
  - apps/worker/tasks/scene_breakdown.py
  - apps/worker/services/test_scene_breaker.py
✓ All Acceptance Criteria: PASSED
✓ Ready for next task group: Integration
```
