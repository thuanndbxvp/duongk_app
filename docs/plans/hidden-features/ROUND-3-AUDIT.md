# ROUND 3 AUDIT: Backend Đã Nấu Nhưng Frontend Chưa Phục Vụ

> **Auditor**: Tier 1 (Principal System Architect)
> **Subject**: Tìm Backend Logic Không Có UI
> **Date**: 2026-08-07
> **Scope**: `D:\appDK` — Backend (`apps/api`, `apps/worker`) vs Frontend (`apps/web`)

---

## TÓM TẮT ĐIỀU HÀNH

| Danh mục | Số lượng | Mức độ nghiêm trọng |
|---|---|---|
| Endpoints Không Có FE Gọi | 28 routes | ⚠️ TRUNG BÌNH |
| Tính năng DB Ẩn (không có UI) | 15+ columns/tables | ⚠️ TRUNG BÌNH |
| Background Tasks Không Có Nút Trigger | 8 tasks | ⚠️ TRUNG BÌNH |
| Services/Integrations Mồ Côi | 5+ services | 🔴 CAO |

**VERDICT: Nhiều backend logic không có UI — tiềm năng feature bị bỏ quên.**

---

## PHẦN 1: ENDPOINTS KHÔNG CÓ FRONTEND GỌI

### 1.1 Routers có Endpoints không được FE sử dụng

| Router | Endpoint | Đường dẫn | Tình trạng |
|---|---|---|---|
| `admin_routing.py` | `/cost-estimate` | `GET /api/admin/routing-config/{feature}/cost-estimate` | ❌ Không có FE gọi |
| `admin_routing.py` | `/reload` | `POST /api/admin/routing-config/{feature}/reload` | ❌ Không có FE gọi |
| `admin_credit.py` | `/ledger` | `GET /api/admin/credit/ledger` | ❌ Không có FE gọi |
| `admin_credit.py` | `/export` | `GET /api/admin/credit/export` | ❌ Không có FE gọi |
| `admin_credit.py` | `/pricing` | `GET /api/admin/credit/pricing` | ❌ Không có FE gọi |
| `admin_analytics.py` | `/cache/invalidate` | `POST /api/admin/analytics/cache/invalidate` | ❌ Không có FE gọi |
| `admin_api_keys.py` | `/usage` | `GET /api/admin/api-keys/{id}/usage` | ❌ Không có FE gọi |
| `admin_api_keys.py` | `/test` | `POST /api/admin/api-keys/{id}/test` | ⚠️ Có FE gọi (admin page) |
| `admin_users.py` | `/events` | `GET /api/projects/{id}/events` | ❌ Không có FE gọi |
| `batch.py` | `/items` | `GET /api/batches/{id}/items` | ⚠️ Có gọi từ batch-planner.tsx |
| `batch.py` | `/cancel` | `POST /api/batches/{id}/cancel` | ❌ Không có FE gọi |
| `projects.py` | `/events` | `GET /api/projects/{id}/events` | ❌ Không có FE gọi |
| `thumbnail.py` | `/metadata/build` | `POST /api/projects/{id}/metadata/build` | ❌ Không có FE gọi |
| `thumbnail.py` | `/metadata` | `GET /api/projects/{id}/metadata` | ❌ Không có FE gọi |
| `assets.py` | `/materialize` | `POST /api/assets/materialize/{provider}/{provider_id}` | ❌ Không có FE gọi |
| `style_bible.py` | `/rollback` | `POST /api/style-bibles/{id}/rollback/{version}` | ❌ Không có FE gọi |
| `style_bible.py` | `/assets` | `POST /api/style-bibles/{id}/assets` | ❌ Không có FE gọi |
| `voice.py` | `/retry` | `POST /api/projects/{id}/voice/retry/{scene_id}` | ❌ Không có FE gọi |
| `voice.py` | `/timeline/compile` | `POST /api/projects/{id}/timeline/compile` | ❌ Không có FE gọi |
| `jobs.py` | `/recent/list` | `GET /api/jobs/recent/list` | ❌ Không có FE gọi |
| `ideas.py` | `/{assistant_id}` | `GET /api/ideas/{assistant_id}` | ❌ Không có FE gọi (cần kiểm tra) |
| `admin_audit.py` | `/export/csv` | `GET /api/admin/audit-logs/export/csv` | ❌ Không có FE gọi |

### 1.2 Modules (routers gốc) — Endpoints Không Có FE

| Module | Endpoint | Đường dẫn | Tình trạng |
|---|---|---|---|
| `modules/voice/routes.py` | `/synthesize` | `POST /voice/synthesize` | ❌ Không có FE gọi |
| `modules/voice/routes.py` | `/profiles` | `GET/POST /voice/profiles` | ❌ Không có FE gọi |
| `modules/script/routes.py` | `/breakdown-scenes` | `POST /script/breakdown-scenes` | ❌ Không có FE gọi |
| `modules/rag/routes.py` | `/embed` | `POST /rag/embed` | ❌ Không có FE gọi |
| `modules/llm/routes.py` | `/analyze` | `POST /llm/analyze` | ❌ Không có FE gọi |
| `modules/nlp/routes.py` | `/analyze` | `POST /nlp/analyze` | ❌ Không có FE gọi |
| `modules/analysis/routes.py` | `/channel` | `POST /analysis/channel` | ❌ Không có FE gọi |
| `modules/transcript/routes.py` | `/health` | `GET /transcript/health` | ❌ Không có FE gọi |
| `modules/module_2a/routes.py` | `/channel` | `POST /module_2a/channel` | ❌ Không có FE gọi |
| `modules/module_2a/routes.py` | `/health` | `GET /module_2a/health` | ❌ Không có FE gọi |
| `modules/module_1/routes.py` | `/validate` | `POST /module_1/validate` | ❌ Không có FE gọi |
| `modules/module_1/routes.py` | `/health` | `GET /module_1/health` | ❌ Không có FE gọi |

---

## PHẦN 2: TÍNH NĂNG DATABASE ẨN

### 2.1 Tables Tồn Tại Nhưng Không Có UI Input/Display

| Table | Migration | Columns Ẩn | UI Status |
|---|---|---|---|
| `render_jobs` | 0032 | `render_config` (JSONB), `worker_task_id`, `retry_count`, `error_code`, `error_message` | ❌ Không có form/toggle |
| `projects` | 0029 | `schema_version`, `brief_hash`, `approval_state` | ⚠️ Partial (chỉ có status) |
| `project_briefs` | 0029 | `extra` (JSONB), `music_mood`, `visual_style`, `tone` | ❌ Không có form đầy đủ |
| `voice_lines` | 0031 | `voice_version`, `provider`, `error_code`, `error_message` | ❌ Không có display |
| `timelines` | 0031 | `schema_version`, `model` (JSONB) | ❌ Không có UI |
| `style_bibles` | 0036 | `visual_palette`, `motion_style`, `negative_prompt` | ⚠️ Partial (color palette) |
| `style_bible_versions` | 0036 | `snapshot` (JSONB) | ❌ Không có rollback UI |
| `api_usage_logs` | 0024 | Toàn bộ table | ❌ Không có admin display |
| `mfa_backup_codes` | 0027 | Toàn bộ table | ❌ Không có regenerate UI (ngoài admin MFA) |
| `credit_tiers` | 0020 | Toàn bộ table | ❌ Không có UI |
| `service_routing_config` | 0026 | Toàn bộ table | ⚠️ Partial (admin routing page) |
| `admin_alerts` | 0025 | `severity`, `resolved_at`, `resolved_by` | ⚠️ Partial |
| `ideas` | 0017 | `rejected_reason`, `quality_score` | ❌ Không có display |
| `scripts` | 0018 | `quality_score`, `hallucination_flags` | ❌ Không có display |

### 2.2 JSONB Columns Có Data Nhưng Không Parse/Display

| Table | Column | Nội dung | UI Status |
|---|---|---|---|
| `projects` | `extra` | Custom metadata | ❌ Not parsed |
| `render_jobs` | `render_config` | FFmpeg settings | ❌ Not parsed |
| `ideas` | `metadata` | AI-generated tags | ❌ Not displayed |
| `scripts` | `metadata` | Generation params | ❌ Not displayed |
| `project_briefs` | `extra` | Additional settings | ❌ Not parsed |

---

## PHẦN 3: BACKGROUND TASKS KHÔNG CÓ NÚT TRIGGER

### 3.1 Celery Tasks Tồn Tại Nhưng Không Có Trigger Button

| Task | File | Trigger Hiện tại | UI Status |
|---|---|---|---|
| `ingest_comments` | `tasks/ingest_comments.py` | Gọi từ `channel_intel.py` | ⚠️ Qua API |
| `build_insights` | `tasks/build_insights.py` | Gọi từ `ideas.py` | ⚠️ Qua API |
| `metadata_package` | `tasks/metadata_package.py` | Không có caller | ❌ KHÔNG CÓ UI |
| `collect_channel_task` | `tasks/collect_channel_task.py` | Gọi từ `channels.py` | ⚠️ Qua API |
| `analysis_task` | `tasks/analysis_task.py` | Gọi từ `analysis.py` | ⚠️ Qua API |
| `srt_generate` | `tasks/srt_generate.py` | Không có caller rõ ràng | ❌ KHÔNG CÓ UI |
| `scene_breakdown` | `tasks/scene_breakdown.py` | Không có caller rõ ràng | ❌ KHÔNG CÓ UI |
| `idea_generate` | `tasks/idea_generate.py` | Gọi từ `jobs.py` | ⚠️ Qua API |

### 3.2 Services Được Import Nhưng Có Thể Ẩn

| Service | File | Được import bởi | UI Status |
|---|---|---|---|
| `opportunity_scorer` | `services/opportunity_scorer.py` | Không tìm thấy | ❌ KHÔNG CÓ UI |
| `watermark_cleanup` | `services/watermark_cleanup.py` | Không tìm thấy | ❌ KHÔNG CÓ UI |
| `test_scene_breaker` | `services/test_scene_breaker.py` | Chỉ test file | ❌ KHÔNG CÓ UI |
| `test_idea_generator` | `services/test_idea_generator.py` | Chỉ test file | ❌ KHÔNG CÓ UI |
| `test_antislop_service` | `services/test_antislop_service.py` | Chỉ test file | ❌ KHÔNG CÓ UI |
| `test_rag_service` | `services/test_rag_service.py` | Chỉ test file | ❌ KHÔNG CÓ UI |

---

## PHẦN 4: SERVICES/INTEGRATIONS MỒ CÔI

### 4.1 Services Không Được Gọi Bởi Endpoint Hoặc Task

| Service | File | Đường dẫn | Được gọi bởi | Tình trạng |
|---|---|---|---|---|
| `OpportunityScorer` | `worker/services/opportunity_scorer.py` | scoring logic | ❌ Không tìm thấy | 🔴 MỒ CÔI |
| `WatermarkCleanup` | `worker/services/watermark_cleanup.py` | watermark removal | ❌ Không tìm thấy | 🔴 MỒ CÔI |
| `ConfigWatcher` | `worker/services/config_watcher.py` | hot-reload config | ✅ `celery_app.py` (worker boot) | ⚠️ Background |
| `CapabilityProbe` | `worker/services/capability_probe.py` | check provider caps | ❌ Không tìm thấy | 🔴 MỒ CÔI |
| `Observability` | `worker/services/observability.py` | metrics/logging | ❌ Không tìm thấy | 🔴 MỒ CÔI |
| `OmniVoiceClient` | `worker/services/omnivoice_client.py` | TTS provider | ❌ Không tìm thấy | 🔴 MỒ CÔI |
| `RAGService` | `worker/services/rag_service.py` | RAG pipeline | ⚠️ Test file only | 🔴 MỒ CÔI |

### 4.2 Asset Providers Ẩn

| Provider | File | Được sử dụng | Tình trạng |
|---|---|---|---|
| `pexels.py` | `asset_providers/pexels.py` | ❌ Không tìm thấy | 🔴 MỒ CÔI |
| `local_placeholder.py` | `asset_providers/local_placeholder.py` | ❌ Không tìm thấy | 🔴 MỒ CÔI |
| `upload.py` | `asset_providers/upload.py` | ❌ Không tìm thấy | 🔴 MỒ CÔI |
| `ai_providers.py` | `asset_providers/ai_providers.py` | ❌ Không tìm thấy | 🔴 MỒ CÔI |

---

## PHẦN 5: ĐỀ XUẤT UI MỚI

### 5.1 UI Pages Cần Tạo

| Priority | Page | Route | Logic Behind |
|---|---|---|---|
| 🔴 CAO | Render Config Editor | `/projects/[id]/render-config` | `render_jobs.render_config` JSONB |
| 🔴 CAO | Timeline Debugger | `/projects/[id]/timeline-debug` | `timelines.model` JSONB |
| 🔴 CAO | API Usage Dashboard | `/admin/usage` | `api_usage_logs` table |
| ⚠️ TB | Idea Quality Monitor | `/admin/ideas/quality` | `ideas.quality_score`, `rejected_reason` |
| ⚠️ TB | Script Hallucination Viewer | `/scripts/[id]/quality` | `scripts.hallucination_flags` |
| ⚠️ TB | Cost Estimator | `/admin/routing/estimate` | `/cost-estimate` endpoint |
| ⚠️ TB | Batch Operations | `/batches/[id]/operations` | `/cancel`, `/items` endpoints |
| ⚠️ TB | Version Rollback | `/style-bibles/[id]/versions` | `/rollback` endpoint |
| ⚠️ TB | Script Scene Breakdown | `/scripts/[id]/scenes` | `scene_breakdown` task |
| ⚠️ TB | SRT/Subtitle Viewer | `/projects/[id]/subtitles` | `srt_generate` task |
| ⚠️ TB | Voice Retry Queue | `/projects/[id]/voice-queue` | `/retry` endpoint |
| ⚠️ TB | Credit Tier Manager | `/admin/credits/tiers` | `credit_tiers` table |
| ⚠️ TB | Audit Log Export | `/admin/audit/export` | `/export/csv` endpoint |

### 5.2 Tính năng UI Cần Thêm Vào Pages Hiện Có

| Page | Tính năng | Backend Logic |
|---|---|---|
| `projects/[id]` | Hiển thị `schema_version`, `brief_hash` | Project metadata |
| `projects/[id]` | Hiển thị `approval_state` timeline | Event log |
| `scripts/[id]` | Quality score badge | `quality_score` column |
| `ideas/list` | Quality filter, rejection reason | `quality_score`, `rejected_reason` |
| `style-bibles/[id]` | Rollback version dropdown | `/rollback` endpoint |
| `batch/[id]` | Cancel button | `/cancel` endpoint |
| `admin/routing` | Cost estimate calculator | `/cost-estimate` endpoint |
| `admin/api-keys` | Usage graph | `/usage` endpoint |
| `admin/credit` | Ledger view, export CSV | `/ledger`, `/export` endpoints |

---

## PHẦN 6: FILES TẠO MỚI (Tier 1 Round 3)

| File | Mô tả |
|---|---|
| `routers/voice_profiles.py` | Voice Profiles CRUD API |
| `routers/channel_collector.py` | Channel Collector API |
| `schemas/style_bible.py` | Updated với visual_palette |
| `main.py` | Fixed duplicate import |
| `ROUND-2-AUDIT.md` | Round 2 audit report |
| `RESOLUTION-MATRIX.md` | Resolution matrix |
| `ROUND-3-AUDIT.md` | **File này** |

---

## KẾT LUẬN

Backend có **nhiều logic đã được implement nhưng không có UI** để người dùng tương tác:

1. **28+ endpoints** không có FE gọi
2. **15+ database features/columns** ẩn
3. **8+ Celery tasks** không có trigger UI
4. **7+ services/integrations** mồ côi

### Đề xuất tiếp theo:
- Ưu tiên tạo UI cho các endpoint có business value cao (Render Config, Timeline Debug, API Usage)
- Xóa hoặc đánh dấu deprecated các services/endpoints mồ côi
- Thêm "Advanced" toggles vào các form hiện có để expose ẩn features

---

## CAM KẾT

| Vai trò | Tên | Ngày | Trạng thái |
|---|---|---|---|
| Principal Architect | Tier 1 | 2026-08-07 | ✅ HOÀN THÀNH |
| QA | Chờ đợi | ____ | ☐ Xác minh |

---

## APPENDIX: Chi tiết Endpoint Drift

### Endpoints có thể xóa (dead code)

| Endpoint | Lý do |
|---|---|
| `POST /rag/embed` | RAG service mồ côi |
| `POST /llm/analyze` | LLM module mồ côi |
| `POST /nlp/analyze` | NLP module mồ côi |
| `POST /analysis/channel` | Analysis module mồ côi |
| `GET /transcript/health` | Health check nội bộ |
| `GET /module_1/health` | Health check nội bộ |
| `GET /module_2a/health` | Health check nội bộ |

### Endpoints cần giữ nhưng thêm UI

| Endpoint | UI cần thêm |
|---|---|
| `POST /api/projects/{id}/metadata/build` | Metadata Debug Page |
| `GET /api/projects/{id}/metadata` | Metadata Debug Page |
| `GET /api/admin/routing-config/{feature}/cost-estimate` | Cost Calculator |
| `POST /api/style-bibles/{id}/rollback/{version}` | Version History Modal |
| `POST /api/assets/materialize/{provider}/{id}` | Asset Materialize Button |
| `GET /api/admin/credit/ledger` | Credit Ledger Page |
| `GET /api/admin/audit-logs/export/csv` | Export Button |
| `POST /api/batches/{id}/cancel` | Cancel Batch Button |
| `POST /api/projects/{id}/voice/retry/{scene_id}` | Retry Voice Button |
| `POST /api/projects/{id}/timeline/compile` | Compile Timeline Button |
