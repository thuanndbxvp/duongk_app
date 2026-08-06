# Phase 08 — Channel Intelligence Feedback Loop

> Ngày: 2026-08-07 03:17 (UTC+7)
> Phạm vi: Phase mở rộng dựa trên Phase 06, chi tiết hóa cách mượn Tool 1 + Tool 11 của Ai86Studio vào nền channel DNA + RAG hiện có của appDK.
> Tuân thủ bảng mix tại `reports/feature-mix.md` (Keep RAG + DNA, Borrow comment intelligence qua API chính thức, Skip scraping qua session).
> Vị trí: `D:\appDK\docs\plans\20260807-0305-zero-to-video-evolution\phase-08-channel-intelligence.md`

## 1. Context

### Baseline đã có

- `channel_assistants` — metadata của kênh.
- `channel_deep_analysis` — 14 outputs (persona, hook, structure, mimic_rules, emotional_signature, signature_phrases, insights...).
- `dna_chunks` — vector 1024d (Cohere) phục vụ RAG.
- `transcripts` — transcript YouTube.
- `tasks/analysis_task.py` — pipeline phân tích kênh.
- `tasks/script_generate.py` — sinh script dùng RAG.
- `services/rag_service.py` — RAG retrieval + prompt builder.
- Admin plan `docs/plans/admin_panel_plan.md` đã bố trí `service_routing_config` và `api_provider_keys` cho `llm_text`, `embedding`, `transcript_extract`.

### Mục tiêu của phase này

1. Biến DNA + RAG thành hệ thống **đề xuất có bằng chứng** (evidence-backed) và đóng vòng feedback với insight từ video/comment thực.
2. Cho user duyệt insight/idea trước khi đổ vào brief của project mới.
3. Tự động cập nhật `channel_assistants` sau mỗi video được đăng hoặc sau khi user đánh dấu "thực hiện insight X".
4. Bổ sung channel profile versioned (audience, editorial rules, voice, visual style, thumbnail rules, forbidden claims), dùng cho cả blank project khi user chọn profile.

### Không thuộc phạm vi

- Không xây scraper qua session/token (đã loại theo `feature-mix.md`).
- Không gọi endpoint riêng tư không có API hỗ trợ.
- Không tự động đăng video lên YouTube; chỉ gợi ý metadata và cho user copy.

## 2. Key insights

- Insight AI **phải đính kèm evidence IDs** (comment_id, transcript_segment_id, chunk_id) để truy ngược. Không có evidence → insight không được persist.
- Mỗi channel có `last_evidence_collected_at`. Cluster/insight cũ phải giảm trọng số khi stale; user phải thấy freshness/confidence.
- Topic cluster hiện dùng HDBSCAN trên TF-IDF (xem `idea_generator.py`). Có thể thử UMAP + HDBSCAN khi kích thước lớn, nhưng vẫn giữ HDBSCAN mặc định để tránh đổi public API quá sớm.
- `channel_deep_analysis.persona` và `mimic_rules` đã có input cho script. Mở rộng thêm block `*_version INT` để versioning và `*_evidence JSONB` để chuyển insight thành evidence-backed.
- `dna_chunks` đang lưu embedding; mở rộng thêm `source_type` (transcript / comment / insight) để RAG biết weight khi truy xuất.

## 3. Requirements

### Functional

- Channel profile versioned:
  - `audience`, `editorial_rules`, `voice_profile_id`, `visual_style`, `thumbnail_rules`, `forbidden_claims/phrases`, `default_duration_minutes`, `default_aspect_ratio`.
  - Mỗi lần save tạo version mới (rollback được).
- Import video ID/URL qua API chính thức:
  - Transcript bằng `transcript_extract` provider (đã có trong routing).
  - Comments bằng provider đã được audit. Lưu comment_id, parent_id, like_count, published_at, fetched_at, lang.
- Cluster comment theo embedding/HBDSCAN/DBSCAN cùng heuristic ngôn ngữ:
  - Mỗi cluster có `topic_label`, `representative_comment_ids[]`, `size`, `sentiment_score`.
- Sinh insight có evidence:
  - Mỗi insight lưu `evidence_ids[]`, `evidence_type` (transcript | comment | trend | performance), `confidence`, `freshness_at`.
- Insight → idea candidate:
  - Mỗi idea nối `source_insight_id` và có `opportunity_score = f(gap_score, evidence_strength, freshness)`.
- Project nguồn (`project_id`):
  - Một project có thể lấy insight từ channel profile làm brief seed.
- Feedback sau khi user xuất bản:
  - User tick "đã đăng video N" → job cập nhật `channel_assistants.last_published_at`, ghi `published_video_refs` và `insight_outcomes` (idea_id → engagement snapshot).
- Comment intelligence có rate-limit/provider quota/checksum để tránh trùng.

### Non-functional

- RLS theo `user_id` cho mọi bảng mới.
- Mỗi batch ingestion có batch_id, thời gian chạy, số comment ingest, số comment lỗi.
- Job có progress thật (`ingest_step`, `cluster_step`, `insight_step`).
- Tất cả insight phải có evidence trước khi expose cho UI.
- Quota guard: max 5000 comments/channel/ngày; cap by tier.
- Provider fallback chain cho transcript + comment theo `service_routing_config`.

## 4. Architecture

```text
[YouTube Data API official] → transcript provider
                            → comment provider
        ↓
[Celery: ingest_comments]  → comment_normalized table
        ↓
[Celery: cluster_comments] → comment_clusters + cluster_samples
        ↓
[Celery: build_insights]   → insights (with evidence_ids)
        ↓
[IdeaGenerator v2]         → idea với source_insight_id + opportunity_score
        ↓
[User approve]             → brief seed → projects table (Phase 01)
        ↓
[After publish reference]  → channel_assistants updated + insight_outcomes
```

### Adapter layer

```text
class TranscriptProvider:
    fetch(video_id) -> TranscriptSegments

class CommentProvider:
    fetch(video_id, page_token=None) -> list[CommentRow]

class TrendsProvider:           # Google Trends / SerpAPI
    topic_score(topic) -> float
```

Đây là extension của `service_routing_config` đã định nghĩa `transcript_extract`. Phase 08 thêm:
- `comment_intel` (YouTube Data API + optional backup).
- `topic_cluster` (HDBSCAN self-host, không tốn cost).
- `trend_provider` (Google Trends / SerpAPI; feature flag).

### RAG integration

`build_context()` trong `rag_service.py` được nâng cấp:

```text
1. Lấy channel profile version (visual + editorial + voice + forbidden).
2. RAG top_k trên `dna_chunks` (giảm top_k nếu có persona/mimic_rules version mới).
3. Nếu brief có `source_insight_ids`, chèn evidence snippet vào prompt với tag rõ ràng.
4. Cuối prompt: list forbidden claims để LLM tránh.
```

`dna_chunks` thêm cột `source_type` để ưu tiên.

## 5. Data model

Migration `0027_channel_intel.sql`:

```sql
-- Versioned channel profile
CREATE TABLE channel_profile_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assistant_id UUID NOT NULL REFERENCES channel_assistants(id) ON DELETE CASCADE,
  version INT NOT NULL,
  audience TEXT,
  editorial_rules JSONB NOT NULL DEFAULT '{}',
  voice_profile_id UUID,
  visual_style JSONB DEFAULT '{}',
  thumbnail_rules JSONB DEFAULT '{}',
  forbidden_claims JSONB DEFAULT '[]',
  default_duration_minutes INT,
  default_aspect_ratio TEXT,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  is_active BOOLEAN NOT NULL DEFAULT false,
  UNIQUE (assistant_id, version)
);

CREATE INDEX idx_cpv_active ON channel_profile_versions(assistant_id) WHERE is_active;

-- Episode references (referenced videos / published)
CREATE TABLE channel_references (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assistant_id UUID NOT NULL REFERENCES channel_assistants(id) ON DELETE CASCADE,
  source TEXT NOT NULL,                  -- 'youtube_video_id' | 'manual_url' | 'internal'
  external_id TEXT,                      -- video_id nếu có
  url TEXT,
  kind TEXT NOT NULL,                    -- 'reference' | 'published'
  title TEXT,
  published_at TIMESTAMPTZ,
  ingested_at TIMESTAMPTZ DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_ref_assistant ON channel_references(assistant_id, kind);

-- Comments ingestion
CREATE TABLE comment_clusters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assistant_id UUID NOT NULL REFERENCES channel_assistants(id) ON DELETE CASCADE,
  cluster_label TEXT,
  size INT,
  sentiment_score FLOAT,
  representative_comment_ids JSONB,        -- text[]
  algorithm TEXT,                         -- 'hdbscan' | 'umap_hdbscan'
  freshness_at TIMESTAMPTZ DEFAULT NOW(),
  ingest_batch_id UUID
);

CREATE TABLE insight_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assistant_id UUID NOT NULL REFERENCES channel_assistants(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,                     -- 'comment_theme' | 'performance_pattern' | 'audience_question' | 'content_gap'
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  evidence_ids JSONB NOT NULL,            -- [{source, ref_id}]
  evidence_strength FLOAT,
  confidence FLOAT,
  freshness_at TIMESTAMPTZ DEFAULT NOW(),
  status TEXT NOT NULL DEFAULT 'pending', -- 'pending' | 'approved' | 'rejected' | 'archived'
  reviewer_id UUID REFERENCES users(id),
  reviewed_at TIMESTAMPTZ
);

CREATE INDEX idx_insight_assistant ON insight_items(assistant_id, status, freshness_at DESC);

-- Link from generated_ideas to insight source
ALTER TABLE generated_ideas
  ADD COLUMN source_insight_id UUID REFERENCES insight_items(id),
  ADD COLUMN opportunity_score FLOAT,
  ADD COLUMN evidence_ids JSONB;

-- Outcome tracking
CREATE TABLE insight_outcomes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  insight_id UUID REFERENCES insight_items(id) ON DELETE CASCADE,
  project_id UUID,                        -- FK to projects (Phase 01)
  idea_id UUID,
  published_at TIMESTAMPTZ,
  engagement_snapshot JSONB               -- snapshot manual / API sau khi đăng
);

-- Provider call audit
CREATE TABLE comment_ingest_batches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assistant_id UUID NOT NULL REFERENCES channel_assistants(id),
  started_at TIMESTAMPTZ DEFAULT NOW(),
  finished_at TIMESTAMPTZ,
  total_comments INT,
  failed_comments INT,
  provider TEXT,
  status TEXT
);

CREATE INDEX idx_cib_assistant ON comment_ingest_batches(assistant_id, started_at DESC);

-- RLS
ALTER TABLE channel_profile_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE comment_clusters ENABLE ROW LEVEL SECURITY;
ALTER TABLE insight_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE insight_outcomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE comment_ingest_batches ENABLE ROW LEVEL SECURITY;

-- Reuse existing helper functions in appDK to enforce RLS via channel_assistants.user_id
```

## 6. Related code files

### Modify

- `apps/worker/services/idea_generator.py` — bổ sung `cluster_comments()` và `opportunity_score()`.
- `apps/worker/services/rag_service.py` — `build_context()` đọc channel profile version + chèn evidence.
- `apps/api/routers/analysis.py` — endpoint lấy/approve insight.
- `apps/api/routers/ideas.py` — trả về `source_insight_id` và `opportunity_score` (Phase 06 đã mô tả).
- `apps/web/app/(dashboard)/dashboard/page.tsx` — card "Insights" và "Reference videos".
- `apps/web/app/(dashboard)/assistants/[id]/page.tsx` — tab "Intelligence" (insights, channel references, comment clusters).

### Create

- `apps/api/routers/channel_intel.py` — admin/user endpoints cho profile versions, references, insights.
- `apps/api/schemas/channel_intel.py` — Pydantic schemas.
- `apps/worker/services/comments_provider.py` — provider abstraction + multiple providers.
- `apps/worker/services/insights_service.py` — build cluster + insight + scoring.
- `apps/worker/tasks/ingest_comments.py` — batch ingestion qua provider chính thức.
- `apps/worker/tasks/build_insights.py` — cluster + insight jobs.
- `apps/web/components/insight-card.tsx` — UI render insight có evidence chip.
- `apps/web/app/(dashboard)/assistants/[id]/insights/page.tsx`.
- `apps/web/app/(dashboard)/assistants/[id]/references/page.tsx`.

### Không tạo

- Không scraper, không decrypt cookie, không reCAPTCHA automation. Bỏ qua theo `feature-mix.md`.

## 7. Implementation steps

### 7.1 Routing & schema

1. Mở rộng `service_routing_config` (file admin plan đã có) thêm `comment_intel`, `topic_cluster`, `trend_provider`. Seed `enabled_providers` cho `comment_intel=youtube_data_api` + backup `serply` nếu có.
2. Chạy migration `0027_channel_intel.sql`.
3. Bổ sung RLS policy thông qua hàm helper `get_owned_assistant_ids()`.

### 7.2 Provider abstraction

1. Triển khai `CommentsProvider` với `fetch(video_ids, batch_size=100, page_token=...)` trả về `list[CommentRow]`.
2. Triển khai `YouTubeDataAPIProvider` (primary) làm bằng API key ở `api_provider_keys`.
3. Thêm rate-limit guard: 1000 units/phút mặc định (theo quota YouTube).
4. Viết unit test cho pagination, retry 5xx, exhausted quota.
5. Mock provider cho test: deterministic comment set.

### 7.3 Ingestion worker

1. Tạo `tasks/ingest_comments.py` Celery task, idempotency key `(assistant_id, batch_id)`.
2. Logic:
   - Lấy `channel_references` chưa ingest.
   - Với mỗi reference, fetch comments theo page.
   - Lưu `comment_normalized` (không bắt buộc tạo bảng riêng nếu chỉ dùng tạm; nếu muốn audit có thể chuyển sang bảng `comment_normalized` nhưng giữ schema cho task này).
   - Cập nhật `comment_ingest_batches.status`.
3. Tích hợp `ProgressTracker` với `ingest_step`, `cluster_step`, `insight_step`.

### 7.4 Clustering & insights

1. `tasks/build_insights.py`:
   - Step 1 — `cluster_comments()` dùng HDBSCAN trên embedding Cohere (đã có) hoặc TF-IDF + language hint.
   - Step 2 — `build_insight_from_cluster()` gọi LLM theo `select_llm_provider()` (đã có ở `script_generate.py`).
   - Bước gọi LLM phải yêu cầu JSON với trường `evidence_comment_ids`, reject nếu thiếu.
   - Tạo `insight_items` với `status='pending'`.
2. `calculate_opportunity_score()`:
   - `0.4 * normalize(gap_score) + 0.3 * normalize(evidence_strength) + 0.2 * freshness_factor + 0.1 * confidence`.
3. Tạo `idea v2` từ insight đã approve:
   - Row mới trong `generated_ideas` với `source_insight_id`, `opportunity_score`, `evidence_ids`.

### 7.5 UI

1. `insight-card.tsx`:
   - Hiển thị title, body, evidence chip (click mở drawer có snippet + link).
   - Action: approve / reject / "Tạo project từ insight".
2. Trang `insights/page.tsx`:
   - Filter theo `kind`, `status`, freshness.
   - Bulk approve.
3. Trang `references/page.tsx`:
   - Quản lý reference videos, nút "ingest comments".
4. Từ idea list, cho phép "Biến thành project" → tạo `projects` row ở Phase 01 với brief seed từ insight.

### 7.6 RAG integration

1. `rag_service.build_context()`:
   - Thêm block channel profile version (editorial + forbidden claims).
   - Chèn evidence snippet khi `source_insight_ids` được cung cấp.
   - Tag rõ ràng `[evidence] ... [evidence_end]`.
2. Test: cùng script + có/không evidence → sinh output khác biệt, không trộn vào nhau.

### 7.7 Feedback loop

1. Sau khi user đánh dấu "đã đăng video":
   - Cập nhật `channel_assistants.last_published_at`, ghi `insight_outcomes.published_at`.
   - Lên lịch worker snapshot engagement (chỉ sau khi có user cung cấp URL/ID hợp lệ qua API).
2. Sau 30 ngày từ lần ingest cuối của cluster, đánh `stale` nếu `freshness_at < NOW() - INTERVAL '30 days'`.

### 7.8 Tests

- Unit:
  - Clusterer deterministic với seed comments.
  - Insights reject khi thiếu evidence_ids.
  - Scoring qua các ngưỡng biên.
  - Provider pagination và retry.
- Integration:
  - Ingest → cluster → insight → idea → project seed (Phase 01).
  - RLS test: user A không đọc insight của user B.
- E2E:
  - User mở assistant, ingest 1 video test, approve insight, tạo project, brief seed hoạt động.

## 8. Acceptance criteria

- User thấy insight kèm evidence (comment snippet / transcript segment) trong UI.
- Insight không có evidence bị reject bởi schema validation.
- Approve insight → tạo được idea và project từ insight, có `source_insight_id` lưu xuyên suốt.
- Channel profile version tạo mới không xóa bản cũ; rollback được.
- RAG script dùng evidence snippet rõ ràng; prompt không bị prompt-injection từ comment body (escape các pattern `[evidence]` nội dung).
- Provider gọi đúng quota, idempotency, retry an toàn.
- Ingest 1000 comment chạy không quá tải worker (chunks + throttled).

## 9. Risks & mitigations

| Rủi ro | Chiến lược giảm thiểu |
|---|---|
| Dữ liệu comment có chứa prompt-injection | Escape/sanitize; tách content thô và trường "preview"; whitelist response format |
| Comment sentiment / cluster phụ thuộc ngôn ngữ | Dùng language detection; fallback cụm theo heuristic |
| Provider quota cạn kiệt | Tôn trọng `enabled_providers`; trả lỗi rõ + retry sau; hiển thị thời gian nhập lại |
| Insight noise | Đặt ngưỡng `confidence`/`evidence_strength`; admin có thể ẩn cluster không đạt ngưỡng |
| Lộ PII từ comment | Mask email/phone trước khi lưu; redact khi hiển thị; RLS đảm bảo chỉ user sở hữu xem được |
| Stale insight ảnh hưởng RAG | `freshness_factor` giảm weight theo ngày; auto-archive sau ngưỡng |
| Scraping risk từ developer copy code cũ | Mọi provider code chỉ dùng API; không thêm script "browser session" |
| Cost bất ngờ từ LLM clustering | Dùng `llm_text` routing có cost gate; sample cluster lớn để giảm call |

## 10. Security considerations

- Provider key lưu trong `api_provider_keys` (Supabase Vault) — không hardcode.
- Endpoint admin đã chuẩn trong admin plan `docs/plans/admin_panel_plan.md`. Phase 08 dùng `require_admin` cho cluster re-run + tuning insight weights.
- Audit log khi admin re-cluster toàn channel.
- User content policy: chặn nội dung vi phạm ngay khi normalize comment body (URL, email, phone, hate terms).
- Không ghi comment body gốc vào log chỉ ghi comment_id + hash.

## 11. Definition of done

- Migration `0027_channel_intel.sql` chạy thành công ở cả staging và production.
- Insight approve → tạo project end-to-end.
- RAG context có evidence chip trong script prompt (verify qua log và unit test).
- Tất cả tests ở mục 7.8 xanh.
- Không có endpoint mới nào dùng browser session, token sniff hoặc cookie decrypt.

## 12. Liên kết

- `plan.md` — tổng quan 7 phase.
- `phase-06-feedback-and-batch.md` — phase tổng thể.
- `phase-01-project-foundation.md` — entity `projects` mà insight sẽ seed.
- `phase-04-ffmpeg-render-export.md` — render dùng output của phase này.
- `phase-05-ai-media-thumbnail.md` — AI media cho scene, scene khai thác insight làm visual gợi ý.
- `reports/feature-mix.md` — bảng mix Keep/Borrow/Skip.
- `docs/plans/admin_panel_plan.md` — provider key, routing config, audit log, telemetry.
