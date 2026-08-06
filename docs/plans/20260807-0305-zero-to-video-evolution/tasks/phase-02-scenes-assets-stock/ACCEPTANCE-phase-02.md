# Tiêu chí Nghiệm thu (ACCEPTANCE): Phase 02 — Scene Studio

## 1. Functional Criteria
- [ ] User upload được image/video/audio; preview hiển thị.
- [ ] User search Pexels, chọn result → asset materialize vào R2.
- [ ] Asset từ Pexels có license.photographer, license.pexels_id, license.url.
- [ ] Retry download không tạo duplicate nhờ `provider + provider_id` unique.
- [ ] Scene reorder giữ stable `scene_id`; asset binding không đổi.
- [ ] Mapping scene → asset có thể thay đổi mà không đổi narration.
- [ ] Save draft + dirty state cho scene editor.
- [ ] Validation: scene thiếu asset cảnh báo; duration vượt target cảnh báo.

## 2. Non-functional
### Bảo mật
- [ ] RLS: user B không select asset/scene của user A.
- [ ] Signed URL upload TTL ≤ 15 phút; download TTL ≤ 5 phút.
- [ ] Magic byte scan reject file không khớp MIME.
- [ ] Size limit: image ≤ 20MB, video ≤ 200MB, audio ≤ 50MB.

### Hiệu năng
- [ ] Search Pexels < 2s cho page đầu.
- [ ] Upload-init < 300ms.

## 3. Test Coverage
- Coverage ≥80% cho:
  - `apps/api/routers/assets.py`
  - `apps/worker/services/asset_providers/`
  - `apps/worker/tasks/materialize_asset.py`
- 100% cho `apps/api/schemas/assets.py`.

## 4. Manual Verification (Windows)
```powershell
.\venv\Scripts\Activate.ps1
supabase db reset
uvicorn apps.api.main:app --reload

# Upload test
$body = @{ filename="test.jpg"; mime_type="image/jpeg"; size_bytes=102400; checksum="abc123" } | ConvertTo-Json
$resp = Invoke-RestMethod -Uri "http://localhost:8000/api/assets/upload-init" -Method Post -Headers $headers -ContentType "application/json" -Body $body
Write-Host $resp.upload_url

# Search Pexels
$search = @{ provider="pexels"; query="mountain"; media_type="image" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/assets/search" -Method Post -Headers $headers -ContentType "application/json" -Body $search
```

## 5. Done khi
- Tất cả checkbox mục 1, 2 đạt.
- Tests pass với coverage mục 3.
- AUDIT-REPORT nộp cho Tier 1.
- KHÔNG push git cho đến khi sếp duyệt.