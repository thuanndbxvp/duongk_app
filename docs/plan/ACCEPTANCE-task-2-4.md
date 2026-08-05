# Tiêu chí Nghiệm thu (ACCEPTANCE): Task 2.4

## 1. Tiêu chuẩn Chức năng

- [ ] E3 FIX: Vietnamese text → Cohere model
- [ ] E3 FIX: English text → OpenAI model
- [ ] E3 FIX: Dimensions = 1024 for both
- [ ] Chunk size ~500 tokens
- [ ] Overlap working
- [ ] E6 FIX: TTL = 90 days set
- [ ] E6 FIX: Cron cleanup scheduled
- [ ] API `/api/rag/embed` hoạt động

## 2. Verification Commands

```powershell
$body = @{
    transcripts = @("Bạn có biết cách làm đẹp không? Đây là video hướng dẫn chi tiết.")
    video_id = "test123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/rag/embed" -Method Post -Body $body -ContentType "application/json"
```

## 3. Sign-off Checklist

- [ ] Embedding dimensions verified (1024)
- [ ] Language detection works
- [ ] TTL columns created
- [ ] Unit tests pass
