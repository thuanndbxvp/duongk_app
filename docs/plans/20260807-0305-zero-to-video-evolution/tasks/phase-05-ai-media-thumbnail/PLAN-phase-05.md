# PLAN: Phase 05 — AI Media, Thumbnail

## 1. Mục tiêu
- **Mô tả:** Provider routing mở rộng cho image/video generation, upscale, thumbnail, music. Pipeline media preparation chuẩn hoá. Watermark cleanup an toàn với consent gate.
- **Giá trị:** Thumbnail sinh AI bắt mắt, asset upscale chất lượng cao, cleanup watermark hợp pháp.

## 2. Kiến trúc
```text
User request → Capability probe → ProviderAdapter
  → Normalize → Optional upscale → Optional authorized cleanup → Resize → Validate
  → asset_variants row → Manifest (provider, model_version, license)
```

## 3. Lựa chọn
- **Phương án A — Cleanup mặc định (ĐÃ LOẠI):** Rủi ro pháp lý.
- **Phương án B — Consent gate + provenance + preview (CHỌN):** An toàn, có audit.
- **Phương án C — Cleanup provider có gói chính thức no-watermark (CÂN NHẮC):** Ưu tiên dùng cho provider có sẵn.

## 4. Rủi ro

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Cleanup không có consent → vi phạm | Cao | Consent gate bắt buộc. |
| Provider key lộ | Cao | Vault, không hardcode. |
| Cleanup ghi đè source | Cao | Temp output → atomic move. |
| Cleanup chạy hàng loạt không preview | Trung bình | Per-asset preview trước khi commit. |
| Rate limit provider | Thấp | Capability probe + retry. |

## 5. Nỗ lực
- ~1300 LOC, 9 micro-steps, 6–7 ngày Tier 2.