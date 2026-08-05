# Tiêu chí Nghiệm thu (ACCEPTANCE): Task 2.1

## 1. Tiêu chuẩn Chức năng

- [ ] Output 1 (Metadata) có: total_videos, avg_duration, median_views, engagement_rate
- [ ] Output 2 (Tags) có: top_tags, tag_cooccurrence_matrix
- [ ] Output 3 (Performance) có: best/worst videos, consistency_score
- [ ] Output 4 (Duration) có: optimal_duration_seconds, recommendations
- [ ] Formula A5 consistency score: 0-1
- [ ] API `/api/analysis/channel` hoạt động

## 2. Verification Commands

```powershell
# Unit tests
pytest tests/test_analysis/ -v --cov=apps/api/modules/analysis

# Manual test
$body = @{ videos = @(@{duration=600; views=10000}) } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/analysis/channel" -Method Post -Body $body -ContentType "application/json"
```

## 3. Sign-off Checklist

- [ ] All unit tests pass
- [ ] Coverage ≥ 80%
- [ ] API endpoint verified
