# Phase 05 — AI media, upscale, thumbnail và metadata

## Mục tiêu

Thêm các tính năng học từ Ai86Studio sau khi upload/stock/render core đã ổn định.

## Provider routing

Mở rộng routing hiện có cho:

- `image_generation`.
- `video_generation`.
- `image_upscale`.
- `thumbnail_generation`.
- `music_search`.

Mỗi provider adapter có timeout, retry classification, estimated cost, quota response và capability probe.

Không xây adapter dựa trên sniff token phiên, CAPTCHA bypass hoặc private endpoint không được phép.

## Media preparation

Pipeline:

```text
source asset
  → normalize
  → optional upscale
  → optional authorized cleanup
  → target resize
  → validate
  → variant manifest
```

Requirements:

- Source immutable.
- Temp output rồi atomic move.
- Preview trước cleanup.
- Model/binary/GPU probe.
- Retry từng asset.
- Ghi provider/model/parameters/license vào manifest.

## Thumbnail

Input:

- Project brief.
- Script hook.
- Channel/genre style.
- Candidate visual assets.

Output:

- 2–4 candidates.
- 1280x720.
- Text legibility check.
- Optional AI vision score cho contrast/composition.
- User selection và version.

## Metadata package

Sinh:

- Title candidates.
- Description.
- Tags.
- Chapters từ timeline/voice.
- Hashtags.
- Thumbnail.
- SRT.

Không coi SEO output là sự thật tuyệt đối; cho user review và chỉnh sửa.

## Acceptance criteria

- User generate được asset cho từng scene qua provider adapter được phép.
- Upscale tạo variant mới, không phá source.
- Thumbnail candidates gắn project/manifest.
- Export package chứa MP4, SRT, thumbnail và metadata JSON.
- Credit hold/commit/refund hoạt động khi provider fail một phần.
