# KẾ HOẠCH MAP TÍNH NĂNG "TTS VOICE STUDIO" BẢN HOÀN CHỈNH (SPA)

## 1. Tóm tắt vấn đề (Problem Statement)
Ở phiên bản trước, chúng ta mới chỉ đắp giao diện xịn cho tính năng "Tạo giọng nói" (Voice Design & TTS) mà bỏ quên các tính năng cốt lõi khác từ repo gốc `E:\omnivoice-api-server`. Sếp đã tinh ý nhận ra việc thiếu sót các tính năng này ở Sidebar.

Nhiệm vụ: Cấu trúc lại giao diện thành mô hình **Single Page Application (SPA)**, map chuẩn xác 4 menu ở Sidebar tương ứng với 4 tính năng cũ nhưng phải mặc "áo mới" Premium.

## 2. Bản đồ Mapping Tính năng (Feature Mapping)
1. **✨ Tạo giọng nói (tab-tts):** 
   - *Gốc:* Tab "Thiết kế giọng" + Form nhập liệu chính.
   - *Mới:* Chứa khung gõ chữ, chèn Tag Emotion, chọn Mode (Auto/Preset/Design/Clone), kéo tốc độ và Sinh Audio.
2. **👤 Nhân bản giọng nói (tab-clone):**
   - *Gốc:* Tab "Clone giọng mẫu".
   - *Mới:* Chứa form Tải lên file Audio (wav, mp3), chọn file có sẵn và lưu thành VoiceID mới vào Registry.
3. **🎙️ Đa giọng (tab-registry):**
   - *Gốc:* Tab "Quản lý giọng".
   - *Mới:* Hiển thị bảng (Table) danh sách các VoiceID đã lưu. Cho phép Sửa tên, Đổi ID, Xóa trực tiếp trên giao diện cao cấp.
4. **⚙️ Profile (tab-profile):**
   - *Gốc:* Tab "API cho App khác".
   - *Mới:* Hiển thị thông số Server Endpoint, tích hợp Code Snippets (Python, JS, cURL) để lập trình viên copy paste.

## 3. Kiến trúc Frontend (Cập nhật)
- HTML sẽ chứa 4 div `view-panel` ẩn/hiện tương ứng với Menu được click.
- CSS sẽ bổ sung các class cho form Tải file, Bảng (Table) Quản lý giọng, và Khối Code Snippets. Đảm bảo mọi thứ đều áp dụng chuẩn Dark Theme, Glassmorphism.
- JS sẽ port (chuyển) nguyên xi các hàm từ bản gốc (`saveCloneToRegistry`, `loadVoiceRegistry`, `loadApiTab`, v.v.) vào cấu trúc mới.

Mọi thứ sẽ được gom vào `app/templates/index.html` để Tầng 2 thực thi gọn gàng trong 1 nốt nhạc.
