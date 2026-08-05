Hạn mức 10.000 đơn vị/ngày có thể gánh được khối lượng công việc khổng lồ, đủ cho hàng ngàn người dùng nếu bạn biết cách tối ưu API Endpoint thay vì dùng sai cách như 90% các lập trình viên mới làm quen.
Dưới đây là cách giải quyết bài toán giới hạn này cho hệ thống SaaS của bạn:
Bí quyết tối ưu: Đừng bao giờ dùng Search Hầu hết mọi người cạn kiệt 10.000 quota chỉ trong vài chục phút vì họ sử dụng endpoint search.list để tìm video của một kênh.
Chi phí của search.list: 100 quota / 1 request. (10.000 quota chỉ cào được 100 lần là sập).
Cách làm "chính đạo" siêu tiết kiệm: Trong kiến trúc hạ tầng web của bạn, hãy cấu hình backend đi theo luồng 3 bước sau:
Gọi channels.list (Chi phí: 1 quota): Truyền URL kênh vào để lấy channel_id và ID của danh sách phát (playlist) có tên là uploads (chứa toàn bộ video của kênh).
Gọi playlistItems.list (Chi phí: 1 quota): Truyền ID playlist uploads vào, bạn sẽ lấy được danh sách 50 video mới nhất cùng lúc.
Gọi videos.list (Chi phí: 1 quota): Truyền 50 video_id vừa lấy được (cách nhau bằng dấu phẩy) vào endpoint này để lấy toàn bộ chỉ số chi tiết (view, like, comment) cho 50 video đó trong chỉ 1 request duy nhất.
Kết quả: Để bóc tách và tìm ra video Viral nhất trong 50 video gần nhất của một kênh, bạn chỉ tốn vỏn vẹn 3 quota. => Với 10.000 quota miễn phí, hệ thống của bạn có thể phân tích được hơn 3.300 kênh mỗi ngày.