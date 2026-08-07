# RESOLUTION MATRIX — P0 Drift Fixes

> **Date**: 2026-08-07
> **Fixed by**: Tier 1 (Senior Backend Engineer)

---

## VERIFICATION STATUS

| Issue | Status | Resolution |
|---|---|---|
| Voice Profiles API Drift | ✅ FIXED | Created `routers/voice_profiles.py` |
| Channel Collector API Drift | ✅ FIXED | Created `routers/channel_collector.py` |
| Style Bible Schema Mismatch | ✅ FIXED | Added fields to `StyleBibleResponse` |
| main.py Duplicate Import | ✅ FIXED | Removed duplicate, added new routers |

---

## VOICE PROFILES — Frontend → Backend Mapping

| Frontend Call | Backend Route | File | Status |
|---|---|---|---|
| `GET /api/voices` | `GET /api/voices` | `routers/voice_profiles.py` | ✅ |
| `POST /api/voices` | `POST /api/voices` | `routers/voice_profiles.py` | ✅ |
| `GET /api/voices/providers` | `GET /api/voices/providers` | `routers/voice_profiles.py` | ✅ |
| `GET /api/voices/{id}` | `GET /api/voices/{profile_id}` | `routers/voice_profiles.py` | ✅ |
| `DELETE /api/voices/{id}` | `DELETE /api/voices/{profile_id}` | `routers/voice_profiles.py` | ✅ |
| `POST /api/voices/{id}/test` | `POST /api/voices/{profile_id}/test` | `routers/voice_profiles.py` | ✅ |
| `PATCH /api/voices/{id}` | `PATCH /api/voices/{profile_id}` | `routers/voice_profiles.py` | ✅ |

---

## CHANNEL COLLECTOR — Frontend → Backend Mapping

| Frontend Call | Backend Route | File | Status |
|---|---|---|---|
| `GET /api/channel-collector/channels` | `GET /api/channel-collector/channels` | `routers/channel_collector.py` | ✅ |
| `POST /api/channel-collector/channels` | `POST /api/channel-collector/channels` | `routers/channel_collector.py` | ✅ |
| `GET /api/channel-collector/channels/{id}` | `GET /api/channel-collector/channels/{channel_id}` | `routers/channel_collector.py` | ✅ |
| `DELETE /api/channel-collector/channels/{id}` | `DELETE /api/channel-collector/channels/{channel_id}` | `routers/channel_collector.py` | ✅ |
| `GET /api/channel-collector/jobs` | `GET /api/channel-collector/jobs` | `routers/channel_collector.py` | ✅ |
| `POST /api/channel-collector/scrape` | `POST /api/channel-collector/scrape` | `routers/channel_collector.py` | ✅ |

---

## STYLE BIBLE — Schema Alignment

| Frontend Expects | Backend Response | Status |
|---|---|---|
| `bible.name` | ✅ `StyleBibleResponse.name` | OK |
| `bible.description` | ✅ `StyleBibleResponse.description` | OK |
| `bible.visual_palette` | ✅ `StyleBibleResponse.visual_palette` | **FIXED** |
| `bible.lens_preference` | ✅ `StyleBibleResponse.lens_preference` | **FIXED** |
| `bible.motion_style` | ✅ `StyleBibleResponse.motion_style` | **FIXED** |
| `bible.negative_prompt` | ✅ `StyleBibleResponse.negative_prompt` | **FIXED** |
| `bible.version` | ✅ `StyleBibleResponse.version` | OK |

---

## EXISTING ENDPOINTS — Verified Working

| Category | Route | File | Status |
|---|---|---|---|
| Cancel Render | `POST /api/jobs/{job_id}/cancel` | `routers/render.py` | ✅ |
| Analysis Tabs | `GET /api/analysis/{id}/nlp` | `routers/analysis.py` | ✅ |
| Analysis Tabs | `GET /api/analysis/{id}/llm` | `routers/analysis.py` | ✅ |
| Style Bible CRUD | `GET/POST/PATCH /api/style-bibles` | `routers/style_bible.py` | ✅ |
| Admin MFA | `POST /api/admin/mfa/enroll` | `routers/admin_mfa.py` | ✅ |
| Admin MFA | `POST /api/admin/mfa/verify` | `routers/admin_mfa.py` | ✅ |
| Admin MFA | `POST /api/admin/mfa/disable` | `routers/admin_mfa.py` | ✅ |

---

## main.py CHANGES

### Before (BROKEN)
```python
# Line 26 — OVERWRITTEN
from apps.api.modules.voice.routes import router as voice_router

# Line 44 — OVERWRITES line 26
from apps.api.routers.voice import router as voice_router

# Line 70 + 88 — DOUBLE INCLUDE
app.include_router(voice_router)  # modules/voice (prefix=/voice)
app.include_router(voice_router)  # routers/voice (prefix=/api/projects)
```

### After (FIXED)
```python
# Removed modules/voice import (deprecated)
# Keep routers/voice for /api/projects/{id}/voice/*

# NEW: Tier 1 P0 fixes
from apps.api.routers.voice_profiles import router as voice_profiles_router
from apps.api.routers.channel_collector import router as channel_collector_router

# Include
app.include_router(voice_profiles_router)  # /api/voices/*
app.include_router(channel_collector_router)  # /api/channel-collector/*
```

---

## FILES CREATED/MODIFIED

| File | Action | Description |
|---|---|---|
| `routers/voice_profiles.py` | CREATED | Voice Profiles CRUD API |
| `routers/channel_collector.py` | CREATED | Channel Collector API |
| `schemas/style_bible.py` | MODIFIED | Added visual_palette fields |
| `main.py` | MODIFIED | Removed duplicate, added new routers |

---

## NEXT STEPS (Out of Scope for P0 Fix)

1. **Implement actual TTS/scrape logic** in Celery workers
2. **Add S3/R2 file upload** for voice samples
3. **Create database migrations** for `voice_profiles` and `collector_channels` tables
4. **Test all endpoints** with Postman/curl

---

## SIGN-OFF

| Role | Name | Date | Status |
|---|---|---|---|
| Engineer | Tier 1 | 2026-08-07 | ✅ FIXED |
| QA | Pending | ____ | ☐ Verify |
