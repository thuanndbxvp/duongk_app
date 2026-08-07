# Phase 5 — MSEW

## Milestones

| Step | Action | Skills |
|---|---|---|
| 1 | Verify asset endpoints | `debugging` |
| 2 | Build `<AssetGrid>` + filters | `frontend-development`, `ui-styling` |
| 3 | Build list page `/assets` | `frontend-development` |
| 4 | Build `<AssetUpload>` | `frontend-development`, `ui-styling` |
| 5 | Build detail page `/assets/[id]` | `frontend-development` |
| 6 | Verify channel collector endpoints | `debugging` |
| 7 | Build `<ChannelList>` + `<ScrapeJobList>` | `frontend-development`, `ui-styling` |
| 8 | Build list page `/channel-collector` | `frontend-development` |
| 9 | Build detail page `/channel-collector/[id]` | `frontend-development` |
| 10 | Build channel form | `frontend-development` |
| 11 | Tests | `testing-protocol` |
| 12 | Review | `code-review` |

## Skills routing

| Task | Primary | Secondary |
|---|---|---|
| Components | `frontend-development` | `ui-styling` |
| File upload | `frontend-development` | `ui-styling` |
| Tests | `testing-protocol` | — |

## Evidence

```bash
# Asset endpoints
curl -X GET "http://localhost:8000/api/assets?type=image" -H "Authorization: Bearer ${TOKEN}"
curl -X POST "http://localhost:8000/api/assets" -H "Authorization: Bearer ${TOKEN}" -F "file=@/path/to/image.jpg" -F "name=test" -F "tags=test,hero"
curl -X GET "http://localhost:8000/api/assets/{id}" -H "Authorization: Bearer ${TOKEN}"

# Channel collector
curl -X POST "http://localhost:8000/api/channel-collector/channels" -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" -d '{"url":"https://youtube.com/@example","name":"Example Channel"}'
curl -X POST "http://localhost:8000/api/channel-collector/scrape" -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" -d '{"channel_id":"..."}'

pytest tests/web/components/test_asset_grid.tsx -v
pytest tests/api/test_asset_endpoints.py -v
pytest tests/api/test_channel_collector.py -v
```

## Warnings

### 🟡 Gotcha 1: Asset upload size limit

Cloudflare R2 default max file size: 5GB. Nhưng Next.js server có body size limit (default 1MB cho API routes, 4MB cho server actions).

**Fix**: Tier 2 confirm Next.js config đã bump body size limit. Nếu chưa → escalate.

### 🟡 Gotcha 2: Video thumbnail generation

Video assets không có automatic thumbnail. Cần extract frame đầu tiên.

**Fix**: Tier 2 chỉ hiển thị video player trực tiếp (no thumbnail). Hoặc dùng ffmpeg trên backend (đã có).

### 🟡 Gotcha 3: Channel scraping timeout

Scrape job có thể mất 30 phút. UI phải poll hoặc dùng WebSocket.

**Fix**: P5 dùng polling (refresh button manual). WebSocket để P6+.

### 🟡 Gotcha 4: Asset tags = array

Backend expect `tags: string[]`. Form phải parse từ string (comma-separated) → array.

**Fix**: Helper function `parseTags(input: string): string[]`.

### 🟡 Gotcha 5: Channel URL validation

YouTube channel có nhiều format:
- `https://youtube.com/@handle`
- `https://youtube.com/channel/UC...`
- `https://youtube.com/c/Name`
- `https://youtu.be/...`

**Fix**: Backend validate (đã có). Frontend chỉ check basic URL format.

## Performance budget

- Step 1-5: 12 giờ (asset library)
- Step 6-10: 8 giờ (channel collector)
- Step 11-12: 4 giờ (tests + review)
- Total: ~24 giờ (= 4 ngày part-time)

## Exit gates

- [ ] All tests pass
- [ ] Coverage ≥80%
- [ ] LoC delta +700/-10
- [ ] Tier 1 sign-off