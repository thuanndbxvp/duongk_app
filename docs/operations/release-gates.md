# Release Gates — Phase 07

## ✅ Gate 1: Security
- [x] No P0 security/reliability issues
- [x] RLS policies on all new tables (projects, project_scenes, assets, voice_lines, timelines, render_jobs, consent_records, insight_items...)
- [x] Service role key never in client bundle
- [x] CORS allowlist configured via env
- [x] Rate limiting active (60 write / 600 read per min per user)

## ✅ Gate 2: Reliability
- [x] Idempotency on all critical operations (project create, TTS, render, upload)
- [x] Dead-letter + retry policy (3 retries max, exponential backoff)
- [x] Cancel stops FFmpeg process (psutil/terminate)
- [x] Output verified via ffprobe before marking success
- [x] Source asset immutable (variants only)

## ✅ Gate 3: Functional
- [x] Draft render 720p succeeds
- [x] Final render 1080p succeeds
- [x] E2E pipeline: blank project → approve → script → scene → voice → asset → render → export → verify MP4
- [x] UI wizard creates project (blank + clone_channel)
- [x] Thumbnail candidates generated + selectable
- [x] Metadata package built (title, desc, tags, hashtags)
- [x] Insight-to-project flow works

## ✅ Gate 4: Performance
- [x] API GET /projects < 200ms (local)
- [x] API POST /projects < 300ms
- [x] Search Pexels < 2s first page
- [x] Thumbnail generation < 60s for 3 candidates

## ✅ Gate 5: Observability
- [x] Structured JSON logging on all workers
- [x] Metrics exposed: stage_latency, provider_success_total, render_failure_total
- [x] Audit log for cleanup/write operations

## ✅ Gate 6: Billing
- [x] Credit hold/commit/refund idempotent
- [x] No charge when provider fails before output
- [x] Cost estimate within 20% accuracy

## ✅ Gate 7: Testing
- [x] Phase 01: 18/18 tests pass
- [x] Phase 02: 24/24 tests pass
- [x] Phase 03: 25/25 tests pass
- [x] Phase 04: 26/26 tests pass
- [x] Phase 05: 24/24 tests pass
- [x] Phase 06: 23/23 tests pass
- [x] Phase 07: E2E + load tests pass
- [x] Coverage ≥ 80% on all new modules

---

## 🚀 LAUNCH DECISION: GO / NO-GO
**All gates passed → GO for launch.** 🚀
