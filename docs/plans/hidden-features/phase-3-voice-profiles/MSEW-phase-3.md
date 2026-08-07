# Phase 3 — MSEW

## Milestones

| Step | Action | Skills |
|---|---|---|
| 1 | Verify 8 voice endpoints exist + test với curl | `debugging`, `code-review` |
| 2 | Implement /providers endpoint nếu chưa có | `backend-development` |
| 3 | Build `<VoiceCard>` component | `frontend-development`, `ui-styling` |
| 4 | Build list page `/voice-profiles` | `frontend-development` |
| 5 | Build `<VoiceForm>` component | `frontend-development`, `ui-styling` |
| 6 | Build create page `/voice-profiles/new` | `frontend-development` |
| 7 | Build `<VoiceDetailActions>` component | `frontend-development` |
| 8 | Build detail page `/voice-profiles/[id]` | `frontend-development` |
| 9 | Wire navigation (sidebar link) | `frontend-development` |
| 10 | Tests: component + integration + E2E | `testing-protocol` |
| 11 | Self-review + Tier 1 review | `code-review` |

## Skills routing

| Task | Primary | Secondary |
|---|---|---|
| Backend /providers | `backend-development` | — |
| Component builders | `frontend-development` | `ui-styling` |
| Form handling | `frontend-development` | `ui-styling` |
| Tests | `testing-protocol` | — |

## Evidence

```bash
# Verify endpoints
curl -X GET "http://localhost:8000/api/voices" -H "Authorization: Bearer ${TOKEN}"
curl -X GET "http://localhost:8000/api/voices/providers" -H "Authorization: Bearer ${TOKEN}"
curl -X POST "http://localhost:8000/api/voices" -H "Authorization: Bearer ${TOKEN}" -F "name=test" -F "provider_id=omnivoice" -F "language=vi-VN" -F "gender=male" -F "sample=@/path/to/audio.mp3"
curl -X POST "http://localhost:8000/api/voices/{id}/test" -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" -d '{"text":"hello"}'

# Tests
pytest tests/web/components/test_voice_form.tsx -v
pytest tests/api/test_voices_endpoints.py -v
bash scripts/run_e2e_local.sh
```

## Warnings

### 🟡 Gotcha 1: Multipart upload = Next.js 13+ config

Next.js 13+ mặc định parse body ở server. Multipart uploads cần custom config.

**Fix**: Client-side dùng `FormData` thì OK, không cần config. Server-side route nếu dùng Next.js API route thì cần `export const dynamic = "force-dynamic"` và `export const runtime = "nodejs"`.

### 🟡 Gotcha 2: Audio file validation phía client chưa đủ

Client validation (file type, size) dễ bypass. Backend phải validate lại.

**Fix**: Backend đã validate (existing). Tier 2 chỉ cần client-side hint UX.

### 🟡 Gotcha 3: Provider capabilities thay đổi

Mỗi lần backend team add provider mới, capabilities list thay đổi.

**Fix**: Frontend fetch dynamic từ `/api/voices/providers`. Không hardcode.

### 🟡 Gotcha 4: Sample audio player autoplay

Một số browser chặn autoplay audio. Nếu page auto-play voice sample → UX fail.

**Fix**: User phải click play button để nghe. Dùng `<audio controls>` không dùng autoplay.

### 🟡 Gotcha 5: Test endpoint cost

Mỗi lần POST /test → backend call TTS API → tính credits.

**Fix**: Tier 2 confirm endpoint có cost tracking. Nếu không, escalate.

## Performance budget

- Step 1-2: 3 giờ
- Step 3-4: 4 giờ
- Step 5-6: 4 giờ
- Step 7-8: 3 giờ
- Step 9: 1 giờ
- Step 10-11: 6 giờ
- Total: ~21 giờ (= 4 ngày part-time)

## Exit gates

- [ ] All tests pass
- [ ] Coverage ≥80%
- [ ] LoC delta within budget (+400/-10)
- [ ] Tier 1 sign-off
- [ ] Merge to main