# Tiêu chí Nghiệm thu (ACCEPTANCE): Task 2.3

## 1. Tiêu chuẩn Chức năng

- [ ] Output 8 (Hooks): hook_patterns, hook_framework
- [ ] Output 9 (Structure): typical_structure, structure_type
- [ ] Output 11 (Mimic): mimic_guidelines, tone
- [ ] Output 14 (Thumbnail): avg_thumbnail_style, thumbnail_effectiveness
- [ ] E7 FIX: Versioning increments on re-analysis
- [ ] API `/api/llm/analyze` hoạt động

## 2. Verification Commands

```powershell
$body = @{
    transcripts = @("Bạn có biết cách làm đẹp không? Tôi sẽ hướng dẫn bạn.")
    titles = @("Bạn có biết cách làm đẹp?")
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/llm/analyze" -Method Post -Body $body -ContentType "application/json"
```

## 3. Sign-off Checklist

- [ ] GPT-4o returns valid JSON
- [ ] Vision analyzes thumbnails
- [ ] Versioning works
- [ ] Unit tests pass
