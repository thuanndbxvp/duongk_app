# Phase 3 — Acceptance Criteria

## A. List page

- [ ] `/voice-profiles` route exists
- [ ] Grid view renders voices từ GET /api/voices
- [ ] "New voice" button → /voice-profiles/new
- [ ] Empty state with CTA
- [ ] Loading skeleton
- [ ] Error state
- [ ] Click card → /voice-profiles/[id]

## B. Create page

- [ ] `/voice-profiles/new` route exists
- [ ] Form với name, provider, language, gender, sample
- [ ] Providers dropdown from GET /api/voices/providers
- [ ] Language auto-set dựa trên provider
- [ ] File input validates MP3/WAV, max 10MB
- [ ] Required sample if provider.requires_sample
- [ ] Submit → POST /api/voices với multipart
- [ ] Success → redirect to detail
- [ ] Error → inline display

## C. Detail page

- [ ] `/voice-profiles/[id]` route exists
- [ ] Voice metadata hiển thị
- [ ] Sample audio player
- [ ] Test button với text input → POST /test → play audio
- [ ] Edit button → navigate to /edit
- [ ] Delete button với confirm
- [ ] Clone button (optional, if backend supports)

## D. Backend /providers endpoint

- [ ] GET /api/voices/providers exists
- [ ] Returns providers với languages, supports_clone, requires_sample
- [ ] Static data OK (no DB needed)

## E. Tests

- [ ] List page renders
- [ ] Form validation works
- [ ] POST /api/voices với multipart
- [ ] POST /api/voices/{id}/test
- [ ] DELETE /api/voices/{id}
- [ ] E2E flow

## F. Final

- [ ] All tests pass
- [ ] Coverage ≥80%
- [ ] LoC delta: +400 / -10
- [ ] No new dependencies (already have FormData support)
- [ ] Tier 1 review pass

## Sign-off

| Role | Name | Date | Status |
|---|---|---|---|
| Implementer | _Tier 2_ | ____ | ☐ |
| Reviewer | _Tier 1_ | ____ | ☐ |