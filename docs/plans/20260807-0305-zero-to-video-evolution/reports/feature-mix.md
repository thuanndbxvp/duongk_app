# Hàm lượng mix giữa appDK và Ai86Studio

> Ngày: 2026-08-07 03:13 (UTC+7)
> Phạm vi: Xác định tỉ lệ giữ, biến đổi, bỏ qua giữa appDK (baseline) và Ai86Studio (nguồn học pattern).
> Vị trí: `D:\appDK\docs\plans\20260807-0305-zero-to-video-evolution\reports\feature-mix.md`

## 1. Mục đích của tài liệu này

Tránh cả hai cực đoan:

- Viết lại appDK thành bản sao Ai86Studio.
- Bỏ qua toàn bộ tính năng học từ Ai86Studio.

Mục tiêu thực dụng:

- Giữ cấu trúc dữ liệu, queue, credit, RAG, TTS, channel DNA hiện có.
- Hấp thụ pattern tốt: scene contract, render graph, asset pipeline, timeline JSON, versioned preset.
- Bỏ qua cơ chế rủi ro cao: session-token sniffing, CAPTCHA automation, cookie decrypt, watermark bypass, private endpoint scraping.

## 2. Ba nhóm tính năng

| Nhóm | Định nghĩa | Vai trò |
|---|---|---|
| Keep | Tính năng appDK đang có, dùng tiếp | Nền tảng không phải xây lại |
| Borrow | Pattern từ Ai86Studio được biến đổi, phù hợp với stack web | Đòn bẩy sản phẩm |
| Skip | Tính năng Ai86Studio quá rủi ro về điều khoản/kỹ thuật, hoặc không phù hợp web SaaS | Tránh nợ kỹ thuật và pháp lý |

## 3. Mix theo domain

### 3.1 Project & Onboarding

| Tính năng | Nguồn | Nhóm | Ghi chú |
|---|---|---|---|
| Channel assistant onboarding | appDK | Keep | Giữ, backward compat |
| Blank Project (chỉ topic) | Ai86Studio pattern | Borrow | Dùng `mode = blank` để bỏ qua DNA channel |
| Creative brief schema | Ai86Studio pattern | Borrow | Kết hợp channel profile của appDK, làm optional |
| Project root entity | Cả hai | Keep | Lifecycle cho cả video và artifacts |
| Versioned preset | Ai86Studio | Borrow | Áp dụng cho channel profile, genre profile, voice, style |

### 3.2 Content Intelligence (RAG, Idea, Script)

| Tính năng | Nguồn | Nhóm | Ghi chú |
|---|---|---|---|
| Channel DNA extraction | appDK | Keep | Đã chạy, không viết lại |
| RAG retrieval | appDK | Keep | `dna_chunks` 1024d Cohere đang ổn |
| Idea clustering + gap score | appDK | Keep | Đang có HDBSCAN |
| Idea from comments insights | Ai86Studio | Borrow | Phase 06, có evidence |
| Script generation | appDK | Keep | Có RAG + Anti-Slop, fallback provider |
| Script contract nâng cấp | Ai86Studio pattern | Borrow | Thêm outline, narration, chapters, prompt, voice direction |
| Comment intelligence | Ai86Studio pattern | Borrow | Provider hợp lệ, có evidence |
| Token sniffing từ session request | Ai86Studio | Skip | Rủi ro điều khoản |
| Cookie decrypt Chrome for Testing | Ai86Studio | Skip | Rủi ro bảo mật |
| reCAPTCHA Enterprise automation | Ai86Studio | Skip | Không dựng được ổn định |

### 3.3 Asset, Media Preparation

| Tính năng | Nguồn | Nhóm | Ghi chú |
|---|---|---|---|
| Scene contract | Ai86Studio pattern | Borrow | Narration, prompt, asset_type, duration, motion, transition |
| Scene editor UI | appDK + Ai86Studio pattern | Borrow | Tái cấu trúc `SceneTimeline` |
| Upload asset, R2 storage | appDK | Keep | Đã có storage, mở rộng signing |
| Pexels search/materialize | Cả hai | Borrow | Ai86Studio làm via browser session, appDK chuyển sang API chính thức |
| Unsplash/Pixabay | Ai86Studio | Borrow | Chỉ qua API chính thức |
| AI image provider | Ai86Studio pattern | Borrow | Phase 05 |
| AI video provider | Ai86Studio pattern | Borrow | Phase 05, adapter pattern |
| Upscale model | Ai86Studio pattern | Borrow | Phase 05, có probe binary/model |
| Watermark detection + inpaint | Ai86Studio pattern | Borrow | Phase 05, có provenance và consent gate |
| Rename contract | Ai86Studio pattern | Borrow | Phase 02, không phụ thuộc thứ tự file |
| Browser-driven download không qua API | Ai86Studio | Skip | Dễ gãy, vi phạm ToS |

### 3.4 Voice & Audio

| Tính năng | Nguồn | Nhóm | Ghi chú |
|---|---|---|---|
| OmniVoice TTS | appDK | Keep | Đã có serialized inference + timeout |
| Voice per scene | Ai86Studio pattern | Borrow | Phase 03, idempotency theo scene |
| Đo actual audio duration | Ai86Studio pattern | Borrow | Phase 03, dùng ffprobe/wave |
| Recalculate timeline | Ai86Studio pattern | Borrow | Phase 03 |
| Voice profile selector | appDK | Keep | Bảng `voice_profiles` đã có |
| Subtitle (SRT) | Ai86Studio pattern | Borrow | Phase 03 |
| Background music | Ai86Studio pattern | Borrow | Phase 04, thư viện có license rõ |
| Audio ducking | Ai86Studio pattern | Borrow | Phase 04 |

### 3.5 Timeline & Composition

| Tính năng | Nguồn | Nhóm | Ghi chú |
|---|---|---|---|
| Timeline JSON model | Ai86Studio pattern | Borrow | Phase 03, versioned |
| Render planner | Ai86Studio pattern | Borrow | Phase 04, tách UI khỏi FFmpeg |
| Render registry có cancel thật | Ai86Studio pattern | Borrow | Phase 04 |
| FFmpeg compose pipeline | Ai86Studio pattern | Borrow | Phase 04 |
| Ken Burns / xfade / overlay | Ai86Studio pattern | Borrow | Phase 04 |
| ffprobe verification | Ai86Studio pattern | Borrow | Phase 04 |

### 3.6 Output & Distribution

| Tính năng | Nguồn | Nhóm | Ghi chú |
|---|---|---|---|
| MP4 export | Ai86Studio pattern | Borrow | Phase 04 |
| Thumbnail generation | Ai86Studio pattern | Borrow | Phase 05 |
| SEO metadata | Ai86Studio pattern | Borrow | Phase 05 |
| Export package | Ai86Studio pattern | Borrow | Phase 05 |
| Watermark bypass | Ai86Studio | Skip | Dùng gói cho phép export sạch |

## 4. Mix theo thành phần kỹ thuật

| Lớp | appDK hiện có | Mượn từ Ai86Studio | Ghi chú |
|---|---|---|---|
| Frontend | Next.js + Tailwind + Glass design | Tách feature modules, typed state | Tránh 1 file renderer khổng lồ |
| Backend | FastAPI | Domain modules tách bạch | Mỗi domain có router riêng |
| Worker | Celery 4 queue | Capability probe, model probe | Bắt buộc khi gọi AI media |
| Storage | R2 immutable contract | Source immutable, versioned output, atomic move | Tránh ghi đè, hỗ trợ retry |
| TTS | OmniVoice Modal | Voice per scene + actual duration | Không bỏ serialized inference |
| Jobs | Durable jobs + progress | Cancel thật, registry theo `job_id` | Không dùng biến global |
| Credits | Hold/commit/refund | Thêm cost estimate và idempotency key | Tránh charge user khi provider lỗi |
| Routing | `service_routing_config` | Mở rộng sang image/video/upscale/thumbnail | Adapter pattern, không biết chi tiết provider |
| RAG | DNA chunks + persona | Thêm genre_profile cho blank project | Giữ schema, mở rộng input |
| Security | Supabase Auth + RLS | Audit log + content policy | Áp dụng cho AI generation |

## 5. Bảng tỉ lệ

| Nhóm | Tỉ lệ |
|---|---|
| Keep (tái sử dụng appDK) | ~50% |
| Borrow (pattern từ Ai86Studio, biến đổi) | ~40% |
| Skip (rủi ro cao / không phù hợp) | ~10% |

Trong nhóm Skip, mỗi tính năng đều có lý do cụ thể. Nếu sau này có giải pháp chính thức từ provider (ví dụ export MP4 sạch qua API), có thể quay lại Borrow.

## 6. Nguyên tắc khi mix

1. Ưu tiên API/SDK chính thức của provider thay vì cơ chế ngầm.
2. Mọi provider có adapter, fallback, capability probe và mock cho test.
3. Mọi job có id, progress thật, cancel thật và retry-safe.
4. Source asset immutable; output dùng atomic move.
5. Contract dữ liệu phải versioned.
6. User có approval gate trước mỗi stage tốn credits.
7. Insight AI phải có evidence.
8. Cleanup asset phải có consent + provenance.
9. UI không lưu workflow state; workflow state nằm trong DB.
10. Tất cả tính năng mượn phải được gắn `evidence-backed` (không bịa insight ngoài comment thật).

## 7. Mapping rủi ro → quyết định

| Pattern Ai86Studio | Rủi ro | Quyết định trong appDK |
|---|---|---|
| Sniff session token Google | ToS + bảo mật | Skip, dùng API chính thức hoặc Modal self-host |
| reCAPTCHA Enterprise automation | Pháp lý + kỹ thuật | Skip, dùng API chính thức |
| Cookie decrypt | Pháp lý + bảo mật | Skip, dùng OAuth user-side |
| Crawl comment không qua API | ToS + unstable | Borrow qua API chính thức, có evidence |
| Detect + inpaint watermark | ToS + bản quyền | Borrow với consent gate + license metadata |
| Browser session trong Electron | Khó port sang web SaaS | Chuyển sang API + server worker |

## 8. Bảng trên → roadmap

| Phase | Keep | Borrow |
|---|---|---|
| 01 | Project root, channel assistant, RAG, jobs | Blank Project, versioned preset, creative brief |
| 02 | R2 storage, scene list hiện có | Scene contract chuẩn, scene editor, Pexels API |
| 03 | OmniVoice | Voice per scene, actual duration, SRT, timeline model |
| 04 | Jobs, progress, credits | FFmpeg render, draft, cancel thật, verify output |
| 05 | Provider routing, credits | AI image/video, upscale, thumbnail, export package |
| 06 | DNA/RAG | Comment intelligence, batch production |
| 07 | Observability, RLS | Idempotency, dead-letter, content policy |

## 9. Kết luận mix

- appDK giữ vai trò **foundation** (~50%).
- Ai86Studio đóng vai trò **pattern source** (~40%) cho phần production chưa có.
- ~10% bị loại vì rủi ro pháp lý/kỹ thuật.
- Không có copy-paste: mọi pattern mượn đều được chuyển sang stack web SaaS và có đối tác API/SDK chính thức.

Nếu cần, phase tiếp theo có thể phát triển thành `phase-08-channel-intelligence.md` để cụ thể hóa việc mượn Tool 1 + Tool 11 vào hệ thống hiện có.
