# Báo cáo khảo sát baseline appDK

## Phạm vi đã đọc

- `apps/web/app/page.tsx`
- `apps/web/app/(dashboard)/projects/new/page.tsx`
- `apps/web/app/(dashboard)/scripts/[id]/page.tsx`
- `apps/web/components/scene-timeline.tsx`
- `apps/worker/services/idea_generator.py`
- `apps/worker/tasks/idea_generate.py`
- `apps/worker/tasks/script_generate.py`
- `apps/worker/services/scene_breaker.py`
- `apps/worker/tasks/scene_breakdown.py`
- `apps/worker/progress_tracker.py`
- `apps/omnivoice/app/main.py`
- `supabase/migrations/0002_jobs.sql`
- `supabase/migrations/0018_scripts.sql`
- `docker-compose.yml`

## Đã có

- Next.js + FastAPI + Celery + Redis + Supabase.
- Channel analysis và channel DNA/RAG.
- Idea clustering, gap score, confidence, opportunity description.
- Script generation, JSON response, Anti-Slop validation, cost tracking.
- Scene segmentation theo WPM.
- B-roll keyword extraction và VN→EN translation.
- OmniVoice TTS với serialized inference và timeout.
- Durable `jobs` row, sub-progress và credit hold/commit/refund.
- RLS, tests, monitoring và provider routing foundation.

## Chưa có

- Blank project onboarding.
- Project root độc lập với channel assistant.
- Scene contract production-grade.
- Asset library/upload/stock materialization.
- AI image/video generation adapter.
- Voice line gắn từng scene và actual duration feedback.
- Subtitle track/timeline version.
- FFmpeg composition/render/export.
- Preview render/cancel thực.
- Background music/SFX/ducking.
- Thumbnail generation.
- Final SEO/export package.

## Đánh giá

AppDK đã có khoảng 60–80% nền tảng content intelligence nhưng gần 0% production/render core. Vì vậy không nên viết lại app; nên mở rộng theo vertical slice: blank project → scene → asset → voice → draft render → export.

## Ghi chú kỹ thuật

- `idea_generate.py` hiện hardcode `trending_score = 50.0`; cần provider abstraction trước khi dùng gap score làm quyết định sản xuất.
- `script_generate.py` fallback provider hiện có nhánh placeholder; cần routing/fallback thực sự cho production.
- `scene_breaker.py` chia theo paragraph và WPM; duration cuối phải lấy từ audio thật.
- `scripts/[id]/page.tsx` đang dùng controlled textarea nhưng chưa có `onChange`/save flow.
- `SceneTimeline` hiện là scene list, chưa phải timeline editor.
- `generated_scripts.scenes` JSONB đủ cho MVP nhưng nên chuẩn hóa thành `project_scenes` khi asset/timeline phát triển.
