# Sprint 3 Task Group 1: RAG Retrieval - Acceptance Criteria

## Definition of Done

### Để task này được coi là **HOÀN THÀNH**, Tầng 2 phải:

---

## AC1: SQL RPC Function

- [ ] **AC1.1:** Migration file `0014_match_dna_chunks.sql` tồn tại trong `supabase/migrations/`
- [ ] **AC1.2:** Function `match_dna_chunks()` có signature đúng:
  - Input params: `p_assistant_id`, `p_query_embedding`, `p_top_k`, `p_lambda`, `p_section_filter`
  - Output: `TABLE(chunk_id, text, section, timestamp_start, timestamp_end, similarity, mmr_score)`
- [ ] **AC1.3:** Function dùng `VECTOR(1024)` type
- [ ] **AC1.4:** Filter `expires_at > NOW()` được áp dụng

### Test AC1:

```sql
-- Test: Call function với mock data
SELECT * FROM match_dna_chunks(
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid,
  gen_random_vector(1024)::vector,
  10,
  0.7,
  NULL
);
```

---

## AC2: MMR Algorithm

- [ ] **AC2.1:** MMR selection chọn chunk đầu tiên dựa trên **similarity cao nhất**
- [ ] **AC2.2:** Các chunk tiếp theo được chọn dựa trên **MMR score = λ × sim - (1-λ) × max_j(sim(doc_i, doc_j))**
- [ ] **AC2.3:** Lambda = 1.0 → chỉ relevance (như vector search thông thường)
- [ ] **AC2.4:** Lambda = 0.0 → chỉ diversity (chọn chunks khác nhau nhất)
- [ ] **AC2.5:** Không duplicate chunks trong kết quả

### Test AC2:

```python
# Test MMR với 2 chunks giống nhau
# Khi lambda=0.7, chunks giống nhau nên diversity penalty cao
# → MMR score của chunk thứ 2 sẽ thấp hơn
```

---

## AC3: Python RAGService

- [ ] **AC3.1:** Class `RAGService` tồn tại trong `apps/worker/services/rag_service.py`
- [ ] **AC3.2:** Constructor nhận `supabase` và `embedding_router`
- [ ] **AC3.3:** Method `retrieve_context()` là `async`
- [ ] **AC3.4:** Method trả về dict với keys: `chunks`, `context_text`, `num_chunks`
- [ ] **AC3.5:** Gọi `embedding_router.embed()` trước khi query RPC

### Test AC3:

```python
# Mock test
rag_service = RAGService(mock_supabase, mock_embedding_router)
context = await rag_service.retrieve_context(
    assistant_id="uuid",
    query="test query",
)
assert 'chunks' in context
assert 'context_text' in context
assert 'num_chunks' in context
```

---

## AC4: Context Assembly

- [ ] **AC4.1:** Timestamp được format đúng: `[MM:SS]` (VD: `[00:00]`, `[01:05]`)
- [ ] **AC4.2:** Chunks được nối với separator `\n\n---\n\n`
- [ ] **AC4.3:** `num_chunks` = số lượng chunks trong list
- [ ] **AC4.4:** Handle null timestamp (không crash)

### Test AC4:

```python
chunks = [
    {'timestamp_start': 0.0, 'text': 'A'},
    {'timestamp_start': 65.5, 'text': 'B'},  # 1m 5s
]
result = rag_service._assemble_context(chunks)
assert '[00:00] A' in result['context_text']
assert '[01:05] B' in result['context_text']
assert '\n\n---\n\n' in result['context_text']
```

---

## AC5: Script Prompt Builder

- [ ] **AC5.1:** Method `build_script_prompt()` tồn tại
- [ ] **AC5.2:** Prompt chứa channel name, emotional signature, WPM
- [ ] **AC5.3:** Prompt chứa top 3 mimic rules
- [ ] **AC5.4:** Prompt chứa RAG context
- [ ] **AC5.5:** Prompt chứa topic
- [ ] **AC5.6:** Prompt yêu cầu JSON response format

### Test AC5:

```python
persona = {'channel_name': 'Test', 'mimic_rules': [{'do': ['Rule 1']}]}
prompt = rag_service.build_script_prompt(persona, "context", "topic")
assert 'Test' in prompt
assert 'Rule 1' in prompt
assert 'context' in prompt
assert 'topic' in prompt
assert '"title":' in prompt
```

---

## AC6: Unit Tests

- [ ] **AC6.1:** File test tồn tại: `apps/worker/services/test_rag_service.py`
- [ ] **AC6.2:** Test `retrieve_context` mock thành công
- [ ] **AC6.3:** Test `assemble_context` timestamp formatting
- [ ] **AC6.4:** Test `build_script_prompt` output format
- [ ] **AC6.5:** Tests pass: `pytest services/test_rag_service.py -v`

---

## AC7: Code Quality

- [ ] **AC7.1:** Type hints đầy đủ (parameters, return values)
- [ ] **AC7.2:** Docstrings cho class và public methods
- [ ] **AC7.3:** No linter errors (`ReadLints` clean)
- [ ] **AC7.4:** Import từ `apps.worker.services.*` (existing pattern)

---

## Self-Check Checklist

Trước khi báo cáo hoàn thành, Tầng 2 phải:

1. [ ] Tất cả AC1-AC7 đều ✅
2. [ ] Chạy `pytest services/test_rag_service.py -v` → PASSED
3. [ ] `ReadLints` → No errors
4. [ ] Code follows existing patterns

---

## Sign-off

```
✓ Task: Sprint 3 - RAG Retrieval
✓ Status: COMPLETED
✓ Files Created:
  - supabase/migrations/0014_match_dna_chunks.sql
  - apps/worker/services/rag_service.py
  - apps/worker/services/test_rag_service.py
✓ All Acceptance Criteria: PASSED
✓ Ready for next task group: Idea Generation
```
