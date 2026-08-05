Đây là một tính năng vô cùng cốt lõi trong quy trình Nghiên cứu Thị trường & Validate Ngách (Market Research & Demand Validation). Ý tưởng trong ảnh của bạn rất rõ ràng: Tránh việc người dùng lao vào làm một chủ đề "chết" hoặc không đủ dung lượng thị trường bằng cách bắt buộc ngách đó phải đạt ngưỡng > 5.7 triệu view/tháng, sau đó mới bóc tách Top 10 kênh lớn nhất.Dưới đây là thiết kế kiến trúc kỹ thuật chi tiết để backend Python (FastAPI/Worker) của bạn thực thi quy trình này một cách tự động, chính xác và tiết kiệm API Quota nhất.Quy trình xử lý kỹ thuật (4 Bước)[Nhập Từ khóa] ➔ [1. Search Video Top] ➔ [2. Tính Tổng View Tháng] ➔ [3. Lọc & Lấy thông tin Kênh] ➔ [4. Top 10 Output]
Bước 1: Tìm kiếm các Video thuộc Chủ đề (Keyword Search)Khi người dùng gõ từ khóa (ví dụ: Personal Finance hoặc 3D Animation):API gọi: Sử dụng search.list của YouTube Data API v3 (hoặc cào dữ liệu qua RapidAPI / Apify để tiết kiệm quota).Tham số lọc:q: {Từ khóa}type: videopublishedAfter: Ngày hiện tại trừ đi 30 ngày (Chỉ lấy video đăng trong 1 tháng gần nhất).maxResults: 50 - 100 video.Mục tiêu: Thu thập danh sách các videoId và channelId đang tạo ra lưu lượng truy cập cho từ khóa này trong 30 ngày qua.Bước 2: Đo lường tổng Lượt xem Quốc tế hàng tháng (> 5.7 triệu view)Đây là bước tính toán điều kiện Đo lường (Validation Gate):Gộp request: Lấy danh sách 50-100 videoId thu được từ Bước 1, gửi 1 request duy nhất tới endpoint videos.list (truyền id=id1,id2,id3... và part=statistics,snippet).Thu thập View & Quốc gia:Cộng tổng lượt xem (viewCount) của toàn bộ các video xuất bản trong 30 ngày qua liên quan đến từ khóa đó.(Mẹo quốc tế): Kiểm tra ngôn ngữ tiêu đề/mô tả (defaultLanguage hoặc defaultAudioLanguage) để đảm bảo dữ liệu tính trên thị trường quốc tế (Tiếng Anh, v.v.).Điều kiện rẽ nhánh:Nếu $\text{Tổng View trong 30 ngày} < 5,700,000$: Trả về cảnh báo cho User: "Chủ đề này có dung lượng thị trường nhỏ (dưới 5.7M view/tháng), không đề xuất đầu tư làm."Nếu $\text{Tổng View trong 30 ngày} \ge 5,700,000$: Đạt điều kiện, chuyển sang Bước 3.Bước 3: Thu thập thông tin Kênh & Sắp xếp theo SubTừ danh sách channelId độc nhất (unique) thu thập được ở Bước 1:Gộp request lấy chỉ số Kênh: Gửi 1 request duy nhất tới endpoint channels.list (truyền danh sách channelId thu được, part=statistics,snippet).Lấy số liệu: Lấy số lượng người đăng ký (subscriberCount) của từng kênh.Sắp xếp (Sorting): Sắp xếp danh sách kênh theo thứ tự subscriberCount giảm dần (từ lớn đến bé).Cắt kết quả: Lấy ra Top 10 kênh đầu bảng.Luồng code tham khảo (Python / FastAPI Logic)Pythonfrom datetime import datetime, timedelta, timezone

def validate_and_find_top_channels(keyword: str):
    # 1. Tính thời gian 30 ngày trước
    one_month_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    
    # 2. Search Top 50 video liên quan trong 30 ngày qua
    search_response = youtube.search().list(
        q=keyword,
        type="video",
        part="snippet",
        publishedAfter=one_month_ago,
        maxResults=50
    ).execute()
    
    video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
    
    # 3. Lấy chi tiết View của các video này (1 request duy nhất)
    videos_response = youtube.videos().list(
        id=",".join(video_ids),
        part="statistics,snippet"
    ).execute()
    
    total_monthly_views = 0
    channel_ids = set()
    
    for item in videos_response.get('items', []):
        views = int(item['statistics'].get('viewCount', 0))
        total_monthly_views += views
        channel_ids.add(item['snippet']['channelId'])
        
    # 4. Kiểm tra điều kiện 5.7 Triệu View
    if total_monthly_views < 5_700_000:
        return {
            "is_viable": False,
            "total_monthly_views": total_monthly_views,
            "message": "Chủ đề chưa đủ độ hot (< 5.7M view/tháng)."
        }
        
    # 5. Lấy thông tin Subscriber của danh sách kênh tìm được
    channels_response = youtube.channels().list(
        id=",".join(list(channel_ids)[:50]), # Giới hạn 50 channels
        part="statistics,snippet"
    ).execute()
    
    channels_data = []
    for item in channels_response.get('items', []):
        channels_data.append({
            "channel_id": item['id'],
            "title": item['snippet']['title'],
            "subscribers": int(item['statistics'].get('subscriberCount', 0)),
            "total_views": int(item['statistics'].get('viewCount', 0)),
            "custom_url": item['snippet'].get('customUrl', '')
        })
        
    # 6. Sắp xếp theo Sub giảm dần và lấy Top 10
    top_10_channels = sorted(channels_data, key=lambda x: x['subscribers'], reverse=True)[:10]
    
    return {
        "is_viable": True,
        "total_monthly_views": total_monthly_views,
        "top_channels": top_10_channels
    }
Lưu ý quan trọng để tối ưu Performance & Chi phíSử dụng Caching (Redis): Dữ liệu lượt xem của một từ khóa chủ đề không thay đổi liên tục theo từng giây. Bạn nên lưu kết quả tìm kiếm theo keyword vào Redis với thời gian hết hạn (TTL) khoảng 24 giờ đến 3 ngày. Khi người dùng khác gõ lại cùng từ khóa đó, kết quả sẽ trả về ngay lập tức (0.1 giây) mà không tốn 1 đơn vị API Quota nào.Xử lý kênh ẩn Sub: Một số kênh YouTube cài đặt ẩn số lượng người đăng ký. Trình mã hóa của bạn cần có điều kiện try/except gán giá trị mặc định bằng 0 để tránh làm vỡ luồng sắp xếp (sort).