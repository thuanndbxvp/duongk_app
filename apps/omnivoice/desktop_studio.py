import os
import sys
import time
import socket
import threading
import uvicorn
import webview
import requests

# Import app from main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.main import app as fastapi_app

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def run_server(port):
    """Chạy FastAPI server trên port chỉ định"""
    uvicorn.run(fastapi_app, host="127.0.0.1", port=port, log_level="warning")

def check_server_ready(port):
    """Ping health check để đảm bảo server đã sẵn sàng trước khi mở UI"""
    url = f"http://127.0.0.1:{port}/health"
    for _ in range(30): # Đợi tối đa 15s
        try:
            res = requests.get(url, timeout=1)
            if res.status_code == 200:
                return True
        except requests.ConnectionError:
            pass
        time.sleep(0.5)
    return False

if __name__ == '__main__':
    # Bỏ qua warning không cần thiết
    os.environ["WEBVIEW_EDGE_CHROMIUM"] = "1"
    
    # Lấy port tĩnh hoặc động
    PORT = int(os.getenv("PORT", 8088))
    
    print(f"[*] Đang khởi động TTS Voice Studio Server ngầm tại cổng {PORT}...")
    server_thread = threading.Thread(target=run_server, args=(PORT,), daemon=True)
    server_thread.start()
    
    print("[*] Đang chờ server nạp Model (có thể mất vài giây)...")
    if not check_server_ready(PORT):
        print("[!] Không thể kết nối đến server ngầm. Thoát ứng dụng.")
        sys.exit(1)
        
    print("[*] Server đã sẵn sàng. Khởi tạo Desktop Window...")
    # Tạo cửa sổ Desktop (Engine Edge WebView2 trên Windows)
    window = webview.create_window(
        title='TTS Voice Studio',
        url=f'http://127.0.0.1:{PORT}/',
        width=1280,
        height=800,
        min_size=(1024, 768),
        background_color='#0b0c10' # Trùng màu nền của CSS để ko bị nháy trắng
    )
    
    # Khởi chạy GUI loop
    webview.start(private_mode=False)
    
    print("[*] Đã đóng cửa sổ. Đang dọn dẹp và thoát server...")
    os._exit(0) # Đảm bảo force kill mọi thread ngầm tránh lỗi file lock
