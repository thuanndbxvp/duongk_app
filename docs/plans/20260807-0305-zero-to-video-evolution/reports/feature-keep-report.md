# Báo cáo giữ lại các tính năng “nghiên cứu kênh đối thủ – comment – giọng văn”

> Ngày: 2026-08-07 03:20 (UTC+7)
> Ngữ cảnh: Bạn thích các cụm tính năng Tool 1 + Tool 11 của Ai86Studio (channel profile, comment intelligence, voice style) và muốn biết chúng có được giữ lại trong roadmap appDK không.
> Trả lời ngắn: **Có. Toàn bộ 3 cụm đều nằm trong Borrow trong `reports/feature-mix.md` và đã có phase triển khai chi tiết.**

## Cụm bạn hỏi trong Ai86Studio

Theo `D:\SwapCode\Nova\Ai86Studio\docs\PIPELINE-INSIGHTS-FOR-NEW-PROJECT.md`:

```text
§ 2 Tool 1 + Tool 11 — Biến "kênh" thành vòng lặp học nội dung
  2.1 Channel Profile — versioned preset
  2.2 Comment Intelligence — comment gốc → cluster → insight
  2.3 Module mapping
  2.4 Comment không phải output cuối
  2.5 Insight schema — phải có evidence

§ 3 Lên ý tưởng + viết kịch bản — thiết kế như một compiler
  3.3 Stage 3 — Script theo voice profile của kênh
        Câu ngắn/dài, mật độ thông tin, nhịp kể,
        mức độ cảm xúc, cách mở đầu, CTA…
```

## Mapping 1‑1 sang appDK

| Tính năng Ai86Studio (bạn thích) | Phase trong appDK | Nhóm theo feature-mix | Vị trí cụ thể đã viết |
|---|---|---|---|
| Channel Profile dạng versioned preset (audience, editorial, brand, production, distribution) | Phase 01 + Phase 08 | Borrow | `phase-08-channel-intelligence.md` mục 4–5 |
| Comment Intelligence: import → thu thập → chuẩn hoá → cluster → insight có evidence | Phase 06 + Phase 08 | Borrow | `phase-08-channel-intelligence.md` mục 4–7 |
| Insight schema có evidence, confidence, opportunity | Phase 08 | Borrow | `phase-08-channel-intelligence.md` mục 5 (bảng `insight_items`) |
| Không bịa insight ngoài comment gốc (evidence-backed) | Phase 08 | Borrow (nguyên tắc) | `phase-08-channel-intelligence.md` mục 7, 11 |
| RAG inject channel profile vào script | Phase 08 | Borrow | `phase-08-channel-intelligence.md` mục 7.6 |
| Script theo voice profile (câu ngắn/dài, nhịp, cảm xúc, mở đầu, CTA) | Phase 01 + Phase 08 | Borrow | `phase-01-project-foundation.md` mục Architecture + `phase-08` mục 7.6 |
| Channel profile version rollback | Phase 08 | Borrow | `phase-08-channel-intelligence.md` mục 5 |
| Output của comment intel không chỉ là comment mà là opportunity → brief/script | Phase 08 | Borrow | `phase-08-channel-intelligence.md` mục 4 và 7.4 |
| Suggestion rule "không gọi AI generation ngay khi tạo script — phải qua approval gate" | Phase 01 + Phase 04 | Borrow | `phase-01-project-foundation.md` mục Requirements + `phase-04-ffmpeg-render-export.md` mục Draft strategy |

## Trích đoạn chứng minh trong tài liệu

### 1) Channel Profile versioned (Borrow)

Trong `D:\appDK\docs\plans\20260807-0305-zero-to-video-evolution\phase-08-channel-intelligence.md`:

```text
## 4. Architecture

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
```

```sql
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
  ...
  is_active BOOLEAN NOT NULL DEFAULT false,
  UNIQUE (assistant_id, version)
);
```

### 2) Comment Intelligence + Evidence-backed insight (Borrow)

Cùng phase 08:

```text
### 7.2 Provider abstraction
1. Triển khai `CommentsProvider` với `fetch(video_ids, batch_size=100, page_token=...)` ...
2. Triển khai `YouTubeDataAPIProvider` (primary) làm bằng API key ở `api_provider_keys`.
3. Thêm rate-limit guard: 1000 units/phút mặc định (theo quota YouTube).

### 7.4 Clustering & insights
2. `calculate_opportunity_score()`:
   - `0.4 * normalize(gap_score) + 0.3 * normalize(evidence_strength)
      + 0.2 * freshness_factor + 0.1 * confidence`.
```

```sql
CREATE TABLE insight_items (
  ...
  kind TEXT NOT NULL,                 -- 'comment_theme' | 'performance_pattern' | ...
  evidence_ids JSONB NOT NULL,        -- [{source, ref_id}]
  evidence_strength FLOAT,
  confidence FLOAT,
  freshness_at TIMESTAMPTZ DEFAULT NOW(),
  status TEXT NOT NULL DEFAULT 'pending'
);
```

### 3) Giọng văn / voice profile (Borrow)

Trong `phase-01-project-foundation.md`:

```text
Creative brief gồm topic, audience, language, duration, aspect ratio,
tone, visual style, voice profile, music mood.
```

Trong `phase-08-channel-intelligence.md`:

```text
### 7.6 RAG integration
1. rag_service.build_context():
   - Thêm block channel profile version (editorial + forbidden claims).
   - Chèn evidence snippet khi source_insight_ids được cung cấp.
   - Tag rõ ràng [evidence] ... [evidence_end].
```

## Phần appDK đang có sẵn (Keep)

Không phải mọi thứ đều xây mới. appDK đã có DNA + RAG và credit system:

- `channel_assistants` đã có chỗ cho audience/voice/style.
- `channel_deep_analysis` đã có persona, hook, structure, mimic_rules, emotional_signature, signature_phrases.
- `dna_chunks` đã là vector 1024d phục vụ RAG.
- `transcripts` đã có sẵn từ Provider transcript.
- `IdeaGenerator` đã có gap_score.
- `script_generate.py` đã có RAG + Anti-Slop.
- `voice_profiles` đã có sẵn bảng.

AppDK chỉ thiếu 3 phần để hoàn thiện 3 cụm mà bạn thích:

1. **Versioned channel profile** — thêm bảng + API + Rollback.
2. **Comment ingestion pipeline** — provider abstraction + Celery job + UI approve insight.
3. **Insight → idea → project seed** — opportunity_score + brief seed từ insight.

Tất cả 3 phần này đã có trong Phase 08.

## Bị loại có chọn lọc (Skip)

Có 1 cụm phụ của Ai86Studio bị loại vì rủi ro, không phải vì bạn không thích:

- Sniff session token / decrypt cookie / CAPTCHA automation → Skip (xem `feature-mix.md`).
- Lý do: vi phạm điều khoản dịch vụ Google, dễ gãy, không duy trì được dài hạn.

Bù lại, appDK vẫn có thể làm comment intelligence qua API chính thức. Vì vậy tính năng đối thủ + comment vẫn được giữ, chỉ thay đường lấy dữ liệu.

## Kết luận

- **Channel profile versioned**: giữ (Borrow, versioned preset có rollback).
- **Comment intelligence**: giữ (Borrow, qua API chính thức + evidence chip trong UI).
- **Insight có evidence/confidence/opportunity**: giữ (Borrow, bảng `insight_items` + `opportunity_score`).
- **Script theo voice profile của kênh**: giữ (Borrow, channel profile + voice direction trong brief + RAG có evidence).
- **Nghiên cứu kênh đối thủ + comment**: giữ (Borrow, comment + transcript qua API chính thức).
- **Giọng văn khi viết script**: giữ (Borrow, voice profile + style bible + persona từ DNA + script mở rộng theo Phase 01).

Tất cả mục bạn thích đều có trong route map. Không có mục nào bị drop.

## Gợi ý bước tiếp theo (nếu bạn duyệt)

1. Triển khai Phase 01 (Project + Brief) trước vì là nền.
2. Triển khai Phase 02 (Scene + Asset) để có creative brief → scene plan.
3. Triển khai Phase 03 (Voice + Timeline) để duration thật + SRT.
4. Triển khai Phase 04 (FFmpeg Render) để có MP4 + draft.
5. Triển khai Phase 05 (AI Media + Thumbnail) để nâng chất asset.
6. Triển khai Phase 06 + Phase 08 (Channel Intelligence + Feedback Loop) để đóng vòng học nội dung.

Phase 06 + 08 chính là nơi 3 tính năng bạn thích từ Ai86Studio "đóng đinh" trong appDK.
