# Ai86Studio — Ghi chú học tập cho dự án tương tự

> Bản ghi chú rút ra từ `docs/PIPELINE-ANALYSIS.md` (phân tích source deobfuscate, ngày 07/08/2026).
> Tập trung vào 4 nhóm sau: **Tool 1 + Tool 11**, **Tool 4 + Upscale + Watermark**, **Tool 7**, và luồng **Ý tưởng → Kịch bản → Cảnh (Tool 1 + 2)**.

---

## 0. Disclaimer quan trọng

Tài liệu gốc có mô tả một số cơ chế nhạy cảm về mặt pháp lý/kỹ thuật:

- **Sniff token phiên Google** từ request thực tế (thay vì OAuth chính thức).
- **Tự động hóa reCAPTCHA Enterprise** bằng Chrome instance phụ.
- **Decrypt cookie** từ Chrome for Testing trên macOS.
- **Crawl comment** không qua public API chính thức.
- **Xóa watermark** asset của bên khác.

Khi xây dự án mới, nên coi các phần này là **vùng rủi ro cao**:

- Ưu tiên dùng API chính thức của provider.
- Tôn trọng điều khoản dịch vụ, bản quyền, quyền sở hữu nội dung.
- Không mặc định sao chép cơ chế bypass CAPTCHA hay token scraping.
- Có consent rõ ràng cho mọi thao tác xử lý asset.
- Khi xóa watermark, đảm bảo asset thuộc quyền sở hữu hợp pháp của user.

---

## 1. Ý tưởng cốt lõi cần học

### 1.1 Content model trước, UI sau

Topic phải biến thành một cấu trúc trung gian có thể đưa cho TTS, image generation, timeline và SEO.

### 1.2 Mỗi worker có hợp đồng riêng

FFmpeg, Python voice, image processing, AI provider đều nhận input/output rõ ràng, có progress, có phân loại lỗi.

### 1.3 Tách tác vụ tốn thời gian khỏi UI

Job queue + task ID + polling/event stream giúp app chịu được render/generation nhiều phút mà không treo UI.

### 1.4 Có review gate trước chi phí lớn

User duyệt outline, scene plan, prompt trước khi gọi model hoặc render hàng loạt.

### 1.5 Luồng tham chiếu

```
Topic → Channel profile → Research insight
  ↓
Outline → Script → Scene contracts
  ↓
Assets → Normalize → Upscale / cleanup
  ↓
Voice + SRT → Timeline → FFmpeg export
  ↓
Thumbnail + SEO → Publish → Learn
```

### 1.6 Kiến trúc tổng thể hiện tại

```
Web UI
  ↓
preload / contextBridge
  ↓
Electron main process
  ↓
Domain native modules
  ↓
FFmpeg / Python / Chrome / CLI
```

---

## 2. Tool 1 + Tool 11 — biến "kênh" thành vòng lặp học nội dung

Hai chức năng này không nên là hai màn hình độc lập. Chúng tạo thành feedback loop:

> **Profile định nghĩa mục tiêu** → **Comment & video đối thủ cung cấp tín hiệu** → **Insight quay lại cải thiện brief và script**.

### 2.1 Channel Profile — không chỉ là metadata hiển thị

Nên lưu dưới dạng **versioned preset**, được inject vào mọi bước sau:

| Nhóm | Trường |
|---|---|
| Audience | Nhóm khán giả, ngôn ngữ, thị trường |
| Editorial | Chủ đề, góc nhìn, độ dài, nhịp kể |
| Brand | Tone, từ cấm, style thumbnail, màu, CTA |
| Production | Tỉ lệ 16:9/9:16, voice preset, music policy |
| Distribution | Title pattern, tag rules, upload defaults |

Ví dụ một preset:

```
Channel Profile
  audience: nam 25–40 tuổi
  language: tiếng Việt
  tone: điều tra, nghiêm túc
  duration: 8–12 phút
  visual_style: cinematic documentary
  voice: male_deep_narrator
  cta: mềm, không bán hàng trực tiếp
```

### 2.2 Comment Intelligence — từ dữ liệu thô đến quyết định sản xuất

Pipeline đề xuất:

```
1. Import video URL/ID theo quyền truy cập hợp lệ
2. Thu thập comment, reply, like count, timestamp, language
3. Chuẩn hóa, loại spam, deduplicate, ẩn PII không cần thiết
4. Phân cụm: câu hỏi / pain point / phản biện / mong muốn phần tiếp theo
5. AI tổng hợp evidence, không bịa "insight" ngoài comment
6. Xuất content opportunities và đưa vào brief/script
```

### 2.3 Module mapping

| Module | Dữ liệu chính | Output dùng ở đâu |
|---|---|---|
| Profile | channel_id, audience, voice, style, constraints | Prompt, scene style, TTS, thumbnail, SEO |
| Source video | url/id, title, creator, fetched_at | Traceability, refresh dữ liệu |
| Comment | text, parent, likes, language, status | Clustering, evidence |
| Insight | theme, evidence[], confidence, opportunity | Idea backlog, script brief |

### 2.4 Comment không phải output cuối

Output có giá trị phải là:

- Ý tưởng video mới.
- Câu hỏi cần giải đáp.
- Góc tiếp cận khác.
- Hook mới.
- Nội dung nên bổ sung trong phần tiếp theo.
- Điểm người xem phản ứng mạnh.

### 2.5 Insight schema — phải có evidence

```json
{
  "theme": "Người xem chưa hiểu nguyên nhân X",
  "evidence": [
    {
      "comment_id": "...",
      "text": "...",
      "likes": 124
    }
  ],
  "confidence": 0.86,
  "opportunity": {
    "title": "...",
    "angle": "...",
    "target_audience": "..."
  }
}
```

Không nên để AI tự tạo insight mà không có comment gốc làm bằng chứng.

---

## 3. Lên ý tưởng + viết kịch bản — thiết kế như một compiler

### 3.1 Vì sao không dừng ở "một đoạn script"

Hệ thống yếu thường làm:

```
Topic → Một đoạn script dài
```

Ai86Studio mô tả cách tốt hơn:

```
Topic
  ↓
Script
  ↓
Scenes
  ├── Visual description
  ├── Image prompt
  └── Narration
```

Tôi khuyến nghị mở rộng thành **6 stage** như dưới.

### 3.2 Stage 1 — Brief

Input nên có:

- Topic.
- Audience.
- Channel profile.
- Mục tiêu video.
- Độ dài mong muốn.
- Ngôn ngữ.
- Tone.
- Reference videos.
- Comment insights.
- Ràng buộc nội dung.

### 3.3 Stage 2 — Outline

Cấu trúc chuẩn:

```
Hook
  ↓
Promise / Context
  ↓
Main beats
  ↓
Escalation
  ↓
Payoff
  ↓
Conclusion / CTA
```

User nên duyệt outline trước khi AI viết toàn bộ script.

### 3.4 Stage 3 — Script

Script cần được viết theo voice profile của kênh, không chỉ theo topic. Cần quan tâm:

- Câu ngắn hay dài.
- Mật độ thông tin.
- Nhịp kể.
- Mức độ cảm xúc.
- Cách mở đầu.
- Cách chuyển đoạn.
- CTA.

### 3.5 Stage 4 — Scene split

Mỗi scene nên là một **data contract ổn định**:

```json
{
  "scene_id": "scene-001",
  "scene_index": 1,
  "narration": "...",
  "visual_description": "...",
  "image_prompt": "...",
  "asset_type": "image | video",
  "estimated_duration": 6.5,
  "characters": ["..."],
  "background": "...",
  "continuity_references": ["scene-000"],
  "status": "draft"
}
```

Nên thêm các trường:

- `version`.
- `asset_ids`.
- `voice_line_id`.
- `transition`.
- `camera_motion`.
- `generation_status`.
- `error`.
- `retry_count`.

### 3.6 Stage 5 — Validation

Trước khi gọi model tạo ảnh/video/TTS:

| Kiểm tra | Mục đích |
|---|---|
| Scene có narration | Tránh cảnh im lặng không chủ đích |
| Prompt đủ thông tin | Không thiếu style, character, setting |
| Tổng thời lượng khớp | Match target duration của video |
| Nhân vật nhất quán | Continuity qua các cảnh |
| Không scene trùng/thiếu | Coverage outline đầy đủ |
| Asset type có worker hỗ trợ | Tránh gọi provider không hỗ trợ |
| Nội dung không vi phạm policy | Safety check |
| JSON đúng schema | Tránh lỗi downstream |

### 3.7 Stage 6 — Approval gate

Quy tắc quan trọng:

> **Không nên gọi tất cả AI generation ngay sau khi tạo script.**

Luồng chuẩn:

```
Brief → Outline → Script → Scene Plan → Approve → Generate Assets
```

Tránh mất credits và thời gian khi outline hoặc scene plan chưa đúng.

### 3.8 Quy tắc prompt hình ảnh

Prompt hình ảnh nên được sinh từ **style bible chung** + thông tin scene riêng.

Nếu mỗi scene tự viết toàn bộ prompt từ đầu, nhân vật, ánh sáng, ống kính, bối cảnh sẽ trôi dần.

Style bible có thể gồm:

- Mô tả phong cách tổng thể.
- Lighting rule.
- Lens rule.
- Color palette.
- Character reference.
- Background reference.
- Negative prompt chung.

---

## 4. Tool 4 + Upscale + Watermark — Media Preparation Stage

Ba thao tác nên gom thành một stage:

```
Raw Assets
  ↓
Rename / Normalize
  ↓
Watermark Detection / Cleanup
  ↓
Upscale
  ↓
Target Resize
  ↓
Validated Assets
```

### 4.1 Tool 4 — Rename contract

Không nên chỉ rename theo thứ tự file trong thư mục. Cần có:

- Quy tắc sort rõ ràng.
- Mapping từ tên cũ sang tên mới.
- Preview trước khi thực hiện.
- Collision detection.
- Kiểm tra file bị thiếu.
- Không ghi đè file gốc ngay lập tức.
- Khả năng undo hoặc lưu rename manifest.

Ví dụ mapping:

| Old name | New name | Scene |
|---|---|---|
| flow_result_8.png | scene-001.png | 1 |
| download_22.webp | scene-002.webp | 2 |
| upload_final.jpg | scene-003.jpg | 3 |

Tốt hơn nữa là dùng ID logic của scene thay vì phụ thuộc hoàn toàn vào tên file.

### 4.2 Upscale contract

Pipeline trong tài liệu có logic hợp lý:

1. Kiểm tra kích thước ảnh.
2. Nếu ảnh đã lớn hơn target → resize xuống.
3. Nếu ảnh nhỏ hơn target → dùng Real-ESRGAN.
4. Resize lần cuối về đúng kích thước yêu cầu.
5. Convert format.
6. Emit progress.

Điểm cần học:

- Probe binary trước khi chạy.
- Kiểm tra model tồn tại.
- Kiểm tra GPU/Vulkan/CPU capability.
- Cho phép chọn model.
- Lưu thông số upscale vào manifest.
- Chạy từng ảnh hoặc theo batch có retry riêng.
- Không để lỗi một ảnh làm mất toàn bộ batch.

Output manifest:

```json
{
  "source": "scene-001.png",
  "output": "scene-001-upscaled.png",
  "model": "remacri-4x",
  "scale": 2,
  "target_width": 3840,
  "target_height": 2160,
  "duration_ms": 18340,
  "status": "completed"
}
```

### 4.3 Watermark cleanup — cần provenance

Về kỹ thuật, tài liệu mô tả hai hướng:

- Detection watermark bằng model.
- Inpainting vùng được phát hiện bằng LaMa hoặc MI-GAN.

Pipeline nên là:

```
Input
  ↓
Detect boxes
  ↓
Preview cho user
  ↓
Approve
  ↓
Inpaint vào temp output
  ↓
Validate output
  ↓
Ghi manifest
```

Không nên mặc định:

- Ghi đè source.
- Xóa watermark mà không xác nhận quyền xử lý.
- Xóa attribution hoặc dấu bản quyền từ asset của bên khác.
- Chạy inpainting hàng loạt không có preview.

Nếu asset được tạo từ provider có watermark, giải pháp an toàn hơn:

- Dùng gói/API chính thức cho phép export không watermark.
- Dùng asset mà bạn sở hữu đầy đủ quyền.
- Có thỏa thuận với provider về quyền xử lý.

---

## 5. Tool 7 — Video builder là một Render Graph

### 5.1 Vì sao không build FFmpeg trực tiếp trong UI

UI không nên trực tiếp xây các câu lệnh FFmpeg. Nên có ba lớp:

```
Timeline Model
  ↓
Render Planner
  ↓
FFmpeg Command / Filter Graph
```

### 5.2 Timeline Model

Mỗi clip gồm:

```json
{
  "clip_id": "clip-001",
  "asset_id": "scene-001.png",
  "start_time": 0,
  "duration": 6.5,
  "fit_mode": "cover | contain",
  "motion_preset": "ken_burns_zoom_in",
  "transition_in": "fade",
  "transition_out": "fade",
  "volume": 1.0,
  "overlay_ids": []
}
```

Audio track:

```json
{
  "voiceover": "voiceover.mp3",
  "background_music": "music.mp3",
  "voice_volume": 1.0,
  "music_volume": 0.25,
  "ducking": true,
  "fade_in": 1.0,
  "fade_out": 1.5
}
```

Subtitle track:

```json
{
  "srt_file": "subtitles.srt",
  "font": "Inter",
  "font_size": 48,
  "font_color": "#FFFFFF",
  "position": "bottom",
  "margin": 60,
  "stroke": true
}
```

Output config:

```json
{
  "width": 3840,
  "height": 2160,
  "fps": 30,
  "codec": "h264 | h265",
  "quality": "high",
  "format": "mp4"
}
```

### 5.3 Render stages

#### Normalize

- Scale.
- Pad hoặc crop.
- Chuẩn hóa FPS.
- Chuẩn hóa pixel format.
- Chuẩn hóa audio sample rate.

#### Compose

- Ảnh tĩnh dùng `zoompan`.
- Video clip dùng trim/scale.
- Scene nối bằng `xfade`.
- Overlay logo/text theo time range.

#### Audio

- Voiceover là track chính.
- Nhạc nền được giảm âm lượng.
- Sidechain ducking khi có voice.
- Fade in/out.
- `apad` để tránh audio ngắn hơn video.

#### Encode

- H.264/H.265.
- Chọn GPU encoder theo platform.
- Preset quality/speed.
- Cho phép cấu hình CRF hoặc bitrate.

#### Verify

Sau render nên chạy ffprobe:

- File có tồn tại không.
- Có video stream không.
- Có audio stream không.
- Duration.
- Resolution.
- FPS.
- Codec.
- File size hợp lệ.

### 5.4 Bug đáng chú ý

Tài liệu phát hiện các lỗi sau:

| Bug | Mức độ | Mô tả |
|---|---|---|
| `cancelRender()` | 🔴 Cao | Gọi sai process handle, không thể hủy render |
| Transition undefined | 🟡 Vừa | Biến obfuscation undefined, mọi transition ≠ "none" lỗi |
| Cookie success path | 🟡 Vừa | Dead code, thêm account bằng cookie luôn thất bại |

Bài học tổng quát: **mỗi job cần registry rõ ràng**:

```text
job_id → process handle → status → progress → cancellation state
```

Không nên dùng biến process global khó quản lý, đặc biệt khi sau này có nhiều render job hoặc nhiều cửa sổ.

---

## 6. Kiến trúc nên mượn, phần nên tránh

### 6.1 Bảng so sánh

| Điểm quan sát | Rủi ro / hạn chế | Phiên bản tốt hơn |
|---|---|---|
| Tác vụ nặng chạy đồng bộ | UI treo hoặc mất trạng thái | Job ID + queue + progress event + cancel thật |
| Tích hợp không có public API | Dễ gãy, bị chặn, rủi ro điều khoản | Ưu tiên API chính thức; adapter tách biệt; consent rõ ràng |
| File bị ghi đè sớm | Mất dữ liệu gốc, khó retry | Temp output → validate → atomic move; immutable source |
| Prompt/script không có schema | Cảnh thiếu trường, pipeline sau lỗi | JSON schema + validation + repair loop + versioning |
| Nhiều engine phụ thuộc GPU | Cài đặt khó, kết quả không ổn định | Capability probe, mock engine, fallback CPU, diagnostics |

### 6.2 Nên mượn

- IPC contract rõ theo domain thay vì một channel khổng lồ.
- Native worker cho FFmpeg/AI local, có probe và progress.
- Voice job queue với status pending/running/completed/failed.
- Account/profile/preset làm dữ liệu versioned.
- Temp directory + output manifest + retry từng stage.

### 6.3 Nên tránh hoặc thay thế

- Renderer 1 file HTML quá lớn; tách feature modules và typed state.
- Obfuscation artifact và biến undefined; bật TypeScript/lint/test.
- In-memory jobs; dùng durable local store hoặc SQLite khi cần resume.
- Cookie/token scraping và CAPTCHA automation; dùng integration chính thức.
- Xóa watermark mặc định; có consent, provenance và policy gate.

---

## 7. MVP theo thứ tự ưu tiên

Không nên bắt đầu ngay bằng Flow/CDP, token session hoặc CAPTCHA automation vì đó là phần phức tạp, dễ gãy và có rủi ro điều khoản.

### 7.1 Phase 1 — Content Core

```
Channel Profile
  ↓
Idea Brief
  ↓
Outline
  ↓
Script
  ↓
Scene Contracts
```

Tập trung vào schema, validation, versioning, review UI.

### 7.2 Phase 2 — Media Core

```
Upload Assets
  ↓
Rename / Normalize
  ↓
Timeline Editor
  ↓
FFmpeg Render
  ↓
Subtitle + Music
```

Tập trung vào progress, cancel, retry, output validation.

### 7.3 Phase 3 — Voice

```
Narration
  ↓
TTS
  ↓
Duration Measurement
  ↓
SRT
```

Có thể bắt đầu bằng mock TTS hoặc API chính thức trước khi tích hợp model local lớn.

### 7.4 Phase 4 — Research Intelligence

```
Video References
  ↓
Comments
  ↓
Clustering
  ↓
Evidence-backed Insights
  ↓
New Idea Backlog
```

### 7.5 Phase 5 — AI Asset Providers

Sau cùng mới thêm nhiều provider sinh ảnh/video, upscale nâng cao và các integration có rate limit.

---

## 8. Data contract trung gian — chìa khóa của dự án

Bài học quan trọng nhất: **thiết kế các data contract trung gian rõ ràng**.

| Contract | Vai trò |
|---|---|
| `ChannelProfile` | Định nghĩa identity kênh, inject vào mọi bước |
| `ContentInsight` | Insight từ comment + video tham chiếu, có evidence |
| `IdeaBrief` | Input cho toàn bộ script generation |
| `Script` | Output outline/script, versioned |
| `Scene` | Data contract cho từng cảnh |
| `AssetManifest` | Tracking mọi asset đã tạo |
| `Timeline` | Model cho renderer |
| `RenderJob` | Quản lý process, progress, cancel |
| `VoiceJob` | Quản lý TTS/ASR job queue |

Khi các contract này rõ ràng, có thể thay đổi:

- Claude bằng model khác.
- Flow bằng provider khác.
- XTTS bằng API TTS khác.
- FFmpeg bằng worker khác.
- Electron bằng web app hoặc desktop framework khác.

mà không phải viết lại toàn bộ hệ thống.

---

## 9. Kết luận

Giá trị lớn nhất của Ai86Studio không nằm ở một model riêng lẻ, mà ở **cách nối các representation**: channel profile, insight, scene contract, media manifest, render graph.

Các điểm cần lưu ý khi áp dụng vào dự án mới:

1. **Tách data contract khỏi provider** — provider có thể đổi, schema thì ổn định.
2. **Có approval gate trước chi phí** — tránh gọi AI generation khi brief chưa đúng.
3. **Job registry có cancel thật** — không gửi tín hiệu rồi giả định thành công.
4. **Temp output + atomic move** — bảo vệ source, cho phép retry.
5. **Capability probe cho mọi engine** — probe binary, model, GPU trước khi chạy.
6. **Versioned preset** — channel profile, voice preset, theme pack đều có version.
7. **Evidence-backed insights** — không để AI tự bịa insight ngoài comment gốc.
8. **Dùng API chính thức** — tránh sniff token, CAPTCHA automation, cookie decrypt.
9. **Consent trên cleanup** — watermark/upscale chỉ chạy khi có quyền.
10. **Output manifest** — mỗi step đều ghi lại input/output/parameters/status.

---

*Tài liệu tham chiếu: `docs/PIPELINE-ANALYSIS.md` — phân tích source deobfuscate, ngày 07/08/2026.*
