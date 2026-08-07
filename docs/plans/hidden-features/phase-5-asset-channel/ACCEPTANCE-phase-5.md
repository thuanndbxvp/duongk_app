# Phase 5 — Acceptance Criteria

## A. Asset Library

### A.1 — List page

- [ ] `/assets` exists
- [ ] Grid view với thumbnails
- [ ] Filter: type, tags, project
- [ ] Sort: created date, name, size
- [ ] Pagination
- [ ] Upload button
- [ ] Empty state
- [ ] Loading skeleton
- [ ] Error state

### A.2 — Detail page

- [ ] `/assets/[id]` exists
- [ ] Preview (image/video/audio)
- [ ] Metadata hiển thị
- [ ] Edit form
- [ ] Delete with confirm
- [ ] Download button
- [ ] Use in project button

### A.3 — Upload

- [ ] File input với drag-drop
- [ ] Type validation
- [ ] Size validation
- [ ] Progress bar
- [ ] Success/error states

## B. Channel Collector

### B.1 — List page

- [ ] `/channel-collector` exists
- [ ] List tracked channels
- [ ] Add channel button
- [ ] Recent jobs list
- [ ] Empty states

### B.2 — Detail page

- [ ] `/channel-collector/[id]` exists
- [ ] Channel metadata
- [ ] Recent videos
- [ ] Top comments/insights
- [ ] Re-scrape button
- [ ] Delete button

### B.3 — Add channel form

- [ ] Form với URL + name
- [ ] Validate URL format
- [ ] Submit → POST /api/channel-collector/channels
- [ ] Loading state

## C. Tests

- [ ] Component tests for grid, filters, upload
- [ ] Integration tests for endpoints
- [ ] E2E flow

## D. Final

- [ ] Tests pass ≥80%
- [ ] Coverage ≥80%
- [ ] LoC delta: +700 / -10
- [ ] Tier 1 review

## Sign-off

| Role | Name | Date | Status |
|---|---|---|---|
| Implementer | _Tier 2_ | ____ | ☐ |
| Reviewer | _Tier 1_ | ____ | ☐ |