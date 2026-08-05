
    // Navigation Logic
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const viewId = item.dataset.view;
            document.querySelectorAll('.nav-item').forEach(e => e.classList.remove('active'));
            item.classList.add('active');
            document.querySelectorAll('.view-panel').forEach(e => e.classList.remove('active'));
            document.getElementById('view-' + viewId).classList.add('active');
            if (viewId === 'registry') loadVoiceRegistryTable();
        });
    });

    // TTS View Logic
    function insertTag(tag) {
        const ta = document.getElementById('text-input');
        const start = ta.selectionStart;
        const text = ta.value;
        ta.value = text.substring(0, start) + tag + text.substring(ta.selectionEnd);
        ta.focus();
        ta.selectionEnd = start + tag.length;
        document.getElementById('char-count').innerText = ta.value.length + ' ký tự';
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
        const btn = document.getElementById('btn-generate');
        const text = document.getElementById('text-input').value;
        const voiceId = document.getElementById('voice-select').value;
        const speed = parseFloat(document.getElementById('speed-slider').value);

        if (!text.trim()) return alert("Vui lòng nhập văn bản!");
        if (!voiceId) return alert("Chưa có voice nào trong catalog!");

        btn.disabled = true;
        btn.innerText = "⏳ Đang tạo...";

        try {
            const res = await fetch('/v1/tts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, voice_id: voiceId, speed })
            });

            if (!res.ok) throw new Error(await res.text());

            const blob = await res.blob();
            const url = URL.createObjectURL(blob);

            const snippet = text.length > 80 ? text.substring(0, 80) + '...' : text;
            const now = new Date();
            const time = now.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            const filename = `tts_${Date.now()}.wav`;

            const item = document.createElement('div');
            item.className = 'history-item';
            item.innerHTML = `
                <div class="history-meta">
                    <span class="history-time">${time}</span>
                    <span>${(blob.size / 1024).toFixed(1)} KB</span>
                </div>
                <div class="history-text">${escapeHtml(snippet)}</div>
                <div class="history-controls">
                    <audio src="${url}" controls></audio>
                    <a class="history-download" href="${url}" download="${filename}">⬇️ Tải</a>
                </div>
            `;

            const list = document.getElementById('history-list');
            list.insertBefore(item, list.firstChild);

            document.getElementById('empty-state').style.display = 'none';
            document.getElementById('history-section').style.display = 'block';

            const audioInItem = item.querySelector('audio');
            audioInItem.play();
        } catch (e) {
            alert("Lỗi khi tạo TTS: " + e.message);
        } finally {
            btn.disabled = false;
            btn.innerText = "✨ Tạo";
        }
    }

    function escapeHtml(str) {
        return str.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    }

    // Clone View Logic
    async function uploadRefFile() {
        const fileInput = document.getElementById('file-uploader');
        if (!fileInput.files[0]) return alert("Chưa chọn file!");
        const formData = new FormData();
        formData.append("file", fileInput.files[0]);

        try {
            const res = await fetch('/api/upload-ref', { method: 'POST', body: formData });
            const data = await res.json();
            document.getElementById('upload-status').innerText = "Đã tải lên: " + data.filename;
            document.getElementById('save-clone-file').value = data.filename;
        } catch (e) {
            alert("Lỗi upload: " + e.message);
        }
    }

    async function saveCloneToRegistry() {
        const id = document.getElementById('save-clone-id').value;
        const file = document.getElementById('save-clone-file').value;
        if (!id || !file) return alert("Vui lòng điền ID và upload file trước!");
        try {
            await fetch('/v1/voices', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: id, type: 'clone', ref_audio_file: file, display_name: id })
            });
            alert("Đã lưu VoiceID thành công!");
            loadCatalog();
        } catch (e) {
            alert("Lỗi lưu: " + e.message);
        }
    }

    // Registry View Logic
    async function loadVoiceRegistryTable() {
        try {
            const res = await fetch('/v1/catalog');
            const data = await res.json();
            const tbody = document.querySelector('#registry-table tbody');
            tbody.innerHTML = data.voices.map(v => `
                <tr>
                    <td><code>${escapeHtml(v.id)}</code></td>
                    <td>${escapeHtml(v.display_name || '')}</td>
                    <td>${escapeHtml(v.type || '')}</td>
                    <td><button onclick="deleteVoice('${escapeHtml(v.id)}')" style="background:var(--danger); color:#fff; border:none; padding:6px 12px; border-radius:6px; cursor:pointer; font-size:0.8rem;">Xóa</button></td>
                </tr>
            `).join('');
        } catch (e) { console.error(e); }
    }

    async function deleteVoice(id) {
        if (!confirm(`Xác nhận xóa voice ${id}?`)) return;
        try {
            await fetch(`/v1/voices/${id}`, { method: 'DELETE' });
            loadVoiceRegistryTable();
            loadCatalog();
        } catch (e) {
            alert("Lỗi xóa: " + e.message);
        }
    }

    window.onload = () => {
        loadCatalog();
    };

