# Kế hoạch tiến hóa appDK thành Zero-to-Video Workspace

> Ngày: 2026-08-07 03:05 (UTC+7)
> Phạm vi: Thiết kế hướng phát triển, chưa triển khai code.
> Baseline: code thực tế tại `D:\appDK` và bài học từ `Ai86Studio` trong `docs/PIPELINE-INSIGHTS-FOR-NEW-PROJECT.md`.

## Mục tiêu sản phẩm

Biến appDK từ nền tảng `channel analysis → idea → script → scene → TTS` thành workspace:

```text
Blank idea OR reference channel
  → Creative brief
  → Concepts / outline
  → Script
  → Scene contracts
  → Asset search / upload / generation
  → Voice + subtitles
  → Timeline
  → Draft render
  → Edit / approve
  → Final MP4 + SRT + metadata + thumbnail
```

User mới không cần channel, footage, voice sample hoặc kỹ năng dựng video. Channel cloning vẫn là chế độ nâng cao, không phải điều kiện bắt đầu.

## Quyết định kiến trúc

| Quyết định | Lựa chọn | Lý do |
|---|---|---|
| Product shape | Next.js + FastAPI + Celery, giữ stack hiện tại | Giảm rủi ro, tái sử dụng code và deployment |
| Workflow root | `projects` | Một video và toàn bộ artifacts phải có cùng lifecycle |
| Async execution | Celery + Redis + durable `jobs` | Đã có sẵn queue, retry, credits, progress |
| Media storage | R2 với immutable source + versioned output | Tránh mất file, hỗ trợ retry và audit |
| Rendering | FFmpeg worker trước; provider GPU là adapter sau | Có MVP hoạt động không phụ thuộc provider AI |
| Content schema | Typed JSON contracts + DB migration | Đảm bảo scene/asset/timeline không trôi schema |
| Provider integration | Adapter + routing/fallback | Học từ routing hiện có, thay provider không đổi business logic |
| Channel profile | Optional | Hỗ trợ user bắt đầu từ tay trắng |
| Flow/CDP/CAPTCHA | Không đưa vào MVP | Rủi ro điều khoản, bảo trì và vận hành cao |

## Nguyên tắc

1. Project state là nguồn sự thật; không dùng UI state làm workflow state.
2. Mỗi stage có job ID, progress, error code, retry và output manifest.
3. User duyệt trước các bước tốn credits: concept, script, scene plan, generation batch, final render.
4. Source asset bất biến; mọi xử lý tạo artifact mới.
5. TTS duration thật được dùng để hiệu chỉnh timeline.
6. Insight AI phải có evidence; không tạo kết luận không truy xuất được.
7. Provider phải có mock/fallback/capability probe.
8. Chỉ xử lý asset khi user có quyền; không xây watermark bypass hoặc session-token scraping.

## Roadmap tổng quan

| Phase | Mục tiêu | Trạng thái |
|---|---|---|
| 01 | Project + blank onboarding + content contracts | Planned |
| 02 | Scene studio + asset management + stock search | Planned |
| 03 | Voice per scene + SRT + timeline model | Planned |
| 04 | FFmpeg draft/final render + export | Planned |
| 05 | AI media providers + upscale + thumbnail | Planned |
| 06 | Channel intelligence feedback loop + batch production | Planned |
| 07 | Hardening, observability, billing and launch | Planned |
| 08 | Channel intelligence + comment + RAG integration | Planned |
| 09 | Style bible + character reference + design system | Planned |
| 10 | Batch production + cost estimation + provider fallback | Planned |
| 11 | Character & background lab (presets trước khi batch scene) | Planned |

## Dependencies

- Phase 01 trước Phase 02–06.
- Phase 02 trước Phase 03–04.
- Phase 03 trước render final ở Phase 04.
- Phase 04 là prerequisite để gọi AI media ở quy mô lớn.
- Phase 05 và 06 có thể chạy song song sau Phase 04.
- Phase 08 mở rộng Phase 06 (channel intelligence + RAG integration), phụ thuộc Phase 01.
- Phase 09 (style bible) phụ thuộc Phase 01 (brief schema); tích hợp với Phase 05 (AI media) và Phase 08 (RAG inject).
- Phase 10 (batch + fallback) phụ thuộc Phase 04 (render registry có cancel thật), Phase 05 (provider routing đầy đủ) và Phase 06 (batch scope).
- Phase 11 (character/background lab) phụ thuộc Phase 02 (scene.characters + scene.background), Phase 05 (provider adapter + capability probe), Phase 09 (style bible + anchor_strength); Phase 10 batch scene chỉ chạy khi Phase 11 lab approved.
- Không bắt đầu Phase 06 batch production trước khi cancellation, idempotency và cost controls hoàn tất.
- Không bắt đầu Phase 10 batch fan-out trước khi Phase 04 đã có cancel thật và Phase 05 có provider adapter chuẩn.
- Không bắt đầu Phase 10 batch scene assets khi chưa có Phase 11 lab_run.status = approved.

## Definition of success

Một user mới có thể:

1. Tạo blank project chỉ bằng topic.
2. Duyệt concept, sửa script và scene.
3. Chọn/upload/tìm asset cho từng scene.
4. Tạo voice và subtitle.
5. Xem draft render.
6. Chỉnh timeline.
7. Export MP4, SRT, thumbnail và metadata.

Chi tiết nằm trong các phase files.

## Unresolved decisions

- Chọn render local CPU, dedicated worker GPU hay Modal làm primary.
- Chọn provider AI image/video đầu tiên và license policy.
- R2 presigned URL lifecycle và dung lượng miễn phí theo tier.
- Timeline editor mức nào cho MVP: scene board hay drag/drop đầy đủ.
- Có cần thêm SQLite/local cache cho job recovery hay Supabase đủ dùng.
- Video đầu tiên ưu tiên `16:9` hay hỗ trợ `9:16` ngay từ Phase 01.
