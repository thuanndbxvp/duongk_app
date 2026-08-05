# MICRO-STEP EXECUTION WORKFLOW (MSEW) - Mapping Full Tính Năng

## Bước 1: Ghi đè file `index.html` với cấu trúc SPA Đầy đủ 4 Tính năng
**File mục tiêu:** `app/templates/index.html`
**Lệnh cho Tầng 2:** Copy và GHI ĐÈ toàn bộ file `index.html` bằng đoạn code khổng lồ dưới đây. Tôi đã tích hợp toàn bộ API cũ (Upload, Registry, Snippets) vào đúng 4 Menu Sidebar với CSS cực mượt.

```html
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TTS Voice Studio</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-body: #0b0f19; --bg-sidebar: #111827; --bg-card: #1f2937; --bg-input: #111827;
            --border-color: #374151; --text-main: #f9fafb; --text-muted: #9ca3af;
            --accent-blue: #3b82f6; --accent-blue-hover: #2563eb; --accent-green: #10b981; --danger: #ef4444;
            --radius-md: 8px; --radius-lg: 12px;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', sans-serif; }
        body { background-color: var(--bg-body); color: var(--text-main); height: 100vh; overflow: hidden; display: flex; }
        ::-webkit-scrollbar { width: 6px; height: 6px;} ::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 10px; }

        .app-container { display: grid; grid-template-columns: 260px 1fr; width: 100%; height: 100%; }

        /* SIDEBAR */
        .sidebar { background-color: var(--bg-sidebar); border-right: 1px solid var(--border-color); display: flex; flex-direction: column; padding: 20px; z-index: 10;}
        .logo { font-size: 1.2rem; font-weight: 700; color: white; margin-bottom: 30px; display: flex; align-items: center; gap: 10px; }
        .logo-box { width: 24px; height: 24px; background-color: var(--accent-blue); border-radius: 6px; }
        .nav-item { padding: 12px 16px; margin-bottom: 8px; border-radius: var(--radius-md); color: var(--text-muted); cursor: pointer; font-weight: 500; font-size: 0.95rem; transition: 0.2s; }
        .nav-item:hover { background-color: rgba(255,255,255,0.05); color: var(--text-main); }
        .nav-item.active { background-color: rgba(59, 130, 246, 0.15); color: var(--accent-blue); }

        /* MAIN CONTENT AREA */
        .main-wrapper { display: flex; flex-direction: column; height: 100%; background-color: var(--bg-body); overflow: hidden;}
        .topbar { height: 64px; min-height: 64px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: flex-end; align-items: center; padding: 0 24px; gap: 16px; background-color: var(--bg-sidebar);}
        .user-profile { display: flex; align-items: center; gap: 10px; font-size: 0.9rem; font-weight: 500; }
        .avatar { width: 32px; height: 32px; background-color: #fff; border-radius: 50%; color: #000; display: flex; justify-content: center; align-items: center; font-weight: bold; }
        
        .view-panel { display: none; height: 100%; overflow: hidden; }
        .view-panel.active { display: flex; }

        /* LAYOUT CHO VIEW TTS (3 Cột cũ) */
        .tts-layout { display: grid; grid-template-columns: 1fr 380px; height: 100%; width: 100%; }
        .center-content { overflow-y: auto; padding: 30px; }
        .right-panel { background-color: var(--bg-sidebar); border-left: 1px solid var(--border-color); padding: 30px 24px; display: flex; flex-direction: column; overflow-y: auto;}
        
        /* LAYOUT CHO CÁC VIEW CÒN LẠI (1 Cột rộng) */
        .single-layout { padding: 30px; overflow-y: auto; width: 100%; max-width: 1200px; margin: 0 auto;}

        /* SHARED COMPONENTS */
        .page-title { font-size: 1.5rem; font-weight: 700; margin-bottom: 6px; }
        .page-desc { color: var(--text-muted); font-size: 0.95rem; margin-bottom: 24px;}
        .card { background-color: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-lg); padding: 24px; margin-bottom: 24px; }
        .form-label { display: block; font-size: 0.95rem; font-weight: 600; margin-bottom: 12px; color: var(--text-main); }
        .text-input, .select-input { width: 100%; background-color: var(--bg-input); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 12px 16px; color: var(--text-main); font-size: 0.95rem; outline: none; }
        .text-input:focus, .select-input:focus { border-color: var(--accent-blue); }
        .btn-blue { background-color: var(--accent-blue); color: white; border: none; padding: 12px 20px; border-radius: var(--radius-md); font-weight: 600; cursor: pointer; }
        .btn-blue:hover { background-color: var(--accent-blue-hover); }

        /* TABLE & SNIPPETS */
        .registry-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
        .registry-table th { text-align: left; padding: 12px; border-bottom: 1px solid var(--border-color); color: var(--text-muted); }
        .registry-table td { padding: 12px; border-bottom: 1px solid var(--border-color); }
        .snippet-box { background: #000; padding: 16px; border-radius: var(--radius-md); font-family: monospace; font-size: 0.85rem; color: #a5b4fc; white-space: pre-wrap; margin-bottom: 16px;}
        
        /* EMOTIONS (Từ code cũ) */
        .emotion-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .emotion-btn { background-color: var(--bg-input); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 10px; cursor: pointer; }
        .emotion-title { display: block; font-weight: 600; font-size: 0.9rem;} .emotion-sub { font-size: 0.75rem; color: var(--text-muted); }
    </style>
</head>
<body>

<div class="app-container">
    <!-- SIDEBAR -->
    <div class="sidebar">
        <div class="logo"><div class="logo-box"></div> TTS Voice Studio</div>
        <div class="nav-item active" onclick="switchNav('tts', this)">✨ Tạo giọng nói</div>
        <div class="nav-item" onclick="switchNav('clone', this)">👤 Nhân bản giọng nói</div>
        <div class="nav-item" onclick="switchNav('registry', this)">🎙️ Đa giọng</div>
        <div class="nav-item" onclick="switchNav('profile', this)">⚙️ Profile</div>
    </div>

    <div class="main-wrapper">
        <div class="topbar">
            <div class="user-profile"><div class="avatar">M</div> Minh Hiếu Nguyễn</div>
        </div>

        <!-- 1. VIEW: TẠO GIỌNG NÓI -->
        <div id="view-tts" class="view-panel active tts-layout">
            <div class="center-content">
                <div class="page-title">✨ Tạo giọng nói</div>
                <div class="page-desc">Nhập văn bản, chọn chế độ giọng, đổ bóng sáng tạo.</div>
                
                <div class="card">
                    <label class="form-label">Văn bản</label>
                    <textarea id="text-input" class="text-input" style="height:120px" oninput="document.getElementById('char-count').innerText = this.value.length + ' ký tự'">Xin chào, đây là bản demo của TTS Voice Studio.</textarea>
                    <div id="char-count" style="font-size:0.8rem; color:gray; margin-top:5px;">45 ký tự</div>
                    
                    <label class="form-label" style="margin-top:20px;">Biểu cảm / Hiệu ứng</label>
                    <div class="emotion-grid">
                        <div class="emotion-btn" onclick="insertTag('[sigh]')"><span class="emotion-title">Thở dài</span><span class="emotion-sub">Sighing</span></div>
                        <div class="emotion-btn" onclick="insertTag('[uh]')"><span class="emotion-title">Xác nhận</span><span class="emotion-sub">Uh sound</span></div>
                        <div class="emotion-btn" onclick="insertTag('[laugh]')"><span class="emotion-title">Cười</span><span class="emotion-sub">Laughter</span></div>
                    </div>
                </div>

                <div class="card">
                    <label class="form-label">Chế độ giọng</label>
                    <select id="voice-select" class="select-input"></select>
                </div>
                
                <div class="card">
                    <label class="form-label">Tốc độ (Speed)</label>
                    <input type="range" id="speed-slider" min="0.5" max="2.0" step="0.1" value="1.0" style="width:100%">
                </div>
            </div>

            <div class="right-panel">
                <div class="page-title">Tạo giọng nói</div>
                <button class="btn-blue" id="btn-generate" onclick="generateTTS()" style="padding:16px; font-size:1.1rem; margin-bottom:20px;">✨ Tạo</button>
                <div class="card" style="flex:1; display:flex; flex-direction:column;">
                    <div id="player-container" style="display:none;">
                        <audio id="audio-player" controls style="width:100%"></audio>
                        <a id="download-link" href="#" style="color:var(--accent-blue); display:block; margin-top:10px;">⬇️ Tải xuống</a>
                    </div>
                </div>
            </div>
        </div>

        <!-- 2. VIEW: NHÂN BẢN GIỌNG NÓI -->
        <div id="view-clone" class="view-panel single-layout">
            <div class="page-title">👤 Nhân bản giọng nói</div>
            <div class="page-desc">Tải lên file audio gốc để hệ thống AI học và nhân bản giọng nói.</div>
            
            <div class="card">
                <label class="form-label">1. Tải lên file giọng mẫu (.wav, .mp3)</label>
                <input type="file" id="file-uploader" class="select-input" accept=".wav,.mp3,.ogg,.flac">
                <button class="btn-blue" style="margin-top:10px;" onclick="uploadRefFile()">Tải lên Server</button>
                <div id="upload-status" style="margin-top:10px; color:var(--accent-green);"></div>
            </div>

            <div class="card">
                <label class="form-label">2. Lưu thành Profile VoiceID</label>
                <input type="text" id="save-clone-id" class="text-input" placeholder="Nhập ID không dấu (vd: sep_tong)" style="margin-bottom:10px;">
                <input type="text" id="save-clone-file" class="text-input" placeholder="Tên file đã tải lên (vd: sep_tong.wav)" style="margin-bottom:10px;" readonly>
                <button class="btn-blue" onclick="saveCloneToRegistry()">Lưu VoiceID</button>
            </div>
        </div>

        <!-- 3. VIEW: ĐA GIỌNG (REGISTRY) -->
        <div id="view-registry" class="view-panel single-layout">
            <div class="page-title">🎙️ Đa giọng (Quản lý Voice Registry)</div>
            <div class="page-desc">Danh sách toàn bộ các giọng đã được thiết kế và nhân bản trên hệ thống.</div>
            
            <div class="card">
                <button class="btn-blue" onclick="loadVoiceRegistryTable()" style="margin-bottom:20px;">↻ Tải lại danh sách</button>
                <table class="registry-table" id="registry-table">
                    <thead><tr><th>VoiceID</th><th>Tên hiển thị</th><th>Loại</th><th>Hành động</th></tr></thead>
                    <tbody><!-- Render via JS --></tbody>
                </table>
            </div>
        </div>

        <!-- 4. VIEW: PROFILE (API) -->
        <div id="view-profile" class="view-panel single-layout">
            <div class="page-title">⚙️ Profile & API Integration</div>
            <div class="page-desc">Tích hợp OmniVoice API vào phần mềm của bên thứ 3.</div>
            
            <div class="card">
                <label class="form-label">Server Endpoint</label>
                <input type="text" id="api-endpoint" class="text-input" value="http://127.0.0.1:8088" readonly style="color:var(--accent-green); font-family:monospace;">
            </div>

            <div class="card">
                <label class="form-label">Python (requests) Snippet</label>
                <div class="snippet-box">
import requests
url = "http://127.0.0.1:8088/v1/voices/YOUR_VOICE_ID/tts"
res = requests.post(url, json={"text": "Xin chào"})
with open("output.wav", "wb") as f:
    f.write(res.content)
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    const serverUrl = window.location.origin; // Sẽ map đúng port khi chạy bằng pywebview

    // Navigation Logic
    function switchNav(viewId, el) {
        document.querySelectorAll('.nav-item').forEach(e => e.classList.remove('active'));
        el.classList.add('active');
        document.querySelectorAll('.view-panel').forEach(e => e.classList.remove('active'));
        document.getElementById('view-' + viewId).classList.add('active');

        if(viewId === 'registry') loadVoiceRegistryTable();
    }

    // TTS View Logic
    function insertTag(tag) {
        const ta = document.getElementById('text-input');
        const start = ta.selectionStart;
        const text = ta.value;
        ta.value = text.substring(0, start) + tag + text.substring(ta.selectionEnd);
        ta.focus();
    }

    async function loadCatalog() {
        try {
            const res = await fetch('/v1/catalog');
            const data = await res.json();
            const select = document.getElementById('voice-select');
            select.innerHTML = data.voices.map(v => `<option value="${v.id}">${v.display_name || v.id} (${v.type})</option>`).join('');
        } catch(e) { console.error(e); }
    }

    async function generateTTS() {
        const text = document.getElementById('text-input').value;
        const voiceId = document.getElementById('voice-select').value;
        const speed = parseFloat(document.getElementById('speed-slider').value);
        document.getElementById('btn-generate').innerText = "⏳ Đang tạo...";
        
        try {
            const res = await fetch('/v1/tts', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ text, voice_id: voiceId, speed })
            });
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            document.getElementById('player-container').style.display = 'block';
            document.getElementById('audio-player').src = url;
            document.getElementById('audio-player').play();
            document.getElementById('download-link').href = url;
        } catch(e) { alert("Lỗi: " + e.message); }
        document.getElementById('btn-generate').innerText = "✨ Tạo";
    }

    // Clone View Logic
    async function uploadRefFile() {
        const fileInput = document.getElementById('file-uploader');
        if(!fileInput.files[0]) return alert("Chưa chọn file!");
        const formData = new FormData();
        formData.append("file", fileInput.files[0]);
        
        try {
            const res = await fetch('/api/upload-ref', { method: 'POST', body: formData });
            const data = await res.json();
            document.getElementById('upload-status').innerText = "Đã tải lên: " + data.filename;
            document.getElementById('save-clone-file').value = data.filename;
        } catch(e) { alert("Lỗi upload: " + e.message); }
    }

    async function saveCloneToRegistry() {
        const id = document.getElementById('save-clone-id').value;
        const file = document.getElementById('save-clone-file').value;
        if(!id || !file) return alert("Vui lòng điền ID và upload file trước!");
        try {
            await fetch('/v1/voices', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ id: id, type: 'clone', ref_audio_file: file, display_name: id })
            });
            alert("Đã lưu VoiceID thành công!");
            loadCatalog(); // Refresh TTS dropdown
        } catch(e) { alert("Lỗi lưu: " + e.message); }
    }

    // Registry View Logic
    async function loadVoiceRegistryTable() {
        try {
            const res = await fetch('/v1/catalog');
            const data = await res.json();
            const tbody = document.querySelector('#registry-table tbody');
            tbody.innerHTML = data.voices.map(v => `
                <tr>
                    <td><code>${v.id}</code></td>
                    <td>${v.display_name || ''}</td>
                    <td>${v.type}</td>
                    <td><button onclick="deleteVoice('${v.id}')" style="background:#ef4444; color:#fff; border:none; padding:5px 10px; border-radius:5px; cursor:pointer;">Xóa</button></td>
                </tr>
            `).join('');
        } catch(e) { console.error(e); }
    }

    async function deleteVoice(id) {
        if(!confirm(`Xác nhận xóa voice ${id}?`)) return;
        await fetch(`/v1/voices/${id}`, { method: 'DELETE' });
        loadVoiceRegistryTable();
        loadCatalog();
    }

    window.onload = loadCatalog;
</script>
</body>
</html>
```
