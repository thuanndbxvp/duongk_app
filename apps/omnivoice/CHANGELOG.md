# Changelog

All notable changes to **omnivoice-api-server** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-07-09

### Changed
- **Bump `omnivoice` to upstream `0.2.0`** (pinned via `requirements.txt`).
  - Replaces unpinned `git+https://...@main` (was vulnerable to upstream force-push).
  - Note: tag is `0.2.0` (no `v` prefix), unlike `0.1.x` series.
- **TTSRequest field routing**: pass inference params through
  `OmniVoiceGenerationConfig` (new in `0.2.0`) instead of `**kwargs`.
  This is the **only** correct way to pass `num_step`, `guidance_scale`,
  `denoise`, `postprocess_output`, `pad_duration`, `fade_duration`.
- `audio_chunk_duration` / `audio_chunk_threshold` no longer hardcoded —
  uses upstream defaults (`15.0` / `30.0`).
- VN-friendly defaults: `pad_duration=0.15s`, `fade_duration=0.05s`
  (reduces pop/clip at start/end for long narration).
- Logging format: UTC timestamps with `Z` suffix for log-aggregator
  compatibility (was local time before).
- Re-raise exceptions with `raise ... from e` (`B904` lint rule) to preserve
  exception chain in stack traces.
- Top-level `OmniVoice` / `OmniVoiceGenerationConfig` import (with safe
  fallback to `None` if package missing) so version-mismatch errors surface
  at startup rather than first request.

### Added
- `GET /v1/version` endpoint — reports server + omnivoice versions and
  pinned tag, useful for client validation (Phase 6 uses this).
- `request_id` (12-char hex UUID) generated per `/v1/tts` request and
  embedded in all related log lines (`[req=xxxxxxxxxxxx]`) for tracing.
- Validation: `pad_duration < 0` or `fade_duration < 0` returns `422`
  (was `500` from upstream exception).
- `pyproject.toml` — unified dependency + tool config (matches upstream
  OmniVoice style).
- `ruff.toml` (inline in `pyproject.toml`) — enables `E`, `W`, `F`, `I`,
  `B`, `C4`, `UP` rule sets. `line-length=100`, double quotes, LF.
- `.github/workflows/ci.yml` — three parallel jobs:
  - **lint**: `ruff check app/` + `ruff format --check app/`
  - **compile**: `python -m py_compile app/main.py`
  - **test**: `pytest tests/` on Python 3.10/3.11/3.12 (mocked model)
- This `CHANGELOG.md` file.

### Backward Compatibility
- **100%** backward-compatible: clients that don't send `pad_duration` /
  `fade_duration` still get the new VN-friendly defaults automatically.
- Clients that send `speed` / `duration` still work (passed via
  `generate(**extra_kwargs)` since these are not part of
  `OmniVoiceGenerationConfig`).
- `1.0.0` clients continue to function — no breaking changes.

### Bug Fixes
- HTTPException raised inside `try: ... except Exception` block was being
  swallowed and converted to `500`. Validation now lives **before** the
  `try` block.

### Added (Phase 6)
- **`app/voice_registry.py`** — JSON-backed VoiceID Registry with
  `threading.Lock` + atomic write (R10 mitigation).
- **`voice_registry.json`** — 11 voiceID mẫu phủ 8 ngôn ngữ (vi/km/my/en/zh/es/hi/ar).
- **`server_id.txt`** — UUID stable định danh server (D11/R9 mitigation).
- **`test_external_app.py`** — CLI mẫu cho dev bên thứ 3 tích hợp nhanh.
- **6 endpoint mới**:
  - `GET /v1/identify` — IP/port/version/voice_count (cho App validate IP:port)
  - `GET /v1/catalog` — danh sách voiceID (catalog, KHÔNG bao gồm instruct)
  - `GET /v1/voices/{voice_id}` — chi tiết 1 voice (có instruct)
  - `POST /v1/voices/{voice_id}/tts` — **endpoint đơn giản**, body chỉ cần `{text, language?}`
  - `POST /v1/voices` — admin tạo/cập nhật voiceID
  - `DELETE /v1/voices/{voice_id}` — admin xoá voiceID
- 3 loại voice được hỗ trợ: `design` (instruct) / `clone` (ref_audio) / `auto`.
- Validation: `type='design'` thiếu `instruct` → 422, `type='clone'` ref_audio không tồn tại → 422 (R11).
- README có section "Tích hợp nhanh" 5 bước cho dev bên thứ 3.
- CHANGELOG cập nhật.

### Risk Mitigations (Phase 6)
- **R9** (App nhập nhầm IP): `GET /v1/identify` trả về `server_id` để validate.
- **R10** (file bị race): `threading.Lock` + atomic rename write.
- **R11** (ref_audio bị xoá): check file tồn tại trước khi gọi model, trả 422 với code `ref_audio_not_found`.

## [1.0.0] - 2026-04-02 (baseline)

### Features (pre-1.1.0)
- FastAPI server with `POST /v1/tts`, `GET /health`, `POST /api/upload-ref`,
  `GET /api/voices`.
- Web playground at `GET /` with Vietnamese UI for 4 languages
  (vi/en/zh/auto).
- Voice cloning via `voices/*.wav` lookup.
- Voice design via text instructions (e.g. `"female, young adult, ..."`).
- Reference audio upload endpoint.
- `test_client.py` smoke test.
- `setup_and_run.bat` for Windows one-click install.
- `run.bat` for Windows one-click start (simple, fixed 127.0.0.1:8088).
- `.env`-driven device/dtype/host/port configuration.

## [1.1.1] - 2026-07-10

### Added
- **`start.bat`** — Windows launcher có menu (chọn host: `127.0.0.1` / `0.0.0.0` / custom + port). Auto-check Python, venv, omnivoice version, CUDA, voices/, voice_registry.json. Hiển thị LAN IP khi chọn mode 2 (LAN). Kill process trên port trước khi launch.

## [1.1.2] - 2026-07-10

### Fixed (UI)
- **Dropdown bg color**: Custom CSS cho `<select>` (custom SVG arrow + option styling `#1e1e2e` bg, hover/selected gradient `var(--accent)`). Loại bỏ browser default highlight.
- **Lang-select promoted**: Di chuyển `<select id="lang-select">` lên **Global Setting block** ngay dưới textarea (luôn visible, không bị ẩn trong Advanced panel).
- **Save voice to registry**: Thêm khối "Lưu giọng vào Registry" trong Voice Design panel với input `voiceID` + `display_name`. Button → `POST /v1/voices` với `type=design`. Validation regex `[a-z0-9_]+` cho voiceID.

## [1.1.3] - 2026-07-10

### Added (UI)
- **Voice Registry Manager** trong Voice Design panel — bảng hiển thị 11 voice mẫu (auto-load từ `GET /v1/catalog`):
  - Cột: `voiceID` (code style), Tên (display_name), Type (🎨design / 🎤clone / 🎲auto), Ngôn ngữ, nút 🗑 xoá
  - Button "↻ Tải lại danh sách" → gọi lại `/v1/catalog`
  - XSS-safe: `escapeHtml` + `escapeAttr` helpers cho tất cả giá trị user-controlled
  - Confirm dialog trước khi xoá
  - Auto-refresh sau khi save voice mới (UI đồng bộ không cần F5)
- 3 JS function mới: `loadVoiceRegistry()`, `deleteVoiceFromRegistry(voiceId)`, `escapeHtml/escapeAttr()`
- CSS classes: `.registry-block`, `.registry-table`, `.btn-icon-danger`

## [1.1.4] - 2026-07-10

### Added (UI Phase 6.6 đóng PARTIAL)
- **Tab #3: "API cho App khác (Quick Integration)"** trong UI (cùng cấp với Voice Design + Voice Cloning).
- **Section A — Server Endpoint**: Auto-detect IP:port từ `GET /v1/identify` (fallback `window.location.origin` nếu fail), hiển thị dạng readonly input monospace + nút 📋 Copy.
- **Section B — VoiceID list**: Grid responsive (auto-fill, minmax 220px) hiển thị tất cả voiceID từ `/v1/catalog` (lazy-load khi mở tab), mỗi voice có nút `copy` riêng để copy voiceID.
- **Section C — 4 code snippet**:
  - 🐚 cURL (curl POST + verify với `/v1/identify`)
  - 🐍 Python (requests)
  - 📜 JavaScript (fetch + blob URL)
  - 🍎 Swift (URLSession cho iOS)
  - Mỗi snippet có nút 📋 Copy riêng (clipboard API + fallback `execCommand`).
  - Placeholder tự động fill = `apiServerUrl` + first `voiceID`.
- **Section D — Workflow 4 bước** cho dev bên thứ 3 (ordered list tiếng Việt).
- 7 JS function mới: `loadApiTab()`, `renderSnippets()`, `copyText()`, `copyToClipboard()`, `copySnippet()`, helpers.
- 9 CSS class mới: `.api-section`, `.api-endpoint-row`, `.api-voice-grid`, `.api-voice-card`, `.copy-mini`, `.snippet-card`, `.snippet-header`, `.snippet-lang`, `.btn-icon-secondary`.

### Verification
- 10/10 test PASS trong `tests/test_phase4r4_api_tab.py`.
- Toàn bộ regression: **68/68 PASS** (Phase 3: 6 + Phase 4R: 8 + Phase 4R.2: 6 + Phase 4R.3: 7 + Phase 4R.4: 10 + Phase 5: 24 + Phase 6: 7).
- ruff check: clean.

### Known Limitations
- `omnivoice` unpinned → could break on upstream force-push. *Fixed in 1.1.0.*
- No version endpoint. *Fixed in 1.1.0.*
- No CI / no lint. *Fixed in 1.1.0.*
- No `pad_duration` / `fade_duration` support. *Fixed in 1.1.0.*