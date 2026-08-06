Tôi đã khảo sát code thực tế ở D:\appDK, tập trung vào các entry point, worker, database schema, màn hình dashboard, ý tưởng, script, scene breakdown và OmniVoice.

Kết luận chính:

appDK hiện là nền tảng phân tích kênh YouTube + sinh ý tưởng + viết script + chia scene + TTS.
Nó chưa phải là công cụ tạo video hoàn chỉnh như Ai86Studio vì chưa có asset management, video composition, FFmpeg render và export.

Điều này lại rất phù hợp với ý tưởng mới của bạn, vì appDK đã có phần Content Intelligence Core, còn cần xây thêm Production Core.

1. appDK hiện đang làm tốt phần nào?
1.1 Kiến trúc nền tảng
Stack hiện tại:

Frontend: Next.js 16 + React 19 + Tailwind CSS.
Backend: FastAPI.
Worker: Celery + Redis.
Database: Supabase PostgreSQL.
TTS: OmniVoice + Modal Cloud.
Storage: Cloudflare R2.
AI text: OpenAI.
Embeddings: Cohere.
Monitoring: Sentry.
Các entry point chính:

Web: D:\appDK\apps\web\app\page.tsx
API: D:\appDK\apps\api\main.py
Worker: D:\appDK\apps\worker\celery_app.py
OmniVoice: D:\appDK\apps\omnivoice\app\main.py
Về mặt hạ tầng, appDK đã có nền tảng khá tốt cho một ứng dụng production:

Background jobs.
Queue phân loại theo workload.
Progress tracking.
Credit system.
Supabase RLS.
Retry task.
TTS service riêng.
RAG pipeline.
Test unit/integration/e2e.
1.2 Pipeline hiện tại
Luồng hiện tại của appDK gần như là:

User nhập URL kênh YouTube.
App thu thập dữ liệu và transcript.
App phân tích DNA của kênh.
App sinh ý tưởng dựa trên gap analysis.
App sinh script dựa trên RAG.
App validate script bằng Anti-Slop.
App chia script thành các scene.
App tạo voice bằng OmniVoice.
Nhưng pipeline dừng ở bước voice/scene. Chưa có:

Tạo hoặc tìm hình ảnh/video cho từng scene.
Quản lý asset.
Timeline editor thực sự.
Ghép voice với media.
Subtitle rendering.
Background music.
FFmpeg render.
Video preview/export.
Thumbnail generation.
Publish workflow.
2. Điểm không phù hợp với mục tiêu “từ tay trắng”
Hiện tại onboarding của appDK bắt đầu bằng việc user nhập URL kênh YouTube tại:

D:\appDK\apps\web\app\(dashboard)\projects\new\page.tsx

Flow hiện tại có tinh thần:

Dán URL kênh YouTube → phân tích DNA → bắt chước phong cách → sinh script.

Điều đó phù hợp với sản phẩm “channel cloning” hoặc “AI script generator”, nhưng chưa phù hợp với user muốn:

Tôi chưa có kênh, chưa có nội dung, chưa có asset, chỉ có một ý tưởng và muốn tạo video hoàn chỉnh.

Vì vậy, app mới nên hỗ trợ hai chế độ khởi tạo dự án:

Chế độ A — Blank Project
Dành cho user bắt đầu từ tay trắng:

Nhập topic.
Chọn ngôn ngữ.
Chọn loại video.
Chọn thời lượng.
Chọn tone.
Chọn giọng đọc.
Chọn style hình ảnh.
Chọn tỉ lệ video.
Chế độ B — Clone / Learn from Channel
Dành cho user có kênh tham chiếu:

Nhập URL kênh.
Phân tích transcript.
Phân tích hook.
Phân tích cấu trúc.
Phân tích cách dùng ngôn ngữ.
Tạo channel DNA.
Dùng DNA đó cho script và visual prompt.
Hai chế độ này nên dùng chung phần Content Core phía sau, chỉ khác nguồn đầu vào.

3. Sản phẩm nên định vị như thế nào?
Không nên định vị app mới chỉ là:

AI viết script YouTube.

Mà nên định vị là:

Một workspace giúp người dùng biến một ý tưởng thô thành video hoàn chỉnh, kể cả khi họ chưa có kênh, chưa có footage và chưa biết dựng video.

Luồng trải nghiệm nên là:

Tôi muốn làm video về gì?
Video dành cho ai?
Phong cách kể chuyện là gì?
AI đề xuất concept và outline.
AI viết script.
AI chia script thành scene.
AI tạo hoặc tìm asset cho từng scene.
AI tạo voice và subtitle.
AI tự dựng video.
User xem preview và chỉnh sửa.
Export video, thumbnail, title và description.
Tên gọi phù hợp về mặt sản phẩm có thể là:

Zero-to-Video Studio.
AI Video Workspace.
Faceless Video Factory.
AI Creator Studio.
One Idea to Video.
4. Những phần trong appDK có thể tái sử dụng
4.1 RAG và Channel DNA
Đây là một trong những phần mạnh nhất của appDK.

Script generation hiện dùng:

Channel persona.
RAG retrieval.
DNA chunks.
Prompt builder.
LLM routing.
Anti-Slop validation.
File liên quan:

D:\appDK\apps\worker\tasks\script_generate.py
D:\appDK\apps\worker\services\rag_service.py
D:\appDK\apps\worker\services\antislop_service.py
Phần này nên giữ lại, nhưng mở rộng để hỗ trợ cả hai nguồn:

Với Blank Project
Không có channel DNA thì dùng:

Genre preset.
Audience profile.
Tone preset.
Visual style preset.
Writing framework.
User instructions.
Với Clone Channel
Dùng:

Transcript.
Hook patterns.
Sentence rhythm.
Structural formula.
Signature phrases.
Emotional signature.
Thumbnail analysis.
Comment insights.
Như vậy AI không bị phụ thuộc vào việc user phải có sẵn một channel để bắt đầu.

4.2 Idea generation
File:

D:\appDK\apps\worker\services\idea_generator.py
D:\appDK\apps\worker\tasks\idea_generate.py
Các phần có thể giữ:

Topic clustering.
Gap score.
Confidence level.
Opportunity description.
Lưu idea vào database.
Sắp xếp theo cơ hội.
Nhưng hiện tại có một vấn đề quan trọng: trong idea_generate.py, trending score đang được hardcode:

trending_score = 50.0
Nghĩa là tính năng gap analysis hiện chưa hoàn toàn dựa trên dữ liệu xu hướng thật. Khi xây sản phẩm mới, cần tách rõ:

TrendProvider.
YouTubeProvider.
SearchProvider.
CommentProvider.
IdeaScoringService.
Sau này có thể thay Google Trends, SerpAPI, YouTube Data API hoặc provider khác mà không sửa business logic.

4.3 Script generation
File:

D:\appDK\apps\worker\tasks\script_generate.py
Phần này có một pipeline khá tốt:

Lấy channel persona.
RAG retrieve context.
Xây prompt.
Gọi LLM.
Parse JSON.
Validate Anti-Slop.
Retry nếu chưa đạt score.
Lưu cost và attempts.
Cập nhật job progress.
Đây là nền tảng tốt để xây Script Studio.

Tuy nhiên, script hiện tại vẫn thiên về dạng:

title
hook
body
cta
Trong dự án video hoàn chỉnh, nên mở rộng thành:

Project brief.
Audience.
Promise.
Outline.
Full narration.
Chapters.
Scene contracts.
Estimated duration.
Visual prompts.
Voice direction.
Subtitle lines.
Asset requirements.
4.4 Scene breakdown
File:

D:\appDK\apps\worker\services\scene_breaker.py
D:\appDK\apps\worker\tasks\scene_breakdown.py
D:\appDK\apps\web\components\scene-timeline.tsx
Hiện tại scene breaker làm được:

Chia script theo paragraph.
Tính thời lượng theo WPM.
Tạo start time và end time.
Đếm số từ.
Trích xuất một số keyword B-roll.
Dịch keyword tiếng Việt sang tiếng Anh.
Tạo Pexels search query.
Đây là một nền tảng tốt cho việc tạo video, nhưng vẫn chưa đủ để render.

Hiện tại scene chỉ tương đối giống:

Scene
  - scene_number
  - start_time
  - end_time
  - duration_seconds
  - text
  - broll_keywords
  - broll_translations
Cần mở rộng thành scene contract có thể sản xuất được:

Scene
  - scene_id
  - narration
  - visual_description
  - image_prompt
  - video_prompt
  - asset_type
  - asset_source
  - asset_ids
  - duration
  - camera_motion
  - transition
  - subtitle_range
  - voice_line_id
  - status
Hiện tại SceneTimeline chủ yếu chỉ hiển thị scene. Nó chưa có:

Chỉnh sửa scene.
Gán asset.
Upload asset.
Chọn stock footage.
Generate image.
Preview media.
Thay đổi duration.
Chọn transition.
Reorder scene.
Save scene changes.
5. Điểm cần chú ý trong UI hiện tại
5.1 Script editor chưa phải editor thực sự
Trong:

D:\appDK\apps\web\app\(dashboard)\scripts\[id]\page.tsx

các textarea đang hiển thị nội dung script nhưng chưa có state update hoặc API save rõ ràng.

Ví dụ:

<textarea
  value={script.script.hook}
  ...
/>
Có value, nhưng không có onChange.

Điều này có nghĩa là user chưa thể thực sự sửa nội dung trực tiếp trong UI.

Đối với app mới, mọi vùng editable cần có:

Local draft state.
Dirty state.
Autosave hoặc nút Save.
Version.
Undo/redo cơ bản.
Error khi save thất bại.
Khả năng khôi phục bản trước.
5.2 Scene timeline mới là danh sách, chưa phải timeline editor
SceneTimeline hiện hiển thị các scene theo dạng card dọc. Đây là scene list, chưa phải timeline dựng video.

Cần tiến hóa theo các cấp:

Cấp 1 — Scene board
Danh sách scene.
Nội dung narration.
Thời lượng.
Visual prompt.
Asset placeholder.
Status.
Cấp 2 — Asset assignment
Upload image/video.
Tìm Pexels.
Generate image.
Chọn asset từ library.
Preview asset.
Cấp 3 — Timeline editor
Kéo thả scene.
Điều chỉnh duration.
Chọn transition.
Chọn motion effect.
Chọn subtitle style.
Chọn audio track.
Cấp 4 — Preview/render
Preview từng scene.
Preview toàn video.
Render draft low-resolution.
Render final.
Cancel/retry render.
6. Kiến trúc sản phẩm mới nên gồm 5 lớp
Layer 1 — Project and Creative Brief
Đây là nơi user bắt đầu từ tay trắng.

Project nên có:

Project name.
Topic.
Goal.
Audience.
Language.
Duration.
Aspect ratio.
Content type.
Tone.
Visual style.
Voice profile.
Music mood.
Channel profile tùy chọn.
Điểm quan trọng là Channel Profile phải là tùy chọn, không được bắt buộc.

Layer 2 — Planning and Intelligence
Bao gồm:

Idea generator.
Research.
Competitor analysis.
Comment intelligence.
Outline generator.
Script generator.
Scene planner.
Prompt builder.
Validation.
Các worker hiện tại của appDK có thể làm nền móng cho layer này.

Layer 3 — Asset Production
Đây là phần appDK gần như chưa có và cần xây mới.

Mỗi scene có thể lấy asset từ:

AI image provider.
AI video provider.
Pexels.
Unsplash.
User upload.
Asset library.
Generated previous assets.
Nên có abstraction:

AssetProvider
  - search()
  - generate()
  - upload()
  - download()
  - get_metadata()
  - delete()
Không nên để scene worker biết trực tiếp chi tiết của Pexels, Gemini, Flow hoặc provider cụ thể.

Layer 4 — Voice and Audio
Phần OmniVoice hiện tại có thể tái sử dụng.

Cần xây thêm:

Voice profile selector.
Voice preview.
Voice cloning sample.
TTS theo từng scene.
Regenerate riêng một scene.
Duration thật sau khi TTS.
SRT generation.
Background music.
Sound effects.
Audio ducking.
Một vấn đề quan trọng:

Thời lượng scene ban đầu được ước tính theo WPM, nhưng sau TTS phải cập nhật theo duration thật của audio.

Luồng đúng hơn:

Estimated duration
    ↓
TTS per scene
    ↓
Actual audio duration
    ↓
Recalculate timeline
    ↓
Render
Layer 5 — Composition and Export
Cần xây mới:

Timeline model.
Render planner.
FFmpeg worker.
Preview render.
Final render.
Output validation.
Export MP4.
Export SRT.
Export audio.
Export thumbnail.
Export metadata package.
7. Data model nên mở rộng
AppDK đã có:

users
jobs
channel_assistants
channel_deep_analysis
generated_ideas
generated_scripts
dna_chunks
voice_profiles
transcripts
credit_transactions
Để trở thành hệ thống tạo video từ đầu đến cuối, nên bổ sung các entity sau.

7.1 Projects
Project là root entity của toàn bộ quy trình.

Các trường chính:

id
user_id
name
mode: blank | clone_channel
topic
language
audience
duration_target
aspect_ratio
status
current_stage
created_at
updated_at
7.2 Project profiles
Có thể liên kết project với channel profile:

id
project_id
channel_assistant_id nullable
tone
visual_style
voice_profile_id
music_style
content_constraints
Nếu là Blank Project, channel_assistant_id có thể null.

7.3 Content plans
id
project_id
version
brief
outline
approval_status
approved_at
created_at
7.4 Scenes
Không nên chỉ lưu toàn bộ scenes trong generated_scripts.scenes JSONB khi pipeline bắt đầu phức tạp.

Có thể giữ JSONB trong MVP, nhưng về sau nên có bảng project_scenes:

id
project_id
scene_index
narration
visual_description
image_prompt
video_prompt
duration_estimated
duration_actual
status
metadata
7.5 Assets
id
project_id
scene_id
type: image | video | audio | subtitle
source: upload | stock | ai_generated
provider
storage_key
mime_type
width
height
duration
status
metadata
7.6 Timeline
id
project_id
version
timeline_json
status
created_at
7.7 Render jobs
Có thể tái sử dụng jobs, nhưng nên thêm:

job_type
project_id
process_id
cancel_requested
output_path
error_code
retry_count
8. Luồng “từ tay trắng” được khuyến nghị
Bước 1 — User tạo project
User không cần URL kênh.

Chỉ cần nhập:

“Tôi muốn làm video về lịch sử Ai Cập”.
Thời lượng: 8 phút.
Ngôn ngữ: tiếng Việt.
Phong cách: documentary cinematic.
Giọng: nam trầm.
Tỉ lệ: 16:9.
Bước 2 — AI làm rõ brief
AI hỏi hoặc tự đề xuất:

Khán giả là ai?
Video giáo dục hay giải trí?
Có muốn dùng footage thực tế hay hình AI?
Mức độ chuyên sâu?
Có cần CTA không?
Bước 3 — AI đề xuất concept
Ví dụ:

5 title.
3 angle.
3 hook.
1 recommended outline.
Điểm mạnh/yếu của từng concept.
User chọn một concept.

Bước 4 — AI viết script
Output gồm:

Title.
Hook.
Body.
CTA.
Chapter.
Estimated duration.
Bước 5 — AI chia scene
Mỗi scene có:

Narration.
Visual description.
Image/video prompt.
Asset type.
Estimated duration.
Suggested transition.
B-roll query.
Bước 6 — User duyệt scene plan
User có thể:

Sửa narration.
Sửa prompt.
Gộp scene.
Tách scene.
Bỏ scene.
Đổi asset type.
Generate lại từng scene.
Bước 7 — Tạo assets
Mỗi scene cho phép:

Generate AI image.
Generate AI video.
Search stock.
Upload file.
Chọn asset có sẵn.
Bước 8 — Tạo voice và subtitle
TTS từng scene.
Cập nhật duration thật.
Sinh SRT.
Cho phép regenerate riêng từng câu.
Bước 9 — Dựng preview
Render bản nháp thấp trước:

720p.
Watermark nội bộ của app nếu cần.
Encode nhanh.
Preview toàn bộ pipeline.
Bước 10 — User chỉnh timeline
Đổi thứ tự scene.
Điều chỉnh thời lượng.
Chọn Ken Burns.
Chọn transition.
Đổi nhạc.
Chỉnh subtitle.
Chỉnh volume.
Bước 11 — Final export
Xuất:

MP4.
SRT.
Voiceover.
Thumbnail.
Title.
Description.
Tags.
Project manifest.
9. Định hướng MVP thực tế
Tôi đề xuất không bắt đầu bằng toàn bộ tính năng của Ai86Studio. MVP nên có các phần sau:

Phase 1 — Blank Project Content Core
Tái sử dụng:

Script generation.
Scene breakdown.
Progress tracking.
Job system.
OmniVoice.
Bổ sung:

Blank Project onboarding.
Project entity.
Brief schema.
Outline approval.
Scene schema chuẩn.
Scene editor có save.
Phase 2 — Asset Management
Xây mới:

Upload asset.
Storage R2.
Asset library.
Gán asset vào scene.
Preview image/video.
Asset metadata.
Retry upload/download.
Phase 3 — Stock Search
Tích hợp provider chính thức:

Pexels.
Unsplash.
Pixabay hoặc provider tương tự.
Mỗi kết quả nên lưu:

Provider.
Original URL.
Author.
License metadata.
Download URL.
Local/R2 storage key.
Phase 4 — FFmpeg Render
Xây:

Timeline JSON.
FFmpeg planner.
Scene composition.
Subtitle overlay.
Voice + music mixing.
Progress.
Cancel.
Preview render.
Final render.
ffprobe validation.
Phase 5 — AI Media Generation
Sau khi pipeline render chạy ổn mới thêm:

AI image.
AI video.
Upscale.
Background removal.
Các provider khác.
Lợi ích của thứ tự này là bạn có thể tạo video hoàn chỉnh ngay cả khi AI media provider bị lỗi hoặc hết quota.

10. Ưu tiên kỹ thuật
P0 — Bắt buộc
Project model.
Blank Project onboarding.
Asset model.
Scene contract.
Upload/storage.
FFmpeg render.
Preview/export.
TTS gắn với scene.
Actual audio duration.
Job cancellation thật.
P1 — Rất quan trọng
Stock footage.
AI image generation.
Timeline editing.
Auto subtitle.
Background music.
Thumbnail.
Video metadata.
P2 — Tăng sức mạnh sản phẩm
Comment intelligence.
Channel cloning.
RAG style DNA.
Content calendar.
Multi-channel profiles.
Batch video generation.
Cost estimation.
Provider fallback.
P3 — Nâng cao
AI video generation.
Character consistency.
Automatic scene quality scoring.
A/B thumbnail.
Publish trực tiếp lên YouTube.
Analytics feedback loop.
Kết luận
appDK là nền móng rất tốt cho phần:

Phân tích nội dung.
Sinh ý tưởng.
RAG.
Sinh script.
Chia scene.
TTS.
Background jobs.
Progress tracking.
Credits.
Multi-service architecture.
Nhưng để phục vụ mục tiêu “người dùng có thể tạo video từ tay trắng”, cần chuyển trọng tâm từ:

Channel URL → Channel DNA → Script

sang:

Blank Project → Brief → Script → Scenes → Assets → Voice → Timeline → Render → Export

Điểm cần xây đầu tiên không phải AI video generation mà là:

Project.
Scene.
Asset.
Timeline.
RenderJob.
Khi 5 thành phần này tồn tại, các tính năng AI, Pexels, OmniVoice, RAG và channel analysis sẽ có chỗ để kết nối vào một sản phẩm hoàn chỉnh.