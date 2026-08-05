# Tiêu chí Nghiệm thu (ACCEPTANCE): Task 2.2

## 1. Tiêu chuẩn Chức năng

- [ ] E2 FIX: Models load as singletons
- [ ] Output 5 (Emotions): dominant_emotions, emotion_distribution
- [ ] Output 6 (Pacing): avg_wpm, avg_sentence_length
- [ ] Output 7 (Category): primary_category, confidence
- [ ] Output 10 (Hook): hook_types_detected, effectiveness
- [ ] API `/api/nlp/analyze` hoạt động

## 2. Verification Commands

```powershell
$body = @{
    transcripts = @("Bạn có biết cách làm đẹp không? Tôi sẽ hướng dẫn bạn cực kỳ chi tiết.")
    titles = @("Bạn có biết cách làm đẹp?", "Cách chăm sóc da mùa đông")
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/nlp/analyze" -Method Post -Body $body -ContentType "application/json"
```

## 3. Sign-off Checklist

- [ ] ML models load without errors
- [ ] All outputs generated
- [ ] Unit tests pass
