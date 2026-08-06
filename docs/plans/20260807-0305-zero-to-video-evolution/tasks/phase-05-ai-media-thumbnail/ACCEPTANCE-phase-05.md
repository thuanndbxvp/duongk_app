# ACCEPTANCE: Phase 05 — AI Media

## 1. Functional
- [ ] User generate asset cho scene qua provider adapter được phép.
- [ ] Upscale tạo variant mới, không phá source.
- [ ] Thumbnail candidates gắn project, user select + version.
- [ ] Metadata package sinh title/desc/tags + thumbnail + SRT.
- [ ] Export package chứa MP4, SRT, thumbnail, metadata JSON.
- [ ] Credit hold/commit/refund hoạt động khi provider fail một phần.

## 2. Non-functional
### Bảo mật
- [ ] Cleanup chỉ chạy khi có consent_record + provenance.
- [ ] Preview KHÔNG mutate source.
- [ ] Provider key lưu Vault, không log.

### Hiệu năng
- [ ] Thumbnail generation < 60s cho 3 candidates.
- [ ] Upscale < 30s cho ảnh 1920x1080.

## 3. Coverage
- ≥80% cho `media_pipeline`, `watermark_cleanup`, `thumbnail_generate`, `metadata_package`.
- 100% cho schemas.

## 4. Manual Verify
```powershell
# Test consent gate: gọi cleanup không consent → 403.
# Test preview → approve → variant mới tạo, source KHÔNG đổi.
```

## 5. Done
- All checkboxes pass.
- AUDIT-REPORT nộp.