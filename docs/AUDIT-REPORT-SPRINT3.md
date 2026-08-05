# BÁO CÁO AUDIT — SPRINT 3: TASK GROUP 1 → 5

**Ngày audit:** 2026-08-05
**Người thực hiện:** Tầng 2 (Kỹ sư Thực thi)
**Phạm vi:** Kiểm tra thực trạng hoàn thành của 5 Task Groups trong Sprint 3
**Kết luận chung:** ⚠️ **SPRINT 3 ĐẠT ~75%** — Code Python chất lượng cao nhưng **3 SQL migrations quan trọng bị thiếu**, có 2 lỗi runtime nghiêm trọng

---

## LƯU Ý QUAN TRỌNG

- Sprint 3 được tổ chức thành **5 Task Groups** (không phải task đơn lẻ như Sprint 1-2)
- Mỗi Task Group có 5 files planning: CONTEXT, SKILL-ROUTING, PLAN, MSEW, ACCEPTANCE
- Tất cả 5 ACCEPTANCE files đều tự claim **"Status: COMPLETED"** — cần verify độc lập
- **File `docs/sprints/03_sprint3_*.md` KHÔNG TỒN TẠI** — planning nằm trong `docs/plan/`

---

## TỔNG QUAN KẾT QUẢ AUDIT

| # | Task Group | Mô tả | Trạng thái | Mức độ |
|---|-----------|-------|-----------|--------|
| 1 | RAG Retrieval | SQL RPC + Python RAGService | ⚠️ PARTIAL | 70% |
| 2 | Idea Generation | HDBSCAN + Gap Score | ⚠️ PARTIAL | 75% |
| 3 | Script Generation | Anti-Slop + Celery task | ⚠️ PARTIAL | 80% |
| 4 | Scene Breakdown | WPM segmentation + B-roll | ⚠️ PARTIAL | 85% |
| 5 | Integration | API tests + pipeline | ⚠️ PARTIAL | 70% |

**Tổng kết: 0/5 task groups hoàn thành đầy đủ. Code Python rất tốt nhưng thiếu migrations và có lỗi runtime.**

---

## CHI TIẾT TỪNG TASK GROUP

### Task Group 1 — RAG Retrieval ⚠️ 70%

**Yêu cầu:** SQL RPC `match_dna_chunks` với MMR + Python `RAGService.retrieve_context()`

| File | Trạng thái | Đánh giá |
|------|-----------|----------|
| `supabase/migrations/0014_match_dna_chunks.sql` | ❌ **THIẾU** | **RPC function không tồn tại.** `RAGService.retrieve_context()` gọi `supabase.rpc('match_dna_chunks', ...)` → sẽ fail runtime. |
| `apps/worker/services/rag_service.py` | ✅ CÓ | Class `RAGService` đầy đủ: `retrieve_context()`, `_assemble_context()`, `build_script_prompt()`. Code chất lượng cao, có type hints, docstrings. |
| `apps/worker/services/test_rag_service.py` | ✅ CÓ | Test với mock Supabase client. Test `retrieve_context`, `assemble_context`, `build_script_prompt`. |
| `build_script_prompt()` | ✅ CÓ | Prompt tiếng Việt chi tiết: channel persona, mimic rules, RAG context, topic, JSON schema. |

**🔴 Lỗi runtime #1:** `RAGService.retrieve_context()` gọi `self.embedding_router.embed(query)` nhưng class `EmbeddingRouter` (trong `apps/api/modules/rag/embedding_router.py`) **không có method `embed()`**. Class này chỉ có `detect_language()` và `get_model_config()`. Method `embed()` tồn tại trong class `Embedder` (file `embedder.py`), không phải `EmbeddingRouter`.

**Kết luận:** Code service tốt nhưng không thể chạy vì thiếu RPC migration và sai API call tới EmbeddingRouter.

---

### Task Group 2 — Idea Generation ⚠️ 75%

**Yêu cầu:** HDBSCAN clustering + Gap Score Formula A14 + `generated_ideas` table

| File | Trạng thái | Đánh giá |
|------|-----------|----------|
| `supabase/migrations/0015_ideas.sql` | ❌ **THIẾU** | Bảng `generated_ideas` không tồn tại. Code gọi `supabase.table('generated_ideas').insert(...)` → sẽ fail. |
| `apps/worker/services/idea_generator.py` | ✅ CÓ | Class `IdeaGenerator` với 5 methods: `cluster_topics()` (HDBSCAN + TF-IDF), `calculate_gap_score()` (Formula A14), `assign_confidence()`, `generate_opportunity_description()`, `_get_cluster_names()`. Code thực chất, dùng `sklearn` + `hdbscan`. |
| `apps/worker/tasks/idea_generate.py` | ✅ CÓ | Celery task `idea_generate.run` với ProgressTracker integration. |
| `apps/worker/services/test_idea_generator.py` | ✅ CÓ | Test HDBSCAN clustering, gap score calculation, confidence assignment. |

**Đánh giá chất lượng code:**
- HDBSCAN implementation đúng: TF-IDF vectorize → HDBSCAN với `min_cluster_size=3`, `cluster_selection_method='eom'`
- Gap Score formula đúng: `(niche_avg_views - channel_avg_views) / channel_avg_views`
- Edge case handling: < min_cluster_size topics → all 'misc', channel_avg_views <= 0 → return 0.0
- Confidence thresholds đúng: >0.3 HIGH, 0-0.3 MEDIUM, <0 LOW

**Kết luận:** Code hoàn chỉnh nhưng thiếu migration tạo bảng `generated_ideas`.

---

### Task Group 3 — Script Generation & Anti-Slop ⚠️ 80%

**Yêu cầu:** Anti-Slop 3 layers + Celery task + API endpoint + `generated_scripts` table

| File | Trạng thái | Đánh giá |
|------|-----------|----------|
| `supabase/migrations/0016_scripts.sql` | ❌ **THIẾU** | Bảng `generated_scripts` không tồn tại. |
| `apps/worker/services/antislop_service.py` | ✅ CÓ | **Code xuất sắc.** 3 layers: Layer 1 (Regex VN + EN patterns), Layer 2 (GPT-4o-mini scoring 1-10), Layer 3 (Cost-capped retry max $0.10, best-of-N). |
| `apps/worker/tasks/script_generate.py` | ✅ CÓ | **Pipeline hoàn chỉnh:** RAG retrieval → GPT-4o-mini generation → Anti-Slop validation → Save to DB. 3 phases với ProgressTracker. |
| `apps/api/modules/script/routes.py` | ✅ CÓ | 3 endpoints: `POST /api/scripts/generate`, `POST /api/scripts/breakdown-scenes`, `GET /api/scripts/{id}`. Đã đăng ký trong `main.py`. |
| `apps/worker/services/test_antislop_service.py` | ✅ CÓ | Test regex patterns, LLM mock, budget cap. |
| `apps/api/modules/llm/prompts.py` | ✅ CÓ | **Đã được tạo** (thiếu trong Sprint 2 audit). Prompt templates cho hook analysis, structure extraction, mimic rules. |

**🔴 Lỗi runtime #2:** `script_generate.py` gọi `tracker.tick('rag_retrieve', 10)` nhưng class `ProgressTracker` (trong `apps/worker/progress_tracker.py`) **không có method `tick()`**. Class chỉ có: `start()`, `update()`, `increment()`, `complete()`, `fail()`. Gọi `tick()` sẽ throw `AttributeError`.

**Kết luận:** Code anti-slop và script generation pipeline rất tốt. Thiếu migration + lỗi API ProgressTracker.

---

### Task Group 4 — Scene Breakdown ⚠️ 85%

**Yêu cầu:** WPM-based segmentation + B-roll keyword extraction + translation

| File | Trạng thái | Đánh giá |
|------|-----------|----------|
| `apps/worker/services/scene_breaker.py` | ✅ CÓ | Class `SceneBreaker` với 4 methods: `segment_scenes()` (paragraph split + WPM duration), `_extract_broll_keywords()` (regex patterns), `translate_broll_keywords()` (GPT-4o-mini), `calculate_total_duration()`. |
| `apps/worker/tasks/scene_breakdown.py` | ✅ CÓ | Celery task với ProgressTracker integration. |
| `apps/worker/services/test_scene_breaker.py` | ✅ CÓ | Test segmentation, duration, keywords, translation. |

**Đánh giá chất lượng code:**
- WPM formula đúng: `duration_seconds = (words / wpm) * 60`
- B-roll patterns: 5 regex patterns cho tiếng Việt (đang + noun, tại + location, nấu + food, làm + action, cho + food_prep)
- Translation dùng GPT-4o-mini với JSON response format
- Deduplicate keywords, max 5 per scene
- Timestamps cumulative, rounded to 1 decimal

**Kết luận:** Code gần như hoàn chỉnh. Không có migration riêng (scenes lưu trong `generated_scripts.scenes` JSONB). Task group này hoàn thiện nhất.

---

### Task Group 5 — Integration & API Testing ⚠️ 70%

**Yêu cầu:** Integration tests + API unit tests + full pipeline verification

| File | Trạng thái | Đánh giá |
|------|-----------|----------|
| `tests/integration/test_script_flow.py` | ✅ CÓ | Integration test cho full pipeline. |
| `tests/unit/test_api_scripts.py` | ✅ CÓ | Unit test cho API endpoints. |
| `tests/conftest.py` | ✅ CÓ | Shared fixtures. |
| `apps/api/modules/script/routes.py` | ✅ CÓ | GET endpoint cho script retrieval với ownership verification. |
| Router registration in `main.py` | ✅ CÓ | `script_router` đã được import và include. |

**Kết luận:** Integration tests và API endpoints đã có. Tuy nhiên, không thể chạy thực tế vì phụ thuộc vào migrations thiếu từ Task Groups 1-3.

---

## TỔNG HỢP THIẾU SÓT

### Files còn thiếu (3 files — tất cả là SQL migrations):

| # | File | Task Group | Mức độ | Impact |
|---|------|-----------|--------|--------|
| 1 | `supabase/migrations/0014_match_dna_chunks.sql` | TG1 | 🔴 **Critical** | RAG retrieval không hoạt động |
| 2 | `supabase/migrations/0015_ideas.sql` | TG2 | 🔴 **Critical** | Idea generation không lưu được |
| 3 | `supabase/migrations/0016_scripts.sql` | TG3 | 🔴 **Critical** | Script generation không lưu được |

### Lỗi runtime (2 lỗi):

| # | Vị trí | Mô tả | Impact |
|---|--------|-------|--------|
| 1 | `rag_service.py:45` | Gọi `self.embedding_router.embed(query)` — method không tồn tại. Phải dùng `Embedder.embed_texts()` thay vì `EmbeddingRouter.embed()`. | 🔴 RAG pipeline crash |
| 2 | `script_generate.py:42,58,70,81` | Gọi `tracker.tick(...)` — method không tồn tại. Phải dùng `tracker.increment()` hoặc thêm method `tick()` vào ProgressTracker. | 🔴 Script generation crash |

---

## SO SÁNH CHẤT LƯỢNG GIỮA CÁC SPRINT

| Tiêu chí | Sprint 1 | Sprint 2 | Sprint 3 |
|----------|----------|----------|----------|
| Mức độ hoàn thành | ~20% | ~60% | ~75% |
| Chất lượng code | Skeleton/placeholder | Code thực chất | **Code production-grade** |
| Số files đã tạo | ~15 | ~25+ | ~20+ |
| Services (Python) | 1 (youtube.py) | 8+ | 4 (rag, idea, antislop, scene) |
| Celery tasks | 0 | 1 (skeleton) | 3 (script, scene, idea) |
| API routers | 3 | 7 | 8 (+script router) |
| SQL migrations | 11 (chất lượng thấp) | 0 mới | 0 mới (thiếu 3) |
| Tests | 3 files | 3 files | 5 files (unit + integration) |
| Lỗi runtime | Nhiều | Ít | 2 lỗi cụ thể |
| Anti-patterns | Thiếu auth, thiếu credit | Thiếu dependencies | Thiếu migrations |

---

## ĐIỂM TÍCH CỰC NỔI BẬT

1. ✅ **Code Python đạt production-grade:**
   - `AntiSlopService` — 3-layer validation (Regex → LLM → Cost cap) với best-of-N selection
   - `IdeaGenerator` — HDBSCAN clustering thực thụ với TF-IDF vectorization
   - `SceneBreaker` — WPM-based duration calculation chuẩn xác
   - `RAGService` — Prompt engineering tiếng Việt chi tiết với JSON schema

2. ✅ **Pipeline end-to-end đã được thiết kế:** `script_generate.py` tích hợp RAG → LLM → Anti-Slop → Save trong 1 Celery task duy nhất

3. ✅ **API endpoints đầy đủ:** `POST /api/scripts/generate`, `POST /api/scripts/breakdown-scenes`, `GET /api/scripts/{id}`

4. ✅ **Test coverage tốt:** Unit tests cho từng service + Integration test cho full pipeline

5. ✅ **Đã fix 1 lỗi từ Sprint 2:** `apps/api/modules/llm/prompts.py` đã được tạo (trước đây thiếu)

6. ✅ **Script router đã đăng ký trong `main.py`** — kiến trúc API hoàn chỉnh

---

## KHUYẾN NGHỊ HÀNH ĐỘNG (THEO THỨ TỰ ƯU TIÊN)

### Giai đoạn 1 — Vá lỗi runtime (1-2 giờ)

1. **Fix `rag_service.py` line 45** (P0 — Critical)
   - Thay `self.embedding_router.embed(query)` → dùng `Embedder` class thay vì `EmbeddingRouter`
   - Hoặc thêm method `embed()` vào `EmbeddingRouter` delegate sang `Embedder`

2. **Fix `script_generate.py`** (P0 — Critical)
   - Thay tất cả `tracker.tick(...)` → `tracker.increment(...)` 
   - Hoặc thêm method `tick()` alias vào `ProgressTracker`

### Giai đoạn 2 — Tạo migrations (3-4 giờ)

3. **Tạo `0014_match_dna_chunks.sql`** (P0 — Block RAG)
   - Implement MMR algorithm trong PL/pgSQL
   - Signature: `match_dna_chunks(p_assistant_id, p_query_embedding, p_top_k, p_lambda, p_section_filter)`

4. **Tạo `0015_ideas.sql`** (P0 — Block Idea Gen)
   - Tạo bảng `generated_ideas` với schema từ CONTEXT

5. **Tạo `0016_scripts.sql`** (P0 — Block Script Gen)
   - Tạo bảng `generated_scripts` với schema từ CONTEXT

### Giai đoạn 3 — Verify (1-2 giờ)

6. **Chạy integration tests** sau khi fix migrations
7. **End-to-end test:** Generate script → Breakdown scenes → Verify DB

---

## KẾT LUẬN

**Sprint 3 đạt ~75% khối lượng**, là sprint có chất lượng code cao nhất trong 3 sprint. Các service Python được viết cẩn thận với type hints, docstrings, edge case handling, và test coverage.

**Tuy nhiên**, 3 vấn đề chặn việc chạy thực tế:
1. **Thiếu 3 SQL migrations** (0014, 0015, 0016) — tất cả các bảng mới không tồn tại
2. **2 lỗi runtime** trong RAG service và script generate task — sẽ crash ngay khi gọi
3. **ACCEPTANCE files claim "COMPLETED" nhưng thực tế chưa** — cần update lại trạng thái

**So với Sprint 1 (20%) và Sprint 2 (60%):** Sprint 3 có chất lượng code vượt trội, pipeline được thiết kế end-to-end rõ ràng. Nếu fix 3 migrations + 2 lỗi runtime, Sprint 3 có thể hoàn thành trong 1-2 ngày.

**Ước tính thời gian còn lại:** ~6-8 giờ làm việc (khoảng 1 ngày với 2 developers).